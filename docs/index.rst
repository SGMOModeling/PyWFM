.. PyWFM documentation master file

#####################
PyWFM Documentation
#####################

pywfm is a python package that exposes the functionality of the IWFM DLL

--------
Overview
--------

The pywfm library includes 3 main classes:

   * IWFMModel 
   * IWFMBudget 
   * IWFMZBudget 

Each of these inherits from the IWFMMiscellaneous base class. Many of the methods in the IWFMMiscellaneous base class cannot be used on their own because the IWFMMiscellaneous class was designed without direct access to the IWFM DLL. Users can access all of this functionality from within the IWFMModel, IWFMBudget, and IWFMZBudget classes.

------
Design
------

The pywfm library wraps each of the IWFM DLL functions so that the user does not have to deal with the IWFM DLL syntax directly. Instead, users familiar with python can work with standard python objects such as strings, ints, floats, lists, and numpy arrays.

Many parts of the IWFM DLL procedures are handled internally allowing the user to provide only a few pieces of required information to obtain results.

.. toctree::
   :maxdepth: 1
   :hidden:
   
   Installation <installation/index>
   Tutorial <tutorial/index>
   API Reference <reference/index>