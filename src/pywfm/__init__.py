import os

DLL_PATH = os.path.normpath(os.path.join(__file__, "../../../../Library/bin"))
DLL = "IWFM2015_C_x64.dll"

from pywfm.model import IWFMModel
from pywfm.budget import IWFMBudget
from pywfm.zbudget import IWFMZBudget
from pywfm.decorators import program_timer
