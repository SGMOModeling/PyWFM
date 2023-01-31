.. PyWFM documentation master file

#####################
PyWFM Documentation
#####################

**Current Version**: |release|

pywfm is a python package that exposes the functionality of the IWFM API

.. warning::
   IWFM Applications simulated with a different version of IWFM than used with pywfm may fail silently.
   In these cases, users should be able to rerun the model with the same version of IWFM as the IWFM API included with pywfm.
   If you do not plan to rerun the model, install the version of pywfm with the same IWFM API, if available.

.. versionadded:: 0.2.2
   pywfm now includes an indicator for the version of the IWFM API in the version
   
   +----------------------+------------------+
   | pywfm |release|.1273 | IWFM 2015.0.1273 |
   +----------------------+------------------+
   | pywfm |release|.1403 | IWFM 2015.0.1403 |
   +----------------------+------------------+
   | pywfm |release|.1443 | IWFM 2015.1.1443 |
   +----------------------+------------------+


--------
Overview
--------

The pywfm library includes 3 main classes:

   * :doc:`IWFMModel <reference/model>`
   * :doc:`IWFMBudget <reference/budget>`
   * :doc:`IWFMZBudget <reference/zbudget>`

Each of these inherits from the IWFMMiscellaneous base class. Many of the methods in the IWFMMiscellaneous base class cannot be used on their own because the IWFMMiscellaneous class was designed without direct access to the IWFM API. Users can access all of this functionality from within the IWFMModel, IWFMBudget, and IWFMZBudget classes.

------
Design
------

The pywfm library wraps each of the IWFM API procedures so that the user does not have to deal with the IWFM API syntax directly. Instead, users familiar with python can work with standard python objects such as strings, ints, floats, lists, and numpy arrays.

Many parts of the IWFM API are handled internally allowing the user to provide only a few pieces of required information to obtain results.

.. note::
   The IWFM API is contained within a dynamic link library (DLL) and may be referred to as the IWFM DLL

.. toctree::
   :maxdepth: 1
   :hidden:
   
   Installation <installation/index>
   Tutorial <tutorial/index>
   API Reference <reference/index>

.. container:: button

    :doc:`Installation <installation/index>` :doc:`Tutorial <tutorial/index>` 
    :doc:`API Reference <reference/index>` `IWFM <https://water.ca.gov/Library/Modeling-and-Analysis/Modeling-Platforms/Integrated-Water-Flow-Model>`_


------------
Useful Links
------------
 `Download IWFM <https://data.cnra.ca.gov/dataset/iwfm-integrated-water-flow-model>`_ | `Source Repository (Github) <https://github.com/SGMOModeling/PyWFM>`_ | `SGMA Data and Tools <https://water.ca.gov/programs/groundwater-management/data-and-tools>`_
