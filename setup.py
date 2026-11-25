"""Wheel tagging for pywfm.

pywfm itself is pure Python, but platform wheels bundle the IWFM shared
library in ``src/pywfm/_lib``. When that directory holds a library the wheel
is tagged ``py3-none-<platform>`` (one wheel per platform, any Python 3);
otherwise a normal pure ``py3-none-any`` wheel is built.
"""
from pathlib import Path

from setuptools import setup

try:
    from setuptools.command.bdist_wheel import bdist_wheel
except ImportError:  # setuptools < 70
    from wheel.bdist_wheel import bdist_wheel

LIB_DIR = Path(__file__).parent / "src" / "pywfm" / "_lib"


def _has_bundled_library():
    return any(LIB_DIR.glob("*.dll")) or any(LIB_DIR.glob("*.so"))


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


setup(cmdclass={"bdist_wheel": PlatformWheel})
