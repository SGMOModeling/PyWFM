import os
import platform
import shutil
import sys
import tempfile

import click

from pywfm._dll import LIBRARY_NAMES
from pywfm.utilities import extract_all_zips, download_zip, get_iwfm_url


def _environment_library_dir():
    """Directory where the active environment keeps shared libraries."""
    if platform.system() == "Windows":
        return os.path.join(sys.prefix, "Library", "bin")
    return os.path.join(sys.prefix, "lib")


@click.group()
def cli():
    pass


@cli.command()
@click.option("--path", default=None, help="location of the IWFM API to use for pywfm.")
@click.option(
    "--version",
    default=1848,
    help="build number of the stock IWFM API to download from the CNRA Open "
    "Data Platform (e.g. 1594, 1747, 1848).",
)
def setup_pywfm(path, version):
    """Puts the IWFM API into the active environment for use with pywfm"""
    dll_name = LIBRARY_NAMES[0]
    dll_dir = _environment_library_dir()
    target = os.path.join(dll_dir, dll_name)
    click.echo(f"Installing {dll_name} into {dll_dir}")
    os.makedirs(dll_dir, exist_ok=True)

    # if a path is provided to a local copy of the IWFM API, use it
    if path:
        if os.path.isdir(path):
            path = os.path.join(path, dll_name)

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"{dll_name} was not found in path provided. Check the path and try again."
            )

        shutil.copy2(path, target)
        return

    temp_path = tempfile.mkdtemp(prefix="pywfm_")
    try:
        download_zip(get_iwfm_url(version), temp_path)
        extract_all_zips(temp_path)
        for root, dirs, files in os.walk(temp_path):
            if dll_name in files:
                shutil.copy2(os.path.join(root, dll_name), target)
                break
        else:
            raise FileNotFoundError(f"{dll_name} was not found in the IWFM {version} download.")
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@cli.command()
def get_api_version():
    """Returns the version information of the IWFM API"""
    from pywfm import dll_path, abi
    from pywfm.misc import IWFMMiscellaneous

    misc = IWFMMiscellaneous()
    version = misc.get_version()

    for pkg, v in version.items():
        print(f"{pkg:.<50s} {v}")
    print(f"{'Library':.<50s} {dll_path()}")
    print(f"{'API generation':.<50s} {abi()}")
