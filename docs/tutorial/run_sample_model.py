# Tutorial 1
# Created by: Tyler Hatch/DWR
# Date: October 5, 2021
# Description: This tutorial walks a user of the iwfmdll python package
# through how to run the IWFM Sample Model from python

# Set-Up: 
# 1. Copy the code to a text editor
# 2. save the file as 'run_sample_model.py' in the Simulation folder of the Sample Model
# 3. open command prompt and navigate to the Simulation folder of the Sample Model
# 4. run the command 'python run_sample_model.py'
from iwfmdll import IWFMModel

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

if __name__ == "__main__":
    
    # specify path to IWFM DLL
    dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
    
    # specify paths to preprocessor and simulation main files
    pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
    sim_file = 'Simulation_MAIN.IN'

    with IWFMModel(dll, pp_file, sim_file, is_for_inquiry=0) as sm:
        run_model(sm)
