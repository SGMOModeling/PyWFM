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

.. versionadded:: 0.2.6
   pywfm now includes the capability to instantiate multiple models simultaneously and toggle between them. This was added in version 2024.0.1594 of the IWFM API.

.. deprecated:: 0.2.6
   pywfm no longer includes an indicator for the version of the IWFM API in the pywfm version.

   .. versionadded:: 0.2.2
      pywfm now includes an indicator for the version of the IWFM API in the version
      
      Prior versions of pywfm still use this approach as shown below.
      +----------------------+------------------+
      | pywfm 0.2.5.1273 | IWFM 2015.0.1273 |
      +----------------------+------------------+
      | pywfm 0.2.5.1403 | IWFM 2015.0.1403 |
      +----------------------+------------------+
      | pywfm 0.2.4.1443 | IWFM 2015.1.1443 |
      +----------------------+------------------+


--------
Overview
--------

The pywfm library includes 4 classes:

   * :doc:`IWFMModel <reference/model>`
   * :doc:`IWFMBudget <reference/budget>`
   * :doc:`IWFMZBudget <reference/zbudget>`
   * :doc:`IWFMMiscellaneous <reference/misc>`

.. versionadded:: 0.2.5
   pywfm now allows the IWFMMiscellaneous class to be instantiated directly. This was done to allow the addition of convenience scripts in a command line interface (CLI)
   It also reduces duplication of code because each class was calling ctypes.CDLL when it can be called once in IWFMMiscellaneous and inherited by the other classes.
   Users can still access all the functionality of IWFMMiscellaneous via IWFMModel, IWFMBudget, and IWFMZBudget classes.



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
