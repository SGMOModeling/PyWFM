"""Wheel tagging and dependencies for pywfm.

pywfm itself is pure Python, but platform wheels bundle the IWFM shared
library in ``src/pywfm/_lib``. When that directory holds a library the wheel
is tagged ``py3-none-<platform>`` (one wheel per platform, any Python 3);
otherwise a normal pure ``py3-none-any`` wheel is built.

The bundled library is linked dynamically against the Intel Fortran and
OpenMP runtimes, which are not copied into the wheel: the wheel depends on
Intel's own PyPI packages instead (intel-fortran-rt, intel-openmp). The step
that puts the library in ``_lib`` also writes ``_lib/runtime-requirements.txt``
listing them, one requirement per line, matching the compiler it was built
with.
"""
from pathlib import Path

from setuptools import setup

try:
    from setuptools.command.bdist_wheel import bdist_wheel
except ImportError:  # setuptools < 70
    from wheel.bdist_wheel import bdist_wheel

LIB_DIR = Path(__file__).parent / "src" / "pywfm" / "_lib"
RUNTIME_REQUIREMENTS = LIB_DIR / "runtime-requirements.txt"

DEPENDENCIES = [
    "numpy",
    "matplotlib",
    "pandas",
    "Click",
    "requests",
]


def _has_bundled_library():
    return any(LIB_DIR.glob("*.dll")) or any(LIB_DIR.glob("*.so"))


def _runtime_requirements():
    if not _has_bundled_library():
        return []
    if not RUNTIME_REQUIREMENTS.is_file():
        raise SystemExit(
            f"{LIB_DIR} holds an IWFM library but no runtime-requirements.txt "
            "listing the runtime packages it needs (e.g. intel-fortran-rt)."
        )
    lines = RUNTIME_REQUIREMENTS.read_text().splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


class PlatformWheel(bdist_wheel):
    def finalize_options(self):
        super().finalize_options()
        if _has_bundled_library():
            self.root_is_pure = False

    def get_tag(self):
        python, abi, plat = super().get_tag()
        if _has_bundled_library():
            return "py3", "none", plat
        return python, abi, plat


setup(
    install_requires=DEPENDENCIES + _runtime_requirements(),
    cmdclass={"bdist_wheel": PlatformWheel},
)
