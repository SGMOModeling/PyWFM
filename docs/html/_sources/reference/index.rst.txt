.. _reference:

#############
API Reference
#############

.. currentmodule:: pywfm

This section provides detailed documentation of the available 
functionality built into the pywfm python library

********************
Main PyWFM Classes
********************

The pywfm module is separated into three main classes and one base class.

The IWFMModel class is designed around the IWFM Model Object 
which allows for interacting with the model data

.. autosummary::
   :toctree: generated/

   IWFMModel

The IWFMBudget class is designed around the IWFM Budget 
application which summarizes model simulation results to
a preset area or extent

.. autosummary::
   :toctree: generated/

   IWFMBudget

The IWFMZBudget class is designed around the IWFM ZBudget
application which summarizes model simulation results to
a user-customized area or extent

.. autosummary::
   :toctree: generated/

   IWFMZBudget

The IWFMMiscellaneous class is designed around base functionality 
provided by IWFM. It provides internal IDs for different built-in 
types and utility functions for working with dates and string arrays.

.. autosummary::
   :toctree: generated/

   misc.IWFMMiscellaneous

***************
Class Reference
***************

.. toctree::
   :maxdepth: 2

   IWFMModel <model>
   IWFMBudget <budget>
   IWFMZBudget <zbudget>
   IWFMMiscellaneous <misc>
