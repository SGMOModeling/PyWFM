****************
PyWFM Tutorial 1
****************

Created by: Tyler Hatch/DWR

**Description:** This tutorial walks a user of pywfm through how to run the IWFM Sample Model from python

Getting Started
===============

.. code-block:: py

   from pywfm import IWFMModel
   

Create a Function to Perform the Simulation
===========================================

.. code-block:: py

   def run_model(model):
       ''' uses an IWFM model object to run a model simulation '''
       while not model.is_end_of_simulation():
           # advance the simulation time one time step forward
           model.advance_time()

           # read all time series data from input files
           model.read_timeseries_data()

           # Simulate the hydrologic process for the timestep
           model.simulate_for_one_timestep()

           # print the results to the user-specified output files
           model.print_results()

           # advance the state of the hydrologic system in time
           model.advance_state()
		   

.. note::
   
   This function provides template code for the user to interact with the model application on a timestep
   by timestep basis. If the user only wants to run the entire simulation from python using IWFMModel.simulate_all().
   
   Otherwise, certain time series data can be updated during a simulation using IWFMModel.read_timeseries_data_overwrite()
		   

Set Paths to the IWFM DLL, Preprocessor Input File, and Simulation Input File
=============================================================================

.. code-block:: py

   # specify paths to preprocessor and simulation main files
   pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
   sim_file = 'Simulation_MAIN.IN'
   
.. important::

   These paths assume this code is saved in the simulation folder of the Sample Model and the DLL is in a location
   relative to the simulation folder
   

Create the Model Object and Run the Simulation
==============================================

.. code-block:: py

   with IWFMModel(pp_file, sim_file, is_for_inquiry=0) as sm:
       run_model(sm)
	   
	   
.. note::

   the context manager 'with' is equivalent to calling:
   
   .. code-block:: py
   
      sm = IWFMModel(pp_file, sim_file, is_for_inquiry=0)
      run_model(sm)
      sm.kill()
      sm.close_log_file()