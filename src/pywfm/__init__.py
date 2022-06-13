import os
import platform
import ctypes

if platform.uname()[0] == "Windows":
    DLL_PATH = os.path.normpath(os.path.join(__file__, "../../../../Library/bin"))
    DLL = "IWFM2015_C_x64.dll"
    LIB = ctypes.CDLL(os.path.join(DLL_PATH, DLL))
elif platform.uname()[0] == "Linux":
    SO_PATH = os.path.join(os.path.expanduser('~'), "iwfm-docker/build/iwfm")
    SO = "libIWFMLib.so"
    LIB = ctypes.CDLL(os.path.join(SO_PATH, SO))


from pywfm.model import IWFMModel
from pywfm.budget import IWFMBudget
from pywfm.zbudget import IWFMZBudget
from pywfm.decorators import program_timer
