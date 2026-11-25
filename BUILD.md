# Building pywfm packages

pywfm 1.0 ships three ways:

| Package | What it contains | Where the IWFM library comes from |
|---|---|---|
| PyPI wheel, `py3-none-win_amd64` / `manylinux` | pywfm plus the IWFM library in `pywfm/_lib` | bundled; the Intel runtimes it needs come from Intel's PyPI packages |
| PyPI source distribution / pure wheel | pywfm only | `PYWFM_DLL`, `pywfm.load_dll()`, or `pywfm setup-pywfm` |
| conda-forge `iwfm-pywfm` (noarch) | pywfm only | the conda-forge `libiwfm` package, a dependency |

## The IWFM library for a wheel

A wheel bundles the IWFM C library built from the handle-based fork with the
**shared** Intel runtimes, and depends on Intel's PyPI packages of the same
compiler version instead of bundling the runtimes. Requirements for the
library:

- **Compiler.** Build it with the ifx version the fork's release was verified
  with: 2026.1.1 for 2026.0.1848. Other versions don't reproduce the official
  results bit for bit.
- **Runtime libraries.** It may link only libraries that are on PyPI:
  - `libifcoremd`, from `intel-fortran-rt`;
  - `libmmd`, from `intel-cmplr-lib-rt`;
  - `libiomp5md`, from `intel-openmp`;
  - the system C runtime.
- **heclib and HDF5.** Link them statically, which is the fork's default.
- **OpenMP.** The conda-forge ifx links LLVM's `libomp.dll`, which isn't on
  PyPI, and its `libiomp5md.lib` is an alias for that DLL. Link against the
  real `libiomp5md.lib` from the `intel-openmp` PyPI wheel instead. Unpack
  `intel_openmp-<version>-…-win_amd64.whl` and put its `Library\lib` first on
  `LIB`.

Windows, from the fork's source tree, with ifx 2026.1.1 set up and the
`intel-openmp` import library first on `LIB`:

```bat
cmake -S . -B build-wheel -G Ninja -DCMAKE_BUILD_TYPE=Release ^
      -DCMAKE_Fortran_COMPILER=ifx -DIWFM_MONOLITHIC_BUILD=ON -DIWFM_SHARED_RUNTIME=ON ^
      -DIWFM_BUILD_SIMULATION=OFF -DIWFM_BUILD_PREPROCESSOR=OFF -DIWFM_BUILD_BUDGET=OFF ^
      -DIWFM_BUILD_ZBUDGET=OFF -DIWFM_BUILD_TESTS=OFF -DIWFM_BUILD_DLL=ON
cmake --build build-wheel --target IWFM_C_DLL
```

The library is written to the fork's `Bin\IWFM_C_x64.dll`, overwriting
whatever is there. Check its imports with
`dumpbin /dependents Bin\IWFM_C_x64.dll`. Expect only `libiomp5md.dll`,
`libifcoremd.dll`, `libmmd.dll`, `KERNEL32.dll`, `VCRUNTIME140.dll` and
`api-ms-win-crt-*`.

Linux: build in the `quay.io/pypa/manylinux_2_28_x86_64` image, so the
library needs nothing newer than glibc 2.28. Use
`scripts/build_manylinux_library.sh`. It installs ifx 2026.1.1 from
conda-forge with micromamba, builds the C dependencies with the image's gcc,
and links OpenMP against the real `libiomp5.so` from the `intel-openmp` PyPI
wheel. conda-forge's `libiomp5.so` is a symlink to LLVM's `libomp.so`. Set up
a work directory, then run the script:

```bash
mkdir -p WORK/src WORK/rt
git -C path/to/fork archive HEAD | tar -x -C WORK/src
pip download --no-deps --only-binary=:all: --platform manylinux_2_28_x86_64 -d WORK/rt \
    intel-openmp==2026.1.1 intel-fortran-rt==2026.1.1 intel-cmplr-lib-rt==2026.1.1
cp scripts/build_manylinux_library.sh WORK/
docker run --rm -v "$PWD/WORK:/lw" quay.io/pypa/manylinux_2_28_x86_64 bash /lw/build_manylinux_library.sh
```

The script prints the library's `NEEDED` entries and highest glibc symbol
version. Expect:
- `libifcoremt.so.5`, `libifport.so.5`, `libimf.so`, `libsvml.so`,
  `libintlc.so.5` and `libiomp5.so`, all from the PyPI runtime wheels;
- glibc system libraries;
- `GLIBC_2.28` or lower.

A pip install has no RPATH to `<prefix>/lib`, where Intel's PyPI packages put
their libraries. pywfm's loader therefore reads the library's ELF
dependencies and preloads the Intel runtimes from there before loading it.

## Building a wheel

```bash
pip install build
python scripts/stage_library.py path/to/IWFM_C_x64.dll path/to/IWFM/LICENSE --runtime-version 2026.1.1
python -m build --wheel
python scripts/stage_library.py --clean      # back to a pure checkout
```

`stage_library.py` copies three files into `src/pywfm/_lib`:
- the library;
- IWFM's license, as `LICENSE-IWFM`;
- `runtime-requirements.txt`, listing `intel-fortran-rt`, `intel-cmplr-lib-rt`
  and `intel-openmp`, each pinned to `--runtime-version`.

`setup.py` then marks the wheel as platform-specific, tags it
`py3-none-<platform>`, and adds those requirements. Without a staged library,
`python -m build` produces the pure `py3-none-any` wheel and the sdist.

On Linux, build in the manylinux image and give the platform tag
explicitly; setuptools would otherwise tag the wheel `linux_x86_64`, which
PyPI rejects:

```bash
python -m build --wheel -C--build-option=--plat-name=manylinux_2_28_x86_64
```

`auditwheel show` confirms the glibc 2.28 limit. It still reports only
`linux_x86_64`, because it expects the Intel libraries inside the wheel.
They come from Intel's PyPI packages instead, by design, so don't run
`auditwheel repair`: it would copy them into the wheel.

Before uploading, test the wheel in a clean environment with no `PYWFM_DLL`.
pywfm must report the bundled library, and the suite must pass. The
regression tests compare simulated values exactly with the release's
baseline.

```bash
python -m venv /tmp/wheeltest && /tmp/wheeltest/Scripts/python -m pip install dist/*.whl pytest
/tmp/wheeltest/Scripts/pywfm get-api-version          # Library: …/site-packages/pywfm/_lib/…
/tmp/wheeltest/Scripts/python -m pytest tests/unit tests/integration tests/regression
/tmp/wheeltest/Scripts/python -m pytest --runsim tests/integration/model/test_simulation.py
```

Upload with `twine upload dist/*`.

## conda-forge

pywfm on conda-forge is a pure `noarch: python` package (`recipe/`) that
depends on `libiwfm`. The `libiwfm` and `heclib` recipes live in the fork,
under `packaging/conda-forge/`. Both go to conda-forge through
`staged-recipes`, then are maintained in their feedstocks.
