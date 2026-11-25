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
import os
import platform
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
        _dll, _path = dll, target
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

    # Linux: the dynamic loader ignores sys.prefix, so preload each runtime
    # library it reports missing from <prefix>/lib (globally, so later loads
    # resolve against it) and retry.
    return _load_preloading(target, ctypes.DEFAULT_MODE, runtime_dir, set())


def _load_preloading(path, mode, runtime_dir, attempted):
    while True:
        try:
            return ctypes.CDLL(str(path), mode=mode)
        except OSError as err:
            m = re.match(r"(\S+?): cannot open shared object file", str(err))
            name = m.group(1) if m else None
            candidate = runtime_dir / name if name else None
            if candidate is None or name in attempted or not candidate.is_file():
                raise
            attempted.add(name)
            _load_preloading(candidate, ctypes.RTLD_GLOBAL, runtime_dir, attempted)


def get_dll():
    """Return the loaded IWFM library, loading it on first use."""
    return _dll if _dll is not None else load_dll()


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
