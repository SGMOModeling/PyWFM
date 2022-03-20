# PyWFM
---
python library to expose the functionality of the IWFM DLL

Full documentation of PyWFM is available [here](https://sgmomodeling.github.io/PyWFM/html/index.html)

To use the pywfm module, users need to download this repository

**Note** Users must also download the IWFM DLL.

The IWFM DLL can be downloaded from the [CNRA Open Data Platform](https://data.cnra.ca.gov/dataset/iwfm-integrated-water-flow-model)

## Overview
---
The pywfm library includes 3 main classes (IWFMModel, IWFMBudget, and IWFMZBudget). Each of these inherits from the IWFMMiscellaneous base class. Many of the methods in the IWFMMiscellaneous base class cannot be used on their own because the IWFMMiscellaneous class was designed without direct access to the IWFM DLL. Users can access all of this functionality from within the IWFMModel, IWFMBudget, and IWFMZBudget classes.

## Design
---
The pywfm library wraps each of the IWFM DLL functions so that the user does not have to deal with the IWFM DLL syntax directly. Instead, users familiar with python can work with standard python objects such as strings, ints, floats, lists, and numpy arrays.

Many parts of the IWFM DLL procedures are handled internally allowing the user to provide only a few pieces of required information to obtain results.

### IWFMModel
the IWFMModel class can be run in two modes.
1. is_for_inquiry=0, which allows running model simulations from python and interacting with the model simulations at runtime
2. is_for_inquiry=1, which allows obtaining data from a model that has already been completed

### IWFMBudget
the IWFMBudget class performs budget processing from the HDF output files

### IWFMZBudget
the IWFMZBudget class performs ZBudgets based on user provided zone definitions and the HDF output files

## IWFMModel methods
To obtain data from an already completed model, use the following code:

```python
# import libraries
from pywfm import IWFMModel

# set paths to files needed to create model object
preprocessor_in_file = 'SampleModel/Preprocessor/PreProcessor_MAIN.IN'
simulation_in_file = 'SampleModel/Simulation/Simulation_MAIN.IN'

# create instance of the IWFMModel class
m = IWFMModel(preprocessor_in_file, simulation_in_file)
```
To see all methods available within the IWFMModel class, type the following:
```python
from pywfm import IWFMModel

help(IWFMModel)
```

## IWFMBudget methods
To use IWFMBudget, use the following code:

```python
# import libraries
from pywfm import IWFMBudget

# set paths to files needed to create budget object
gw_budget_file = 'SampleModel/Results/GW.hdf'

# create instance of the IWFMBudget class
gw_budget = IWFMBudget(gw_budget_file)
```

## IWFMZBudget methods
To use IWFMZBudget, use the following code:

```python
# import libraries
from pywfm import IWFMZBudget

# set paths to files needed to create zbudget object
gw_budget_file = 'SampleModel/Results/GW_ZBud.hdf'

# create instance of the IWFMZBudget class
z = IWFMZBudget(zbudget_file)
```
