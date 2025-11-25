import os
import ctypes
import platform

__version__ = "0.2.6"

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


from pywfm.model import IWFMModel
from pywfm.budget import IWFMBudget
from pywfm.zbudget import IWFMZBudget
from pywfm.decorators import program_timer
from pywfm.cli import cli
