from iwfmdll import IWFMModel

DLL = r'C:\Users\hatch\Desktop\IWFM\IWFM-2015.0.1273\DLL\Bin\IWFM2015_C_x64.dll'
pp_file = r'C:\Users\hatch\Desktop\IWFM\IWFM-2015.0.1273\SampleModel\Preprocessor\PreProcessor_MAIN.IN'
sim_file = r'C:\Users\hatch\Desktop\IWFM\IWFM-2015.0.1273\SampleModel\Simulation\Simulation_MAIN.IN'

with IWFMModel(DLL, pp_file, sim_file) as model:
    output_interval = model.get_output_interval()

print(output_interval)