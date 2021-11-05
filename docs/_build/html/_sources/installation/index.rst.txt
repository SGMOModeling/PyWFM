############
Installation
############

This guide is an overview and explains the installation process.

********
Overview
********

To use the iwfmdll package there are several steps required.


1. Make sure python 3 [#pythonversion]_ is installed on your computer and pip runs from the command line
========================================================================================================

   To check your python version, open command prompt and type:

   python --version

   .. image:: ../_static/checkpythonversion.png
      :alt: command prompt window showing command to check python version

   .. note::
      if this command does not work, you will need to either install python or add python to the Path Environment Variable

      To install python, go to: https://www.python.org/




2. Download the iwfmdll python code
===================================

   pip install git+https://github.com/SGMOModeling/IWFMDLL.git

   or

   go to https://github.com/SGMOModeling/IWFMDLL and download the code as a ZIP archive.

   .. image:: ../_static/CodeDownload.png
      :alt: github link to download iwfmdll module

   .. note::
      By downloading the ZIP archive of the iwfmdll package, the module can be upzipped and placed 
      in a location of the users choice. a .pth file containing the path to the iwfmdll package can 
      be saved in the site-packages folder of the python installation.

      For example, with an ArcGIS Pro python environment the site packages folder for a cloned
      environment may be located here:

      C:\\Users\\<UserName>\\AppData\\Local\\ESRI\\conda\\envs\\<VirtualEnvironmentName>\\Lib\\site-packages




3. Download the latest version of IWFM
======================================

   Go to https://data.cnra.ca.gov/dataset/iwfm-integrated-water-flow-model

   Click on the download button next to the latest version of IWFM

   .. image:: ../_static/DownloadIWFM.png
      :alt: Download IWFM from the CNRA Open Data Platform

   .. important::
      Downloading IWFM includes the IWFM dll that the iwfmdll python module is dependent on to work


4.

.. rubric Footnotes

.. [#pythonversion] The iwfmdll module has been tested using python 3.7.9