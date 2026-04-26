import os
import ctypes
import platform

from pywfm.exceptions import IWFMError

__version__ = "0.3.0-rc1"

if platform.uname()[0] == "Windows":
    dll_options = ("IWFM_C_x64.dll", "IWFM2015_C_x64.dll")
    for option in dll_options:
        DLL_PATH = os.path.normpath(os.path.join(__file__, "../../../../Library/bin"))
        DLL = option
        LIB = os.path.join(DLL_PATH, DLL)
        if os.path.exists(LIB):
            break
    else:
        raise FileNotFoundError("No IWFM API DLL was found.")

elif platform.uname()[0] == "Linux":
    SO_PATH = os.path.join(os.path.expanduser("~"), "iwfm-docker/build/iwfm")
    SO = "libIWFMLib.so"
    LIB = os.path.join(SO_PATH, SO)

IWFM_API = ctypes.CDLL(LIB)

# 0.3.x requires the handle-based IWFM kernel (commit 393e02e+).
# That kernel removed IW_Model_Switch — its presence is the unambiguous
# signal that the loaded DLL predates the rewrite and won't work here.
if hasattr(IWFM_API, "IW_Model_Switch"):
    raise IWFMError(
        "pywfm {} requires an IWFM DLL built from kernel commit 393e02e or "
        "later (handle-based API). The DLL at {} exports IW_Model_Switch, "
        "which means it predates that change. For stock 2024/2025 or "
        "2015-series DLLs, install iwfm-pywfm<0.3 (the 0.2.x maintenance line)."
        .format(__version__, LIB)
    )


from pywfm.model import IWFMModel
from pywfm.budget import IWFMBudget
from pywfm.zbudget import IWFMZBudget
from pywfm.decorators import program_timer
from pywfm.cli import cli
