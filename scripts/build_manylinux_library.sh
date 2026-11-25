#!/bin/bash
# Build libiwfm_c.so for a manylinux_2_28 wheel, in quay.io/pypa/manylinux_2_28_x86_64.
#
# usage (from a host with docker; WORK holds the fork source as src/ and the
# Intel runtime wheels from PyPI, of the ifx version below, as rt/*.whl; copy
# this script into WORK):
#   docker run --rm -v WORK:/lw quay.io/pypa/manylinux_2_28_x86_64 bash /lw/build_manylinux_library.sh
# Output: WORK/out/libiwfm_c.so. See BUILD.md.
set -euo pipefail
cd /lw
# ifx 2026.1.1 from conda-forge, plus cmake and ninja
if [ ! -x /opt/ifx/bin/ifx ]; then
  curl -sL https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj -C /usr/local bin/micromamba
  /usr/local/bin/micromamba create -y -q -p /opt/ifx -c conda-forge ifx_linux-64=2026.1.1 cmake ninja > /dev/null
fi
# Intel runtimes as pip installs them: the link must name libiomp5.so (Intel),
# not the conda-forge libiomp5.so symlink to LLVM libomp.so
rm -rf rtlib && mkdir rtlib
for w in rt/*.whl; do python3 -c "import zipfile,sys;z=zipfile.ZipFile(sys.argv[1]);[z.extract(n,'rtx') for n in z.namelist() if '/data/lib/' in n]" "$w"; done
cp -a rtx/*/data/lib/* rtlib/
export MAMBA_ROOT_PREFIX=/opt/mamba; set +u; eval "$(/usr/local/bin/micromamba shell hook -s bash)"; micromamba activate /opt/ifx; set -u
export CC=gcc
rm -rf build-wheel src/Bin
cmake -S src -B build-wheel -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_Fortran_COMPILER=ifx \
  -DIWFM_MONOLITHIC_BUILD=ON -DIWFM_SHARED_RUNTIME=ON \
  -DIWFM_BUILD_SIMULATION=OFF -DIWFM_BUILD_PREPROCESSOR=OFF -DIWFM_BUILD_BUDGET=OFF \
  -DIWFM_BUILD_ZBUDGET=OFF -DIWFM_BUILD_TESTS=OFF -DIWFM_BUILD_DLL=ON \
  -DCMAKE_SHARED_LINKER_FLAGS="-L/lw/rtlib" > cfg.log 2>&1 || { tail -40 cfg.log; exit 1; }
cmake --build build-wheel --target IWFM_C_DLL --parallel $(nproc) > build.log 2>&1 || { grep -m5 -B2 -A10 -i "error" build.log; tail -20 build.log; exit 1; }
SO=$(ls src/Bin/libiwfm_c*.so | head -1); echo "built $SO"
mkdir -p out && cp "$SO" out/libiwfm_c.so
echo "== NEEDED"; objdump -p out/libiwfm_c.so | grep NEEDED
echo "== max GLIBC symbol version"; objdump -T out/libiwfm_c.so | grep -o "GLIBC_[0-9.]*" | sort -uV | tail -3
