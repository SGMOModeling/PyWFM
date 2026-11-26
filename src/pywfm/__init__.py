from pywfm.exceptions import IWFMError
from pywfm._dll import load_dll, get_dll, dll_path, find_library, abi, core_version

__version__ = "1.0.0.dev0"

from pywfm.model import IWFMModel
from pywfm.budget import IWFMBudget
from pywfm.zbudget import IWFMZBudget
from pywfm.decorators import program_timer
from pywfm.cli import cli
from pywfm.utilities import run_with_large_stack


def __getattr__(name):
    # Backward compatibility: IWFM_API / LIB used to be loaded at import time.
    # They now resolve on first access, which loads the library.
    if name == "IWFM_API":
        return get_dll()
    if name == "LIB":
        return str(dll_path())
    raise AttributeError(f"module 'pywfm' has no attribute {name!r}")
