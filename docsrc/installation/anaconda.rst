###########################
Installation using Anaconda
###########################

1. Make sure anaconda is installed
==================================
   
   In the start menu, type anaconda prompt. If it appears, then anaconda is installed.

   .. note::
      To install anaconda:

      go to https://www.anaconda.com/products/individual

2. Open anaconda prompt and create a new virtual environment
============================================================

   .. code:: bash
      
      conda create -n <env_name> python
   
   .. note::
      pywfm has been tested using python 3.7.9, 3.7.11, 3.10.2

3. Activate the conda environment you created
=============================================

   .. code:: bash
      
      conda activate <env_name>

4. Install pywfm
================

   .. code:: bash
      
      conda install -c cadwr-sgmo pywfm

   .. note::
      This will install the latest version of the iwfm dll (IWFM 2015.1.1443)
      
   If you want to install pywfm with version 2015.0.1273 of the dll, use:

   .. code:: bash
      
      conda install -c cadwr-sgmo pywfm=0.2.3.1273
   
   