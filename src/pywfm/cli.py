import os
import shutil
import click

from pywfm import LIB
from pywfm.misc import IWFMMiscellaneous

from pywfm.utilities import extract_all_zips, download_zip, get_iwfm_url


@click.group()
def cli():
    pass


@cli.command()
@click.option("--path", default=None, help="location of the IWFM API to use for pywfm.")
@click.option(
    "--version",
    default=1443,
    help="version of the IWFM API to download and install. options: 1273, 1401, or 1443",
)
def setup_pywfm(path, version):
    """Puts the IWFM API into the correct location for use with pywfm"""
    dll_path, dll_name = os.path.split(LIB)
    # create the directory if it doesn't exist
    click.echo(f"Creating {dll_path} in active python environment")
    os.makedirs(dll_path, exist_ok=True)

    # if a path is provided to a local copy of the IWFM API, use it
    if path:

        if dll_name not in path:
            path = os.path.join(path, dll_name)

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"{dll_name} was not found in path provided. Check the path and try again."
            )

        shutil.copy2(path, LIB)

    else:

        temp_path = "temp"

        download_zip(get_iwfm_url(version), temp_path)

        extract_all_zips(temp_path)

        for root, dirs, files in os.walk(temp_path):
            for f in files:
                if f == dll_name:
                    shutil.copy2(os.path.join(root, f), LIB)
                    break

        shutil.rmtree(temp_path)


@cli.command()
def get_api_version():
    """Returns the version information of the IWFM API"""
    misc = IWFMMiscellaneous()
    version = misc.get_version()

    for pkg, v in version.items():
        print(f"{pkg:.<50s} {v}")
