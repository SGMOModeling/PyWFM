############
Installation
############

This guide is an overview and explains the installation process.

********
Overview
********

To use the pywfm package there are several steps required.


1. Make sure python 3 [#pythonversion]_ is installed on your computer and pip runs from the command line
========================================================================================================

   To check your python version, open command prompt and type:

   .. code-block:: bash
   
      python --version

   .. image:: ../_static/checkpythonversion.png
      :alt: command prompt window showing command to check python version

   .. note::
      if this command does not work, you will need to either install python or add python to the Path Environment Variable

      To install python, go to: https://www.python.org/




2. Download the pywfm python code
===================================

   .. code-block:: bash
      
	  pip install git+https://github.com/SGMOModeling/PyWFM.git

   or

   go to https://github.com/SGMOModeling/PyWFM and download the code as a ZIP archive.

   .. image:: ../_static/CodeDownload.png
      :alt: github link to download pywfm module

   .. note::
      By downloading the ZIP archive of the pywfm package, the module can be upzipped and placed 
      in a location of the users choice. a .pth file containing the path to the pywfm package can 
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
      Downloading IWFM includes the IWFM dll that the pywfm python module is dependent on to work


4.

.. rubric Footnotes

.. [#pythonversion] The pywfm module has been tested using python 3.7.9