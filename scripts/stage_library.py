"""Put an IWFM library into src/pywfm/_lib for a platform wheel.

usage: python scripts/stage_library.py LIBRARY LICENSE --runtime-version X.Y.Z
       python scripts/stage_library.py --clean

LIBRARY is the IWFM C shared library (IWFM_C_x64.dll or libiwfm_c.so) built
against the shared Intel runtimes, and LICENSE is IWFM's license file. The
library is linked against the Intel Fortran and OpenMP runtimes of the ifx
that built it; the wheel depends on Intel's PyPI packages of that exact
version instead of bundling them, so pass the compiler version as
--runtime-version (e.g. 2026.1.1). setup.py reads the requirements back from
_lib/runtime-requirements.txt.
"""
import argparse
import shutil
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent.parent / "src" / "pywfm" / "_lib"
RUNTIME_PACKAGES = ["intel-fortran-rt", "intel-cmplr-lib-rt", "intel-openmp"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("library", nargs="?", type=Path)
    ap.add_argument("license", nargs="?", type=Path)
    ap.add_argument("--runtime-version")
    ap.add_argument("--clean", action="store_true", help="empty _lib and exit")
    args = ap.parse_args()

    shutil.rmtree(LIB_DIR, ignore_errors=True)
    if args.clean:
        print(f"removed {LIB_DIR}")
        return
    if not (args.library and args.license and args.runtime_version):
        ap.error("LIBRARY, LICENSE and --runtime-version are required")
    if args.library.name not in ("IWFM_C_x64.dll", "libiwfm_c.so"):
        ap.error(f"unexpected library name {args.library.name}")

    LIB_DIR.mkdir(parents=True)
    shutil.copy2(args.library, LIB_DIR / args.library.name)
    shutil.copy2(args.license, LIB_DIR / "LICENSE-IWFM")
    (LIB_DIR / "runtime-requirements.txt").write_text(
        "# Intel runtimes of the compiler that built the bundled IWFM library\n"
        + "".join(f"{p}=={args.runtime_version}\n" for p in RUNTIME_PACKAGES)
    )
    for p in sorted(LIB_DIR.iterdir()):
        print(p)


if __name__ == "__main__":
    main()
