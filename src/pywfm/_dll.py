"""Locate, load, and classify the IWFM shared library.

The library is found on first use (not at import), in this order:

1. ``load_dll(path)`` called by the user before the first model/budget
   object is created
2. the ``PYWFM_DLL`` environment variable (a file, or a directory that
   contains the library)
3. the library bundled inside the pywfm wheel (``pywfm/_lib``)
4. the active environment's library directory (conda: ``<prefix>/Library/bin``
   on Windows, ``<prefix>/lib`` on Linux), where the ``libiwfm`` conda package
   and ``pywfm setup-pywfm`` install it

Two generations of the IWFM C API are supported (see ``abi()``):

- ``"handle"``: every ``IW_Model_*`` procedure except a few constructors takes
  the model ID as its first argument (kernel commit 393e02e+, e.g. the
  2026.0.1848.rev fork build). Models are independent.
- ``"switch"``: the stock DWR DLLs (2024.2.1594 and later). The DLL holds one
  active model; ``IW_Model_Switch`` selects it. pywfm switches before every
  call and serializes calls, so several ``IWFMModel`` objects still work.
"""
import ctypes
import struct
import os
import platform
import queue
import re
import sys
import threading
from pathlib import Path

from pywfm.exceptions import IWFMError

if platform.system() == "Windows":
    LIBRARY_NAMES = ("IWFM_C_x64.dll",)
else:
    LIBRARY_NAMES = ("libiwfm_c.so", "libIWFMLib.so")

# IW_Model_* procedures whose argument list is the same in both generations
# (no model ID). Every other IW_Model_* procedure takes the model ID first in
# the "handle" generation. Verified against the 2026.0.1848 and
# 2026.0.1848.rev sources: 165 procedures differ only by the leading model ID.
NO_MODEL_ID = frozenset(
    {
        "IW_Model_New",
        "IW_Model_WSA_New",
        "IW_Model_DeleteInquiryDataFile",
        "IW_Model_IsModelInstantiated",
    }
)

# Serializes calls on "switch" DLLs, whose active-model selection is global.
# Re-entrant because some wrappers call other wrappers.
ACTIVE_MODEL_LOCK = threading.RLock()

_lock = threading.Lock()
_dll = None
_path = None
_abi = None
_core_version = None
# Log file opened through IW_SetLogFile. The library keeps one per process.
log_file = None


def _candidates():
    """Yield (path, source) pairs in search order."""
    env = os.environ.get("PYWFM_DLL")
    if env:
        p = Path(env)
        if p.is_dir():
            for name in LIBRARY_NAMES:
                yield p / name, "PYWFM_DLL"
        else:
            yield p, "PYWFM_DLL"
    bundled = Path(__file__).resolve().parent / "_lib"
    for name in LIBRARY_NAMES:
        yield bundled / name, "bundled with pywfm"
    prefix = Path(sys.prefix)
    env_dir = prefix / "Library" / "bin" if platform.system() == "Windows" else prefix / "lib"
    for name in LIBRARY_NAMES:
        yield env_dir / name, "environment"


def find_library():
    """Return the path of the IWFM library that ``get_dll()`` would load.

    Raises
    ------
    FileNotFoundError
        if no candidate exists; the message lists every place searched.
    """
    searched = []
    for path, source in _candidates():
        if path.is_file():
            return path
        searched.append(f"  {path} ({source})")
    raise FileNotFoundError(
        "No IWFM library was found. Searched:\n"
        + "\n".join(searched)
        + "\nInstall it (conda: libiwfm; pip wheels bundle it), set PYWFM_DLL "
        "to its path, or call pywfm.load_dll(path) before creating a model."
    )


def load_dll(path=None):
    """Load the IWFM library and return the ``ctypes.CDLL`` handle.

    Parameters
    ----------
    path : str or os.PathLike, optional
        library file to load; if omitted, the search order in this module's
        docstring is used.

    Note
    ----
    A process can only use one IWFM library: Fortran module state lives in
    the library, and the library cannot be unloaded safely. Calling this
    again with a different path after a library is loaded raises IWFMError.
    """
    global _dll, _path, _abi, _core_version
    with _lock:
        target = Path(path).resolve() if path is not None else None
        if _dll is not None:
            if target is None or target == _path:
                return _dll
            raise IWFMError(
                f"An IWFM library is already loaded from {_path}; a process "
                f"can only use one (requested {target})."
            )
        if target is None:
            target = find_library().resolve()
        elif not target.is_file():
            raise FileNotFoundError(f"IWFM library not found: {target}")
        dll = _open(target)
        _abi = _classify(dll, target)
        _core_version = _version(dll)
        _dll, _path = LargeStackLibrary(dll), target
        return _dll


def _runtime_dir():
    """Where the environment's runtime libraries live.

    conda (intel-fortran-rt, llvm-openmp) and Intel's PyPI packages
    (intel-fortran-rt, intel-openmp) both install into this directory.
    """
    prefix = Path(sys.prefix)
    return prefix / "Library" / "bin" if platform.system() == "Windows" else prefix / "lib"


def _open(target):
    """Load the library, finding the Intel Fortran and OpenMP runtimes it links.

    The runtimes are separate packages, never copied next to the library, so
    a library bundled in the wheel (pywfm/_lib) must find them in the
    environment.
    """
    runtime_dir = _runtime_dir()
    if platform.system() == "Windows":
        dirs = [target.parent]
        if runtime_dir.is_dir() and runtime_dir != target.parent:
            dirs.append(runtime_dir)
        for d in dirs:
            os.add_dll_directory(str(d))
        # libifcoremd.dll loads libmmd.dll in a way that ignores directories
        # added with add_dll_directory (it is found only through PATH, which
        # an activated conda environment sets but a pip install does not), so
        # load it first by full path.
        for d in dirs:
            if (d / "libmmd.dll").is_file():
                ctypes.CDLL(str(d / "libmmd.dll"))
                break
        return ctypes.CDLL(str(target))

    # Linux: the dynamic loader ignores sys.prefix, and a pip install puts
    # the Intel runtimes in <prefix>/lib with no RPATH pointing there. Preload
    # the ones the library needs from there, dependencies first and globally,
    # so that loading the library resolves against them.
    if runtime_dir.is_dir():
        _preload(_runtime_needed(target, runtime_dir, [], set()))
    return ctypes.CDLL(str(target))


def _runtime_needed(path, runtime_dir, found, seen):
    """Libraries in runtime_dir that ``path`` needs, directly or indirectly,
    each listed after its own dependencies."""
    for name in _elf_needed(path):
        candidate = runtime_dir / name
        if name in seen or not candidate.is_file():
            continue
        seen.add(name)
        _runtime_needed(candidate, runtime_dir, found, seen)
        found.append(candidate)
    return found


def _preload(libraries):
    """Load the libraries globally, retrying any that fail after the others.

    Some Intel runtime libraries use symbols of another without listing it
    as a dependency (libifport.so.5 needs for_abort from libifcoremt.so.5),
    so dependency order alone can't order them, and ctypes binds symbols
    at load time.
    """
    pending = list(libraries)
    while pending:
        failed, error = [], None
        for lib in pending:
            try:
                ctypes.CDLL(str(lib), mode=ctypes.RTLD_GLOBAL)
            except OSError as err:
                failed.append(lib)
                error = err
        if len(failed) == len(pending):
            raise error
        pending = failed


def _elf_needed(path):
    """DT_NEEDED entries of a 64-bit little-endian ELF shared library.

    Returns [] for anything else; the loader then reports what is missing.
    """
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return []
    if data[:4] != b"\x7fELF" or data[4] != 2 or data[5] != 1:
        return []
    phoff, = struct.unpack_from("<Q", data, 0x20)
    phentsize, phnum = struct.unpack_from("<HH", data, 0x36)
    loads, dynamic = [], None
    for i in range(phnum):
        p_type, _, p_offset, p_vaddr, _, p_filesz = struct.unpack_from(
            "<IIQQQQ", data, phoff + i * phentsize)
        if p_type == 1:                       # PT_LOAD
            loads.append((p_vaddr, p_offset, p_filesz))
        elif p_type == 2:                     # PT_DYNAMIC
            dynamic = (p_offset, p_filesz)
    if dynamic is None:
        return []

    def file_offset(vaddr):
        for v, o, n in loads:
            if v <= vaddr < v + n:
                return o + vaddr - v
        return None

    needed, strtab = [], None
    off, size = dynamic
    for k in range(0, size, 16):
        tag, val = struct.unpack_from("<qQ", data, off + k)
        if tag == 0:                          # DT_NULL
            break
        if tag == 1:                          # DT_NEEDED
            needed.append(val)
        elif tag == 5:                        # DT_STRTAB
            strtab = file_offset(val)
    if strtab is None:
        return []
    names = []
    for n in needed:
        start = strtab + n
        names.append(data[start:data.index(b"\0", start)].decode())
    return names


def get_dll():
    """Return the loaded IWFM library, loading it on first use.

    Procedures of the returned object run on a large-stack thread (see
    ``LargeStackLibrary``).
    """
    return _dll if _dll is not None else load_dll()


# The library uses the calling thread's stack. The IWFM executables reserve
# 256,000,000 bytes; Python's main thread has 1-2 MB on Windows (8 MB on
# Linux), which even the sample model overflows ("OSError: exception: stack
# overflow") unless the library was compiled with heap-arrays, which makes it
# several times slower. 255 MB is the largest stack CPython allows a thread on
# Windows.
STACK_SIZE_MB = 255

_thread_state = threading.local()


def on_large_stack():
    """True on a thread pywfm created with a large stack."""
    return getattr(_thread_state, "large_stack", False)


def start_large_stack_thread(target, name):
    """Start a daemon thread running ``target`` with a STACK_SIZE_MB stack."""
    def run():
        _thread_state.large_stack = True
        target()
    with _lock:
        previous = threading.stack_size(STACK_SIZE_MB * 1024 * 1024)
        try:
            thread = threading.Thread(target=run, name=name, daemon=True)
            thread.start()
        finally:
            threading.stack_size(previous)
    return thread


class _Worker:
    """A large-stack thread that runs library calls for one calling thread."""

    def __init__(self):
        requests = self.requests = queue.SimpleQueue()
        # The thread holds only the queue, so this object is freed (and the
        # thread told to stop) when the calling thread ends.
        start_large_stack_thread(lambda: _Worker._serve(requests),
                                 f"pywfm-library-{threading.get_ident()}")

    @staticmethod
    def _serve(requests):
        while True:
            request = requests.get()
            if request is None:
                return
            fn, args, done, outcome = request
            try:
                outcome.append((True, fn(*args)))
            except BaseException as exc:
                outcome.append((False, exc))
            del request, fn, args
            done.set()

    def call(self, fn, args):
        done, outcome = threading.Event(), []
        self.requests.put((fn, args, done, outcome))
        while not done.wait(0.5):   # a timeout keeps Ctrl-C responsive
            pass
        ok, value = outcome[0]
        if ok:
            return value
        raise value

    def __del__(self):
        # The calling thread has ended (its thread-local storage was freed).
        self.requests.put(None)


def _worker():
    worker = getattr(_thread_state, "worker", None)
    if worker is None:
        worker = _thread_state.worker = _Worker()
    return worker


class _Procedure:
    __slots__ = ("fn", "__name__")

    def __init__(self, fn, name):
        self.fn = fn
        self.__name__ = name

    def __call__(self, *args):
        if on_large_stack():
            return self.fn(*args)
        return _worker().call(self.fn, args)


class LargeStackLibrary:
    """The loaded library, with every procedure run on a large stack.

    Calls from a thread that pywfm started with a large stack run directly.
    Calls from any other thread run on a large-stack worker thread dedicated
    to that thread, so the calls of one thread keep their order and threads
    using different models still run at the same time. If Ctrl-C interrupts
    a call, the library call itself still runs to its end.
    """

    def __init__(self, cdll):
        self._cdll = cdll
        self._procedures = {}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._procedures[name]
        except KeyError:
            proc = self._procedures[name] = _Procedure(getattr(self._cdll, name), name)
            return proc

    def __repr__(self):
        return f"<LargeStackLibrary {self._cdll!r}>"


def dll_path():
    """Return the path of the loaded IWFM library (loading it if needed)."""
    get_dll()
    return _path


def abi():
    """Return the loaded library's API generation: ``"handle"`` or ``"switch"``."""
    get_dll()
    return _abi


def core_version():
    """IWFM core version of the loaded library as a tuple, e.g. (2026, 0, 1848).

    Wrappers use this when a procedure's argument list changed between
    releases (e.g. IW_Model_FEInterpolate gained NVertex and iStat in
    2026.0.1848).
    """
    get_dll()
    parts = []
    for p in (_core_version.split(".") + ["", "", ""])[:3]:
        m = re.match(r"\d+", p)   # "1848-563bc0ef" -> 1848
        parts.append(int(m.group()) if m else 0)
    return tuple(parts)


def _version(dll):
    """IWFM core version string from IW_GetVersion (same in every generation)."""
    n = ctypes.c_int(500)
    buf = ctypes.create_string_buffer(n.value)
    status = ctypes.c_int(0)
    dll.IW_GetVersion(ctypes.byref(n), buf, ctypes.byref(status))
    fields = {}
    for line in buf.value.decode("utf-8", "replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields.get("IWFM Core") or fields.get("IWFM", "")


def _classify(dll, path):
    if hasattr(dll, "IW_Model_Switch"):
        return "switch"
    major = _version(dll).split(".")[0]
    if major.isdigit() and int(major) <= 2015:
        raise IWFMError(
            f"{path} is a 2015-series IWFM DLL ({_version(dll)}). pywfm 1.0 "
            "supports 2024.2.1594 and later; use iwfm-pywfm<0.3 for 2015 DLLs."
        )
    return "handle"
