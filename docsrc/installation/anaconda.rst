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
      
      conda create -n <env_name>
   
   .. note::
      pywfm has been tested using python 3.7.9, 3.7.11, 3.10.2, 3.11.7, 3.12.2, 3.13.11

3. Activate the conda environment you created
=============================================

   .. code:: bash
      
      conda activate <env_name>

4. Install pywfm
================

   .. code:: bash
      
      conda install iwfm-pywfm

   .. note::
      This will install the latest version of the iwfm dll (IWFM 2025.0.1747)
      
   If you want to install pywfm with version 2015.0.1273 of the dll, use:

   .. code:: bash
      
      conda install iwfm-pywfm iwfmdll=2015.0.1273

   Currently, the following versions of the IWFM DLL are available via conda:
   +----------------------+------------------+
   | IWFM DLL Version     | pywfm Version    |
   +----------------------+------------------+
   | 2015.0.1273         | 0.2.6         |
   +----------------------+------------------+
   | 2015.0.1403         | 0.2.6         |
   +----------------------+------------------+
   | 2015.1.1443         | 0.2.6         |
   +----------------------+------------------+
   | 2024.2.1594         | 0.2.6         |
   +----------------------+------------------+
   | 2025.0.1747         | 0.2.6         |
   +----------------------+------------------+
   
   