# IWFMDLL
---
python library to expose the functionality of the IWFM DLL

To use the iwfmdll module, users need to download this repository

**Note** Users must also download the IWFM DLL.

The IWFM DLL can be downloaded from the [CNRA Open Data Platform](https://data.cnra.ca.gov/dataset/iwfm-integrated-water-flow-model)

## Overview
---
The iwfmdll library includes 3 main classes (IWFM_Model, IWFM_Budget, and IWFM_ZBudget). Each of these inherits from the IWFM_Miscellaneous base class. Many of the methods in the IWFM_Miscellaneous base class cannot be used on their own because the IWFM_Miscellaneous class was designed without direct access to the IWFM DLL. Users can access all of this functionality from within the IWFM_Model, IWFM_Budget, and IWFM_Zbudget classes.

## Design
---
The iwfmdll library wraps each of the IWFM DLL functions so that the user does not have to deal with the IWFM DLL syntax directly. Instead, users familiar with python can work with standard python objects such as strings, ints, floats, lists, and numpy arrays.

Many parts of the IWFM DLL procedures are handled internally allowing the user to provide only a few pieces of required information to obtain results.

### IWFM_Model
the IWFM_Model class can be run in two modes.
1. is_for_inquiry=0, which allows running model simulations from python and interacting with the model simulations at runtime
2. is_for_inquiry=1, which allows obtaining data from a model that has already been completed

### IWFM_Budget
the IWFM_Budget class performs budget processing from the HDF output files

### IWFM_ZBudget
the IWFM_ZBudget class performs ZBudgets based on user provided zone definitions and the HDF output files

## IWFM_Model methods
To obtain data from an already completed model, the following code can be used:

```python
# import libraries
from iwfmdll import IWFM_Model

# set paths to files needed to create model object
iwfm_dll = 'IWFM-2015.0.1177/DLL/Bin/IWFM2015_C_x64.dll'
preprocessor_in_file = 'SampleModel/Preprocessor/PreProcessor_MAIN.IN'
simulation_in_file = 'SampleModel/Simulation/Simulation_MAIN.IN'

# create instance of the IWFM_Model class
m = IWFM_Model(dll_path, preprocessor_in_file, simulation_in_file)
```

## IWFM_Budget methods
To use IWFM_Budget, the following code can be used:

```python
# import libraries
from iwfmdll import IWFM_Budget

# set paths to files needed to create budget object
iwfm_dll = 'IWFM-2015.0.1177/DLL/Bin/IWFM2015_C_x64.dll'
gw_budget_file = 'SampleModel/Results/GW.hdf'

gw_budget = IWFM_Budget(iwfm_dll, gw_budget_file)
```

## IWFM_ZBudget methods