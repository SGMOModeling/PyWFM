.. _reference:

#############
API Reference
#############

.. currentmodule:: iwfmdll

This section provides detailed documentation of the available 
functionality built into the iwfmdll python library

********************
Main IWFMDLL Classes
********************

The iwfmdll module is separated into three main classes.

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

***************
Class Reference
***************

.. toctree::
   :maxdepth: 2

   IWFMModel <model>
   IWFMBudget <budget>
   IWFMZBudget <zbudget>
