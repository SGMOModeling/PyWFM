import os
import ctypes
import math
from typing import Type
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches

from pywfm.misc import IWFMMiscellaneous

class IWFMModel(IWFMMiscellaneous):
    ''' IWFM Model Class for interacting with the IWFM DLL

    Parameters
    ----------
    dll_path : str
        file path and name of the IWFM DLL to access IWFM procedures

    preprocessor_file_name : str
        file path and name of the model preprocessor input file

    simulation_file_name : str
        file path and name of the model simulation input file

    has_routed_streams : int, default=1
        option=1 for model having routed streams
        option=0 for model not having routed streams

    is_for_inquiry : int, default=1
        option=1 for model being accessed to return input and output data
        option=0 for model simulations

        notes:
        is_for_inquiry=1: when an instance of the IWFMModel class is 
        created for the first time, the entire model object will be 
        available for returning data. A binary file will be generated 
        for quicker loading, if this binary file exists when subsequent 
        instances of the IWFMModel object are created, not all functions
        will be available.

    Returns
    -------
    IWFMModel Object
        instance of the IWFMModel class and access to the IWFM Model Object 
        fortran procedures.
    '''
    def __init__(self, dll_path, preprocessor_file_name, simulation_file_name, has_routed_streams=1, is_for_inquiry=1):
        
        if isinstance(dll_path, str):
            self.dll_path = dll_path
        else:
            raise TypeError("DLL path must be a string.\nProvided {} is a {}".format(dll_path, type(dll_path)))
        
        if isinstance(preprocessor_file_name, str):
            self.preprocessor_file_name = ctypes.create_string_buffer(preprocessor_file_name.encode('utf-8'))
            self.length_preprocessor_file_name = ctypes.c_int(ctypes.sizeof(self.preprocessor_file_name))
        
        if isinstance(simulation_file_name, str):
            self.simulation_file_name = ctypes.create_string_buffer(simulation_file_name.encode('utf-8'))
            self.length_simulation_file_name = ctypes.c_int(ctypes.sizeof(self.simulation_file_name))
            
        if isinstance(has_routed_streams, int):
            self.has_routed_streams = ctypes.c_int(has_routed_streams)
        
        if isinstance(is_for_inquiry, int):
            self.is_for_inquiry = ctypes.c_int(is_for_inquiry)
          
        # set instance variable status to 0
        self.status = ctypes.c_int(0)
            
        self.dll = ctypes.windll.LoadLibrary(self.dll_path)

        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_New"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_New'))

        self.dll.IW_Model_New(ctypes.byref(self.length_preprocessor_file_name), 
                              self.preprocessor_file_name, 
                              ctypes.byref(self.length_simulation_file_name), 
                              self.simulation_file_name, 
                              ctypes.byref(self.has_routed_streams), 
                              ctypes.byref(self.is_for_inquiry), 
                              ctypes.byref(self.status))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.kill()
      
    def kill(self):
        ''' terminates model object, closes files associated with model,
        and clears memory
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_Kill"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_Kill'))
        
        # reset instance variable status to 0
        self.status = ctypes.c_int(0)
        
        self.dll.IW_Model_Kill(ctypes.byref(self.status))

    def get_current_date_and_time(self):
        ''' Returns the current simulation date and time 
        
        Returns
        -------
        str
            current date and time in IWFM date format i.e. MM/DD/YYYY_hh:mm

        See Also
        --------
        IWFMModel.get_n_time_steps : Returns the number of timesteps in an IWFM simulation
        IWFMModel.get_time_specs : Returns the IWFM simulation dates and time step
        IWFMModel.get_n_intervals : Returns the number of time intervals between a provided start date and end date
        IWFMModel.get_output_interval : Returns a list of the possible time intervals a selected time-series data can be retrieved at.
        IWFMModel.is_date_greater : Returns True if first_date is greater than comparison_date
        IWFMModel.increment_time : increments the date provided by the specified time interval

        Examples
        --------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_current_date_and_time()
        '09/30/1990_24:00'
        >>> model.kill()

        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file, is_for_inquiry=0)
        >>> model.advance_time()
        >>> model.get_current_date_and_time()
        '10/01/1990_24:00'
        >>> model.kill()

        Note
        ----
        1. the intent of this method is to retrieve information about the
        current time step when using the IWFM DLL to run a simulation. 
        i.e. IWFMModel object is instantiated with is_for_inquiry=0
        
        2. if this method is called when the IWFMModel object is 
        instantiated with is_for_inquiry=1, it only Returns the 
        simulation begin date and time.
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetCurrentDateAndTime"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. ' 
                                 'Check for an updated version'.format('IW_Model_GetCurrentDateAndTime'))
        
        # set length of IWFM Date and Time string
        length_date_string = ctypes.c_int(16)

        # initialize output variables
        current_date_string = ctypes.create_string_buffer(length_date_string.value)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetCurrentDateAndTime(ctypes.byref(length_date_string),
                                                current_date_string,
                                                ctypes.byref(self.status))

        return current_date_string.value.decode('utf-8')

    def get_n_time_steps(self):
        ''' Returns the number of timesteps in an IWFM simulation

        Returns
        -------
        int
            the number of timesteps in the simulation

        See Also
        --------
        IWFMModel.get_current_date_and_time : Returns the current simulation date and time
        IWFMModel.get_time_specs : Returns the IWFM simulation dates and time step
        IWFMModel.get_n_intervals : Returns the number of time intervals between a provided start date and end date
        IWFMModel.get_output_interval : Returns a list of the possible time intervals a selected time-series data can be retrieved at.
        IWFMModel.is_date_greater : Returns True if first_date is greater than comparison_date
        IWFMModel.increment_time : increments the date provided by the specified time interval

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_time_steps()
        3653
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNTimeSteps"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNTimeSteps'))
        
        # reset instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize n_nodes variable
        n_time_steps = ctypes.c_int(0)

        self.dll.IW_Model_GetNTimeSteps(ctypes.byref(n_time_steps),
                                    ctypes.byref(self.status))
        
        return n_time_steps.value

    def get_time_specs(self):
        ''' Returns the IWFM simulation dates and time step

        Returns
        -------
        tuple (length=2)
            index 0 - (list) simulation dates; index 1 - (str) simulation time step

        See Also
        --------
        IWFMModel.get_current_date_and_time : Returns the current simulation date and time
        IWFMModel.get_n_time_steps : Returns the number of timesteps in an IWFM simulation
        IWFMModel.get_n_intervals : Returns the number of time intervals between a provided start date and end date
        IWFMModel.get_output_interval : Returns a list of the possible time intervals a selected time-series data can be retrieved at.
        IWFMModel.is_date_greater : Returns True if first_date is greater than comparison_date
        IWFMModel.increment_time : increments the date provided by the specified time interval

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> time_stamps, time_interval = model.get_time_specs()
        >>> time_stamps
        ['10/02/1990_24:00',
         '10/03/1990_24:00',
         '10/04/1990_24:00',
         '10/05/1990_24:00',
         '10/06/1990_24:00',
         '10/07/1990_24:00',
         ...
         '09/29/2000_24:00'
         '09/30/2000_24:00'
         '10/01/2000_24:00']
        >>> time_interval
        '1DAY'
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetTimeSpecs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetTimeSpecs'))
            
        # set instance variable status to 0
        self.status = ctypes.c_int(0)
        
        # set input variables
        n_data = ctypes.c_int(self.get_n_time_steps())
        length_dates = ctypes.c_int(n_data.value*16)
        length_ts_interval = ctypes.c_int(8)

        # initialize output variables
        simulation_time_step = ctypes.create_string_buffer(length_ts_interval.value)
        raw_dates_string = ctypes.create_string_buffer(length_dates.value)
        delimiter_position_array = (ctypes.c_int*n_data.value)()

        self.dll.IW_Model_GetTimeSpecs(raw_dates_string,
                                       ctypes.byref(length_dates),
                                       simulation_time_step,
                                       ctypes.byref(length_ts_interval),
                                       ctypes.byref(n_data),
                                       delimiter_position_array,
                                       ctypes.byref(self.status))

        dates_list = self._string_to_list_by_array(raw_dates_string, 
                                                        delimiter_position_array, n_data)

        sim_time_step = simulation_time_step.value.decode('utf-8')

        return dates_list, sim_time_step

    def get_output_interval(self):
        ''' Returns a list of the possible time intervals a selected
        time-series data can be retrieved at.

        Returns
        -------
        list of strings
            list of available output intervals for given data type

        See Also
        --------
        IWFMModel.get_current_date_and_time : Returns the current simulation date and time
        IWFMModel.get_n_time_steps : Returns the number of timesteps in an IWFM simulation
        IWFMModel.get_time_specs : Returns the IWFM simulation dates and time step 
        IWFMModel.get_n_intervals : Returns the number of time intervals between a provided start date and end date
        IWFMModel.is_date_greater : Returns True if first_date is greater than comparison_date
        IWFMModel.increment_time : increments the date provided by the specified time interval

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_output_interval()
        ['1DAY', '1WEEK', '1MON', '1YEAR']
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetOutputIntervals"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetOutputIntervals'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # set length of output intervals character array to 160 or larger
        length_output_intervals = ctypes.c_int(160)

        # set maximum number of time intervals to 20 or larger
        max_num_time_intervals = ctypes.c_int(20)

        # initialize output variables
        output_intervals = ctypes.create_string_buffer(length_output_intervals.value)
        actual_num_time_intervals = ctypes.c_int(0)
        delimiter_position_array = (ctypes.c_int*max_num_time_intervals.value)()
            
        self.dll.IW_Model_GetOutputIntervals(output_intervals, 
                                             ctypes.byref(length_output_intervals),
                                             delimiter_position_array,
                                             ctypes.byref(max_num_time_intervals),
                                             ctypes.byref(actual_num_time_intervals),
                                             ctypes.byref(self.status))

        return self._string_to_list_by_array(output_intervals, 
                                                   delimiter_position_array, 
                                                   actual_num_time_intervals)
  
    def get_n_nodes(self):
        ''' Returns the number of nodes in an IWFM model

        Returns
        -------
        int
            number of nodes specified in the IWFM model

        See Also
        --------
        IWFMModel.get_node_coordinates : Returns the x,y coordinates of the nodes in an IWFM model
        IWFMModel.get_node_ids : Returns an array of node ids in an IWFM model
        IWFMModel.get_n_elements : Returns the number of elements in an IWFM model
        IWFMModel.get_n_subregions : Returns the number of subregions in an IWFM model
        IWFMModel.get_n_stream_nodes : Returns the number of stream nodes in an IWFM model
        IWFMModel.get_n_stream_inflows : Returns the number of stream boundary inflows specified by the user as timeseries input data
        IWFMModel.get_n_layers : Returns the number of layers in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_nodes()
        441
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNNodes'))
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize n_nodes variable
        n_nodes = ctypes.c_int(0)

        self.dll.IW_Model_GetNNodes(ctypes.byref(n_nodes),
                                    ctypes.byref(self.status))
           
        if not hasattr(self, "n_nodes"):
            self.n_nodes = n_nodes

        return self.n_nodes.value

    def get_node_coordinates(self):
        ''' Returns the x,y coordinates of the nodes in an IWFM model

        Returns
        -------
        tuple
            np.ndarray of groundwater node x-coordinates
            np.ndarray of groundwater node y-coordinates

        See Also
        --------
        IWFMModel.get_n_nodes : Returns the number of nodes in an IWFM model
        IWFMModel.get_node_ids : Returns an array of node ids in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> x, y = model.get_node_coordinates()
        >>> x
        array([1804440. , 1811001.6, 1817563.2, 1824124.8, 1830686.4, 1837248. , ..., 1902864. , 1909425.6, 1915987.2, 1922548.8, 1929110.4, 1935672. ])
        >>> y
        array([14435520. , 14435520. , 14435520. , 14435520. , 14435520. , ..., 14566752. , 14566752. , 14566752. , 14566752. , 14566752. ])
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNodeXY"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNodeXY'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # get number of nodes
        num_nodes = ctypes.c_int(self.get_n_nodes())

        # initialize output variables
        x_coordinates = (ctypes.c_double*num_nodes.value)()
        y_coordinates = (ctypes.c_double*num_nodes.value)()

        self.dll.IW_Model_GetNodeXY(ctypes.byref(num_nodes),
                                    x_coordinates,
                                    y_coordinates,
                                    ctypes.byref(self.status))

        return np.array(x_coordinates), np.array(y_coordinates)

    def get_node_ids(self):
        ''' Returns an array of node ids in an IWFM model

        Returns
        -------
        np.ndarray
            array of groundwater node ids

        See Also
        --------
        IWFMModel.get_n_nodes : Returns the number of nodes in an IWFM model
        IWFMModel.get_node_coordinates : Returns the x,y coordinates of the nodes in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_node_ids()
        array([  1,   2,   3,   4,   5, ..., 437, 438, 439, 440, 441])
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNodeIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNodeIDs'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # get number of nodes
        num_nodes = ctypes.c_int(self.get_n_nodes())

        # initialize output variables
        node_ids = (ctypes.c_int*num_nodes.value)()

        self.dll.IW_Model_GetNodeIDs(ctypes.byref(num_nodes),
                                     node_ids,
                                     ctypes.byref(self.status))

        return np.array(node_ids)

    def get_n_elements(self):
        ''' Returns the number of elements in an IWFM model

        Returns
        -------
        int
            number of elements in the IWFM model application

        See Also
        --------
        IWFMModel.get_element_ids : Returns an array of element IDs in an IWFM model
        IWFMModel.get_element_config : Returns an array of node IDs for an IWFM element
        IWFMModel.get_n_nodes : Returns the number of nodes in an IWFM model
        IWFMModel.get_n_subregions : Returns the number of subregions in an IWFM model
        IWFMModel.get_n_stream_nodes : Returns the number of stream nodes in an IWFM model
        IWFMModel.get_n_stream_inflows : Returns the number of stream boundary inflows specified by the user as timeseries input data
        IWFMModel.get_n_layers : Returns the number of layers in an IWFM model
        

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_elements()
        400
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNElements"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNElements'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize n_nodes variable
        n_elements = ctypes.c_int(0)

        self.dll.IW_Model_GetNElements(ctypes.byref(n_elements),
                                       ctypes.byref(self.status))
            
        if not hasattr(self, "n_elements"):
            self.n_elements = n_elements

        return self.n_elements.value

    def get_element_ids(self):
        ''' Returns an array of element ids in an IWFM model

        Returns
        -------
        np.ndarray
            array of element ids in an IWFM model application

        See Also
        --------
        IWFMModel.get_n_elements : Returns the number of elements in the IWFM model
        IWFMModel.get_element_config : Returns an array of node IDs for an IWFM element

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_element_ids()
        array([ 1, 2, 3, ..., 398, 399, 400])
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetElementIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetElementIDs'))
            
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # get number of elements
        num_elements = ctypes.c_int(self.get_n_elements())

        # initialize output variables
        element_ids = (ctypes.c_int*num_elements.value)()

        self.dll.IW_Model_GetElementIDs(ctypes.byref(num_elements),
                                        element_ids,
                                        ctypes.byref(self.status))

        return np.array(element_ids)

    def get_element_config(self, element_id):
        ''' Returns an array of node ids for an IWFM element.
        The node ids are provided in a counter-clockwise direction

        Parameters
        ----------
        element_id : int
            single element ID for IWFM model. Must be one of the values returned by
            get_element_ids method

        Returns
        -------
        np.ndarray
            array of node IDs for element

        Note
        ----
        In IWFM, elements can be composed of either 3 or 4 nodes. If 
        the element has 3 nodes, the fourth is returned as a 0. Nodes IDs
        must also be in counter-clockwise order.

        See Also
        --------
        IWFMModel.get_n_elements : Returns the number of elements in an IWFM model
        IWFMModel.get_element_ids : Returns an array of element IDs in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_element_config(1)
        array([ 1, 2, 23, 22])
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetElementConfigData"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetElementConfigData'))
        
        # check that element_id is an integer
        if not isinstance(element_id, (int, np.int32)):
            raise TypeError('element_id must be an integer')

        # check that element_id is a valid element_id
        element_ids = self.get_element_ids()
        if not np.any(element_ids == element_id):
            raise ValueError('element_id is not a valid element ID')

        # convert element_id to element index
        element_index = np.where(element_ids == element_id)[0][0] + 1

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # set input variables
        element_index = ctypes.c_int(element_index)
        max_nodes_per_element = ctypes.c_int(4)

        # initialize output variables
        nodes_in_element = (ctypes.c_int*max_nodes_per_element.value)()

        self.dll.IW_Model_GetElementConfigData(ctypes.byref(element_index),
                                               ctypes.byref(max_nodes_per_element),
                                               nodes_in_element,
                                               ctypes.byref(self.status))

        # convert node indices to node IDs
        node_indices = np.array(nodes_in_element)
        node_ids = self.get_node_ids()

        return node_ids[node_indices - 1]

    def get_n_subregions(self):
        ''' Returns the number of subregions in an IWFM model

        Returns
        -------
        int
            number of subregions in the IWFM model

        See Also
        --------
        IWFMModel.get_subregion_ids : Returns an array of IDs for subregions specified in an IWFM model
        IWFMModel.get_subregion_name : Returns the name corresponding to the subregion_id in an IWFM model
        IWFMModel.get_subregions_by_element : Returns an array identifying the IWFM Model elements contained within each subregion.

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_subregions()
        2
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNSubregions"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNSubregions'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
            
        # initialize n_subregions variable
        n_subregions = ctypes.c_int(0)
            
        self.dll.IW_Model_GetNSubregions(ctypes.byref(n_subregions),
                                         ctypes.byref(self.status))
        
        if not hasattr(self, "n_subregions"):
            self.n_subregions = n_subregions
            
        return self.n_subregions.value

    def get_subregion_ids(self):
        ''' Returns an array of IDs for subregions identified in an IWFM model 
        
        Returns
        -------
        np.ndarray
            array containing integer IDs for the subregions specified in the IWFM model

        Note
        ----
        The resulting integer array will have a length equal to the value returned by the get_n_subregions method

        See Also
        --------
        IWFMModel.get_n_subregions : Returns the number of subregions in an IWFM model
        IWFMModel.get_subregion_name : Returns the name corresponding to the subregion_id in an IWFM model
        IWFMModel.get_subregions_by_element ; Returns an array identifying the IWFM Model elements contained within each subregion.

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_subregion_ids()
        array([1, 2])
        >>> model.kill()
        '''
        
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetSubregionIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetSubregionIDs'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # get number of model subregions
        n_subregions = ctypes.c_int(self.get_n_subregions())

        # initialize output variables
        subregion_ids = (ctypes.c_int*n_subregions.value)()
                
        self.dll.IW_Model_GetSubregionIDs(ctypes.byref(n_subregions),
                                          subregion_ids,
                                          ctypes.byref(self.status))

        return np.array(subregion_ids)

    def get_subregion_name(self, subregion_id):
        ''' Returns the name corresponding to the subregion_id in an IWFM model 
        
        Parameters
        ----------
        subregion_id : int
            subregion identification number used to return name
            
        Returns
        -------
        str
            name of the subregion

        See Also
        --------
        IWFMModel.get_n_subregions : Returns the number of subregions in an IWFM model
        IWFMModel.get_subregion_ids : Returns an array of IDs for subregions identified in an IWFM model
        IWFMModel.get_subregions_by_element : Returns an array identifying the IWFM Model elements contained within each subregion.

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_subregion_name(1)
        'Region1 (SR1)'
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetSubregionName"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetSubregionName'))

        # check that subregion_id is an integer
        if not isinstance(subregion_id, int):
            raise TypeError('subregion_id must be an integer')

        # check that subregion_id is valid
        subregion_ids = self.get_subregion_ids()
        if subregion_id not in subregion_ids:
            subregions = ' '.join([str(val) for val in subregion_ids])
            raise ValueError('subregion_id provided is not a valid '
                             'subregion id. value provided {}. Must be '
                             'one of: {}'.format(subregion_id, subregions))

        # convert subregion_id to subregion index adding 1 to handle fortran indexing
        subregion_index = np.where(subregion_ids == subregion_id)[0][0] + 1

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # convert subregion_index to ctypes
        subregion_index = ctypes.c_int(subregion_index)

        # initialize name length as 50 characters
        length_name = ctypes.c_int(50)

        # initialize output variables
        subregion_name = ctypes.create_string_buffer(length_name.value)
        
        self.dll.IW_Model_GetSubregionName(ctypes.byref(subregion_index),
                                           ctypes.byref(length_name),
                                           subregion_name,
                                           ctypes.byref(self.status))

        return subregion_name.value.decode('utf-8')

    def get_subregions_by_element(self):
        ''' Returns an array identifying the IWFM Model elements contained within each subregion.

        Returns
        -------
        np.ndarray
            array identifying the subregion where each model element is assigned
        Note
        ----
        The resulting integer array will have a length equal to the value returned by get_n_elements method

        See Also
        --------
        IWFMModel.get_n_subregions : Returns the number of subregions in an IWFM model
        IWFMModel.get_subregion_ids : Returns an array of IDs for subregions specified in an IWFM model
        IWFMModel.get_subregion_name : Returns the name corresponding to the subregion_id in an IWFM model
        IWFMModel.get_n_elements : Returns the number of elements in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_subregions_by_element()
        array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
               2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
               2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
               2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
               2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
               2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
               2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
               2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
               2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
               2, 2, 2, 2])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetElemSubregions"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetElemSubregions'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # get number of elements in model
        n_elements = ctypes.c_int(self.get_n_elements())

        # initialize output variables
        element_subregions = (ctypes.c_int*n_elements.value)()

        self.dll.IW_Model_GetElemSubregions(ctypes.byref(n_elements),
                                   element_subregions,
                                   ctypes.byref(self.status))

        # convert subregion indices to subregion IDs
        subregion_index_by_element = np.array(element_subregions)
        subregion_ids = self.get_subregion_ids()

        return subregion_ids[subregion_index_by_element - 1]

    def get_n_stream_nodes(self):
        ''' Returns the number of stream nodes in an IWFM model

        Returns
        -------
        int
            number of stream nodes in the IWFM model

        See Also
        --------
        IWFMModel.get_stream_node_ids : Returns an array of stream node IDs from an IWFM model application
        IWFMModel.get_n_stream_nodes_upstream_of_stream_node : Returns the number of stream nodes immediately upstream of the provided stream node id
        IWFMModel.get_stream_nodes_upstream_of_stream_node : Returns an array of the stream node ids immediately upstream of the provided stream node id
        IWFMModel.get_n_nodes : Returns the number of nodes in an IWFM model
        IWFMModel.get_n_subregions : Returns the number of subregions in an IWFM model
        IWFMModel.get_n_stream_inflows : Returns the number of stream boundary inflows specified by the user as timeseries input data

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_stream_nodes()
        23
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNStrmNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNStrmNodes'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
            
        # initialize n_stream_nodes variable
        n_stream_nodes = ctypes.c_int(0)
            
        self.dll.IW_Model_GetNStrmNodes(ctypes.byref(n_stream_nodes),
                                        ctypes.byref(self.status))
        
        if not hasattr(self, "n_stream_nodes"):
            self.n_stream_nodes = n_stream_nodes
            
        return self.n_stream_nodes.value

    def get_stream_node_ids(self):
        ''' Returns an array of stream node IDs from the IWFM model application
        
        Returns
        -------
        np.ndarray
            array of stream node IDs from the IWFM model
            
        Note
        ----
        The resulting integer array will have a length equal to the value returned by the get_n_stream_nodes method

        See Also
        --------
        IWFMModel.get_n_stream_nodes : Reutrns the number of stream nodes in an IWFM model
        IWFMModel.get_n_stream_nodes_upstream_of_stream_node : Returns the number of stream nodes immediately upstream of the provided stream node id
        IWFMModel.get_stream_nodes_upstream_of_stream_node : Returns an array of the stream node ids immediately upstream of the provided stream node id

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stream_node_ids()
        array([ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17,
               18, 19, 20, 21, 22, 23])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmNodeIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetStrmNodeIDs'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # get number of stream nodes
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # initialize output variables
        stream_node_ids = (ctypes.c_int*n_stream_nodes.value)()

        self.dll.IW_Model_GetStrmNodeIDs(ctypes.byref(n_stream_nodes),
                                         stream_node_ids,
                                         ctypes.byref(self.status))

        return np.array(stream_node_ids, dtype=np.int32)

    def get_n_stream_nodes_upstream_of_stream_node(self, stream_node_id):
        ''' Returns the number of stream nodes immediately upstream of
        the provided stream node id
        
        Parameters
        ----------
        stream_node_id : int, np.int32
            stream node id used to determine number of stream nodes upstream
            
        Returns
        -------
        int
            number of stream nodes immediately upstream of given stream node

        Note
        ----
        Most stream nodes will only have 1 stream node immediately upstream.
        The upstream-most stream node has no upstream stream nodes and will return 0.
        Stream nodes at a confluence of two stream reaches will return a value 2

        See Also
        --------
        IWFMModel.get_n_stream_nodes : Returns the number of stream nodes in an IWFM model
        IWFMModel.get_stream_node_ids : Returns an array of stream node IDs from an IWFM model application
        IWFMModel.get_stream_nodes_upstream_of_stream_node : Returns an array of the stream node ids immediately upstream of the provided stream node id

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_stream_nodes_upstream_of_stream_node(11)
        0
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmNUpstrmNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetStrmNUpstrmNodes'))

        # check that stream_node_id is an integer
        if not isinstance(stream_node_id, (int, np.int32)):
            raise TypeError('stream_node_id must be an integer')

        # check that stream_node_id is a valid stream_node_id
        stream_node_ids = self.get_stream_node_ids()
        if not np.any(stream_node_ids == stream_node_id):
            raise ValueError("stream_node_id '{}' is not a valid Stream Node ID".format(stream_node_id))

        # convert stream_node_id to stream node index
        # add 1 to convert index from python index to fortran index
        stream_node_index = np.where(stream_node_ids == stream_node_id)[0][0] + 1

        # set input variables
        stream_node_index = ctypes.c_int(stream_node_index)
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        n_upstream_stream_nodes = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmNUpstrmNodes(ctypes.byref(stream_node_index),
                                              ctypes.byref(n_upstream_stream_nodes),
                                              ctypes.byref(self.status))

        return n_upstream_stream_nodes.value

    def get_stream_nodes_upstream_of_stream_node(self, stream_node_id):
        ''' Returns an array of the stream node ids immediately upstream
        of the provided stream node id
        
        Parameters
        ----------
        stream_node_id : int
            stream node id used to determine upstream stream nodes 
            
        Returns
        -------
        np.ndarray
            integer array of stream node ids upstream of the provided stream node id

        Note
        ----
        stream node ids returned are for the stream node immediately upstream of the specified
        stream node id only. if stream node specified is the most upstream node, None is returned

        See Also
        --------
        IWFMModel.get_n_stream_nodes_upstream_of_stream_node : Returns the number of stream nodes immediately upstream of the provided stream node id
        IWFMModel.get_n_stream_nodes : Returns the number of stream nodes in an IWFM model
        IWFMModel.get_stream_node_ids : Returns an array of stream node IDs from the IWFM model application

        Examples
        --------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> print(model.get_stream_nodes_upstream_of_stream_node(11))
        None
        >>> model.kill()

        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stream_nodes_upstream_of_stream_node(2)
        array([1])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmUpstrmNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetStrmUpstrmNodes'))

        # check that stream_node_id is an integer
        if not isinstance(stream_node_id, int):
            raise TypeError('stream_node_id must be an integer')

        # check that stream_node_id is a valid stream_node_id
        stream_node_ids = self.get_stream_node_ids()
        if not np.any(stream_node_ids == stream_node_id):
            raise ValueError('stream_node_id is not a valid Stream Node ID')

        # convert stream_node_id to stream node index
        # add 1 to convert between python indexing and fortran indexing
        stream_node_index = np.where(stream_node_ids == stream_node_id)[0][0] + 1

        # set input variables
        n_upstream_stream_nodes = ctypes.c_int(self.get_n_stream_nodes_upstream_of_stream_node(stream_node_id))
        
        # return None if no upstream stream nodes
        if n_upstream_stream_nodes.value == 0:
            return

        stream_node_index = ctypes.c_int(stream_node_index)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        upstream_nodes = (ctypes.c_int*n_upstream_stream_nodes.value)()

        self.dll.IW_Model_GetStrmUpstrmNodes(ctypes.byref(stream_node_index),
                                             ctypes.byref(n_upstream_stream_nodes),
                                             upstream_nodes,
                                             ctypes.byref(self.status))

        # convert stream node indices to stream node ids
        upstream_node_indices = np.array(upstream_nodes)

        return stream_node_ids[upstream_node_indices - 1] 

    def get_stream_bottom_elevations(self):
        ''' Returns the stream channel bottom elevation at each stream node
        
        Returns
        -------
        np.ndarray
            array of floats with the stream channel elevation for each stream node

        See Also
        --------
        IWFMModel.get_n_stream_nodes : Returns the number of stream nodes in an IWFM model
        IWFMModel.get_stream_node_ids : Returns an array of stream node IDs from the IWFM model application
        IWFMModel.get_n_rating_table_points : Returns the number of data points in the stream flow rating table for a stream node
        IWFMModel.get_stream_rating_table : Returns the stream rating table for a specified stream node

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stream_bottom_elevations()
        array([300., 298., 296., 294., 292., 290., 288., 286., 284., 282., 282.,
               280., 278., 276., 274., 272., 272., 270., 268., 266., 264., 262.,
               260.])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmBottomElevs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetStrmBottomElevs'))

        # set input variables
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # reset_instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        stream_bottom_elevations = (ctypes.c_double*n_stream_nodes.value)()

        self.dll.IW_Model_GetStrmBottomElevs(ctypes.byref(n_stream_nodes),
                                             stream_bottom_elevations,
                                             ctypes.byref(self.status))
        
        return np.array(stream_bottom_elevations)

    def get_n_rating_table_points(self, stream_node_id):
        ''' Returns the number of data points in the stream flow rating 
        table for a stream node

        Parameters
        ----------
        stream_node_id : int
            stream node id used to determine number of data points in 
            the rating table

        Returns
        -------
        int
            number of data points in the stream flow rating table

        See Also
        --------
        IWFMModel.get_stream_rating_table : Returns the stream rating table for a specified stream node
        IWFMModel.get_n_stream_nodes : Returns the number of stream nodes in an IWFM model
        IWFMModel.get_stream_node_ids : Returns an array of stream node IDs from the IWFM model application
        IWFMModel.get_stream_bottom_elevations : Returns the stream channel bottom elevation at each stream node

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_rating_table_points(1)
        5
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetNStrmRatingTablePoints"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNStrmRatingTablePoints'))

        # check that stream_node_id is an integer
        if not isinstance(stream_node_id, int):
            raise TypeError('stream_node_id must be an integer')

        # check that stream_node_id is a valid stream_node_id
        stream_node_ids = self.get_stream_node_ids()
        if not np.any(stream_node_ids == stream_node_id):
            raise ValueError('stream_node_id is not a valid Stream Node ID')

        # convert stream_node_id to stream node index
        # add 1 to convert python index to fortran index
        stream_node_index = np.where(stream_node_ids == stream_node_id)[0][0] + 1

        # set input variables convert to ctypes, if not already
        stream_node_index = ctypes.c_int(stream_node_index)

        # reset instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        n_rating_table_points = ctypes.c_int(0)

        self.dll.IW_Model_GetNStrmRatingTablePoints(ctypes.byref(stream_node_index),
                                                    ctypes.byref(n_rating_table_points),
                                                    ctypes.byref(self.status))

        return n_rating_table_points.value


    def get_stream_rating_table(self, stream_node_id):
        ''' Returns the stream rating table for a specified stream node 
        
        Parameters
        ----------
        stream_node_id : int
            stream node id used to return the rating table
        
        Returns
        -------
        tuple (length=2)
            np.ndarrays representing stage and flow, respectively

        See Also
        --------
        IWFMModel.get_n_rating_table_points : Returns the number of data points in the stream flow rating table for a stream node
        IWFMModel.get_n_stream_nodes : Returns the number of stream nodes in an IWFM model
        IWFMModel.get_stream_node_ids : Returns an array of stream node IDs from the IWFM model application
        IWFMModel.get_stream_bottom_elevations : Returns the stream channel bottom elevation at each stream node

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> stage, flow = model.get_stream_rating_table(1)
        >>> stage
        array([ 0.,  2.,  5., 15., 25.])
        >>> flow
        array([0.00000000e+00, 6.34988160e+07, 2.85058656e+08, 1.64450304e+09,
        3.59151408e+09])        
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmRatingTable"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetStrmRatingTable'))

        # check that stream_node_id is an integer
        if not isinstance(stream_node_id, int):
            raise TypeError('stream_node_id must be an integer')

        # check that stream_node_id is a valid stream_node_id
        stream_node_ids = self.get_stream_node_ids()
        if not np.any(stream_node_ids == stream_node_id):
            raise ValueError('stream_node_id is not a valid Stream Node ID')

        # convert stream_node_id to stream node index
        # add 1 to convert between python index and fortan index
        stream_node_index = np.where(stream_node_ids == stream_node_id)[0][0] + 1

        # set input variables
        stream_node_index = ctypes.c_int(stream_node_index)
        n_rating_table_points =ctypes.c_int(self.get_n_rating_table_points(stream_node_id))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        stage = (ctypes.c_double*n_rating_table_points.value)()
        flow = (ctypes.c_double*n_rating_table_points.value)()

        self.dll.IW_Model_GetStrmRatingTable(ctypes.byref(stream_node_index), 
                                             ctypes.byref(n_rating_table_points),
                                             stage,
                                             flow,
                                             ctypes.byref(self.status))

        return np.array(stage), np.array(flow)

    def get_n_stream_inflows(self):
        ''' Returns the number of stream boundary inflows specified by the 
        user as timeseries input data

        Returns
        -------
        int
            number of stream boundary inflows

        See Also
        --------
        IWFMModel.get_stream_inflow_nodes : Returns the stream nodes indices that receive boundary inflows specified by the user as timeseries input data
        IWFMModel.get_stream_inflow_ids : Returns the identification numbers for the stream boundary inflows specified by the user as timeseries input data

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_stream_inflows()
        1
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmNInflows"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmNInflows"))
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)
        
        # initialize output variables
        n_stream_inflows = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmNInflows(ctypes.byref(n_stream_inflows),
                                          ctypes.byref(self.status))

        return n_stream_inflows.value

    def get_stream_inflow_nodes(self):
        ''' Returns the stream node indices that receive boundary 
        inflows specified by the user as timeseries input data 
        
        Returns
        -------
        np.ndarray
            integer array of stream node IDs where inflows occur

        See Also
        --------
        IWFMModel.get_n_stream_inflows : Returns the number of stream boundary inflows specified by the user as timeseries input data
        IWFMModel.get_stream_inflow_ids : Returns the identification numbers for the stream boundary inflows specified by the user as timeseries input data

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stream_inflow_nodes()
        array([1])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmInflowNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmInflowNodes"))
        
        # get number of stream inflow nodes
        n_stream_inflows = ctypes.c_int(self.get_n_stream_inflows())

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        stream_inflow_nodes = (ctypes.c_int*n_stream_inflows.value)()

        self.dll.IW_Model_GetStrmInflowNodes(ctypes.byref(n_stream_inflows),
                                             stream_inflow_nodes,
                                             ctypes.byref(self.status))

        # convert stream node indices to stream node IDs
        stream_node_ids = self.get_stream_node_ids()
        stream_inflow_node_indices = np.array(stream_inflow_nodes)

        return stream_node_ids[stream_inflow_node_indices - 1]

    def get_stream_inflow_ids(self):
        ''' Returns the identification numbers for the stream boundary 
        inflows specified by the user as timeseries input data 
        
        Returns
        -------
        np.ndarray
            integer array of stream inflow IDs

        See Also
        --------
        IWFMModel.get_n_stream_inflows : Returns the number of stream boundary inflows specified by the user as timeseries input data
        IWFMModel.get_stream_inflow_nodes : Returns the stream node indices that receive boundary inflows specified by the user as timeseries input data

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stream_inflow_ids()
        array([1])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmInflowIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmInflowIDs"))
        
        # get number of stream inflow nodes
        n_stream_inflows = ctypes.c_int(self.get_n_stream_inflows())

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        stream_inflow_ids = (ctypes.c_int*n_stream_inflows.value)()

        self.dll.IW_Model_GetStrmInflowIDs(ctypes.byref(n_stream_inflows),
                                             stream_inflow_ids,
                                             ctypes.byref(self.status))

        return np.array(stream_inflow_ids)

    def get_stream_inflows_at_some_locations(self, 
                                             stream_inflow_locations='all', 
                                             inflow_conversion_factor=1.0):
        ''' Returns stream boundary inflows at a specified set of inflow
        locations listed by their indices for the current simulation timestep
        
        Parameters
        ----------
        stream_inflow_locations : int, list, tuple, np.ndarray, or str='all', default='all'
            one or more stream inflow ids used to return flows

        inflow_conversion_factor : float, default=1.0
            conversion factor for stream boundary inflows from the 
            simulation units of volume to a desired unit of volume

        Returns
        -------
        np.ndarray
            array of inflows for the inflow locations at the current 
            simulation time step

        Note
        ----
        This method is designed for use when is_for_inquiry=0 to return
        stream inflows at the current timestep during a simulation.

        See Also
        --------
        IWFMModel.get_stream_flow_at_location : Returns stream flow at a stream node for the current time step in a simulation
        IWFMModel.get_stream_flows : Returns stream flows at every stream node for the current timestep
        IWFMModel.get_stream_stages : Returns stream stages at every stream node for the current timestep

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file, is_for_inquiry=0)
        >>> while not model.is_end_of_simulation():
        ...     # advance the simulation time one time step forward
        ...     model.advance_time()
        ...
        ...     # read all time series data from input files
        ...     model.read_timeseries_data()
        ...
        ...     # Simulate the hydrologic process for the timestep
        ...     model.simulate_for_one_timestep()
        ...
        ...     # print stream inflows
        ...     print(model.get_stream_inflows_at_some_locations(1)[0])
        ...
        ...     # print the results to the user-specified output files
        ...     model.print_results()
        ...
        ...     # advance the state of the hydrologic system in time
        ...     model.advance_state()
        .
        .
        .
        86400000.
        *   TIME STEP 2 AT 10/02/1990_24:00
        86400000.
        *   TIME STEP 3 AT 10/03/1990_24:00
        86400000.
        *   TIME STEP 4 AT 10/04/1990_24:00
        86400000.
        .
        .
        .
        *   TIME STEP 3652 AT 09/29/2000_24:00
        86400000.
        *   TIME STEP 3653 AT 09/30/2000_24:00
        86400000.
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmInflows_AtSomeInflows"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmInflows_AtSomeInflows"))

        # get possible stream inflow locations
        stream_inflow_ids = self.get_stream_inflow_ids()

        if isinstance(stream_inflow_locations, str):
            if stream_inflow_locations.lower() == 'all':
                stream_inflow_locations = stream_inflow_ids
            else:
                raise ValueError('if stream_nodes is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(stream_inflow_locations, int):
            stream_inflow_locations = np.array([stream_inflow_locations])
        
        # if list or tuple convert to np.ndarray
        if isinstance(stream_inflow_locations, (list, tuple)):
            stream_inflow_locations = np.array(stream_inflow_locations)

        # if stream_inflow_locations were provided as an int, list, tuple, 'all', 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(stream_inflow_locations, np.ndarray):
            raise TypeError('stream_inflow_locations must be an int, list, or np.ndarray')

        # check if all of the provided stream_inflow_locations are valid
        if not np.all(np.isin(stream_inflow_locations, stream_inflow_ids)):
            raise ValueError('One or more stream inflow locations are invalid')

        # convert stream_inflow_locations to stream inflow indices
        # add 1 to convert between python indices and fortran indices
        stream_inflow_indices = np.array([np.where(stream_inflow_ids == item)[0][0] for item in stream_inflow_locations]) + 1
        
        # initialize input variables
        n_stream_inflow_locations = ctypes.c_int(len(stream_inflow_locations))
        stream_inflow_indices = (ctypes.c_int*n_stream_inflow_locations.value)(*stream_inflow_indices)
        inflow_conversion_factor = ctypes.c_double(inflow_conversion_factor)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        inflows = (ctypes.c_double*n_stream_inflow_locations.value)()
                
        self.dll.IW_Model_GetStrmInflows_AtSomeInflows(ctypes.byref(n_stream_inflow_locations),
                                                       stream_inflow_indices,
                                                       ctypes.byref(inflow_conversion_factor),
                                                       inflows,
                                                       ctypes.byref(self.status))

        return np.array(inflows)

    def get_stream_flow_at_location(self, stream_node_id, flow_conversion_factor=1.0):
        ''' Returns stream flow at a stream node for the current time
        step in a simulation 

        Parameters
        ----------
        stream_node_id : int
            stream node ID where flow is retrieved

        flow_conversion_factor : float, default=1.0
            conversion factor for stream flows from the 
            simulation units of volume to a desired unit of volume

        Returns
        -------
        float
            stream flow at specified stream node
        
        Note
        ----
        This method is designed for use when is_for_inquiry=0 to return
        a stream flow at the current timestep during a simulation.

        See Also
        --------
        IWFMModel.get_stream_inflows_at_some_locations : Returns stream boundary inflows at a specified set of inflow locations listed by their indices for the current simulation timestep
        IWFMModel.get_stream_flows : Returns stream flows at every stream node for the current timestep
        IWFMModel.get_stream_stages : Returns stream stages at every stream node for the current timestep

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file, is_for_inquiry=0)
        >>> while not model.is_end_of_simulation():
        ...     # advance the simulation time one time step forward
        ...     model.advance_time()
        ...
        ...     # read all time series data from input files
        ...     model.read_timeseries_data()
        ...
        ...     # Simulate the hydrologic process for the timestep
        ...     model.simulate_for_one_timestep()
        ...
        ...     # print stream flow at stream node ID = 1
        ...     print(model.get_stream_flow_at_location(1))
        ...
        ...     # print the results to the user-specified output files
        ...     model.print_results()
        ...
        ...     # advance the state of the hydrologic system in time
        ...     model.advance_state()
        .
        .
        .
        75741791.53232515
        *   TIME STEP 2 AT 10/02/1990_24:00
        75741791.53232515
        *   TIME STEP 3 AT 10/03/1990_24:00
        75741791.53232515
        *   TIME STEP 4 AT 10/04/1990_24:00
        75741791.53232515
        .
        .
        .
        *   TIME STEP 3652 AT 09/29/2000_24:00
        85301157.65510693
        *   TIME STEP 3653 AT 09/30/2000_24:00
        85301292.67626143
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmFlow"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmFlow"))
        
        # check that stream_node_id is a valid stream_node_id
        stream_node_ids = self.get_stream_node_ids()
        if not np.any(stream_node_ids == stream_node_id):
            raise ValueError('stream_node_id is not a valid Stream Node ID')

        # convert stream_node_id to stream node index
        # add 1 to convert between python index and fortan index
        stream_node_index = np.where(stream_node_ids == stream_node_id)[0][0] + 1

        # convert input variables to ctypes
        stream_node_index = ctypes.c_int(stream_node_index)
        flow_conversion_factor = ctypes.c_double(flow_conversion_factor)

        # initialize output variables
        stream_flow = ctypes.c_double(0)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmFlow(ctypes.byref(stream_node_index),
                                      ctypes.byref(flow_conversion_factor),
                                      ctypes.byref(stream_flow),
                                      ctypes.byref(self.status))

        return stream_flow.value

    def get_stream_flows(self, flow_conversion_factor=1.0):
        ''' Returns stream flows at every stream node for the current timestep 
        
        Parameters
        ----------
        flow_conversion_factor : float, default=1.0
            conversion factor for stream flows from the 
            simulation units of volume to a desired unit of volume

        Returns
        -------
        np.ndarray
            flows for all stream nodes for the current simulation timestep

        Note
        ----
        This method is designed for use when is_for_inquiry=0 to return
        stream flows at the current timestep during a simulation.

        See Also
        --------
        IWFMModel.get_stream_inflows_at_some_locations : Returns stream boundary inflows at a specified set of inflow locations listed by their indices for the current simulation timestep
        IWFMModel.get_stream_flow_at_location : Returns stream flow at a stream node for the current time step in a simulation
        IWFMModel.get_stream_stages : Returns stream stages at every stream node for the current timestep

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file, is_for_inquiry=0)
        >>> while not model.is_end_of_simulation():
        ...     # advance the simulation time one time step forward
        ...     model.advance_time()
        ...
        ...     # read all time series data from input files
        ...     model.read_timeseries_data()
        ...
        ...     # Simulate the hydrologic process for the timestep
        ...     model.simulate_for_one_timestep()
        ...
        ...     # get stream flows
        ...     stream_flows = model.get_stream_flows()
        ...     stream_node_ids = model.get_stream_node_ids()
        ...
        ...     # print the results to the user-specified output files
        ...     model.print_results()
        ...
        ...     # advance the state of the hydrologic system in time
        ...     model.advance_state()
        >>> for i, flow in enumerate(stream_flows):
        ...     print(stream_node_ids[i], flow)
        *   TIME STEP 3653 AT 09/30/2000_24:00
        1 85301292.67626143
        2 83142941.70620254
        3 81028792.9071748
        4 78985517.65754062
        5 77081104.67763746
        6 75724877.72101441
        7 74440170.86435351
        8 73367874.87547392
        9 71735544.16731748
        10 70995694.52663273
        11 53285997.91790043
        12 44.84964866936207
        13 0.0
        14 0.0
        15 0.0
        16 0.0
        17 0.0
        18 2553191.7510338724
        19 1948997.4229038805
        20 1487781.3046951443
        21 2345774.2345003784
        22 1599258.8286072314
        23 2495579.2758224607
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmFlows"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmFlows"))

        # get number of stream nodes in the model
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # convert unit conversion factor to ctypes
        flow_conversion_factor = ctypes.c_double(flow_conversion_factor)

        # initialize output variables
        stream_flows = (ctypes.c_double*n_stream_nodes.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmFlows(ctypes.byref(n_stream_nodes),
                                 ctypes.byref(flow_conversion_factor),
                                 stream_flows,
                                 ctypes.byref(self.status))

        return np.array(stream_flows)

    def get_stream_stages(self, stage_conversion_factor=1.0):
        ''' Returns stream stages at every stream node for the current timestep
        
        Parameters
        ----------
        stage_conversion_factor : float
            conversion factor for stream stages from the 
            simulation units of length to a desired unit of length

        Returns
        -------
        np.ndarray
            stages for all stream nodes for the current simulation timestep

        Note
        ----
        This method is designed for use when is_for_inquiry=0 to return
        stream stages at the current timestep during a simulation.

        See Also
        --------
        IWFMModel.get_stream_inflows_at_some_locations : Returns stream boundary inflows at a specified set of inflow locations listed by their indices for the current simulation timestep
        IWFMModel.get_stream_flow_at_location : Returns stream flow at a stream node for the current time step in a simulation
        IWFMModel.get_stream_flows : Returns stream flows at every stream node for the current timestep

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file, is_for_inquiry=0)
        >>> while not model.is_end_of_simulation():
        ...     # advance the simulation time one time step forward
        ...     model.advance_time()
        ...
        ...     # read all time series data from input files
        ...     model.read_timeseries_data()
        ...
        ...     # Simulate the hydrologic process for the timestep
        ...     model.simulate_for_one_timestep()
        ...
        ...     # get stream flows
        ...     stream_flows = model.get_stream_stages()
        ...     stream_node_ids = model.get_stream_node_ids()
        ...
        ...     # print the results to the user-specified output files
        ...     model.print_results()
        ...
        ...     # advance the state of the hydrologic system in time
        ...     model.advance_state()
        >>> for i, flow in enumerate(stream_flows):
        ...     print(stream_node_ids[i], flow)
        *   TIME STEP 3653 AT 09/30/2000_24:00
        1 2.2952133835661925
        2 2.265988534377925
        3 2.23736219849917
        4 2.209695515995236
        5 2.183909078616921
        6 2.1655452773528054
        7 2.148149883990982
        8 2.133630610251487
        9 2.1115282647882054
        10 2.1015104342912423
        11 1.6783304406148432
        12 1.4126136989034421e-06
        13 0.0
        14 0.0
        15 0.0
        16 0.0
        17 0.0
        18 0.08041698765009642
        19 0.061386890202925315
        20 0.046860127429624754
        21 0.07388403067233185
        22 0.050371296013054234
        23 0.07860238766727434
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmStages"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmStages"))

        # get number of stream nodes in the model
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # convert unit conversion factor to ctypes
        stage_conversion_factor = ctypes.c_double(stage_conversion_factor)

        # initialize output variables
        stream_stages = (ctypes.c_double*n_stream_nodes.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmStages(ctypes.byref(n_stream_nodes),
                                        ctypes.byref(stage_conversion_factor),
                                        stream_stages,
                                        ctypes.byref(self.status))

        return np.array(stream_stages)

    def get_stream_tributary_inflows(self, inflow_conversion_factor=1.0):
        ''' Returns small watershed inflows at every stream node for the current timestep
        
        Parameters
        ----------
        inflow_conversion_factor : float
            conversion factor for small watershed flows from the 
            simulation units of volume to a desired unit of volume

        Returns
        -------
        np.ndarray
            inflows from small watersheds for all stream nodes for the
            current simulation timestep

        Note
        ----
        This method is designed for use when is_for_inquiry=0 to return
        small watershed inflows at the current timestep during a simulation.

        stream nodes without a small watershed draining to it will be 0

        See Also
        --------
        IWFMModel.get_stream_rainfall_runoff : Returns rainfall runoff at every stream node for the current timestep
        IWFMModel.get_stream_return_flows : Returns agricultural and urban return flows at every stream node for the current timestep
        IWFMModel.get_stream_tile_drain_flows : Returns tile drain flows into every stream node for the current timestep
        IWFMModel.get_stream_riparian_evapotranspiration : Returns riparian evapotranspiration from every stream node for the current timestep
        IWFMModel.get_stream_gain_from_groundwater : Returns gain from groundwater for every stream node for the current timestep
        IWFMModel.get_stream_gain_from_lakes : Returns gain from lakes for every stream node for the current timestep
        IWFMModel.get_net_bypass_inflows : Returns net bypass inflows for every stream node for the current timestep
        IWFMModel.get_actual_stream_diversions_at_some_locations : Returns actual diversion amounts for a list of diversions during a model simulation
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmTributaryInflows"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmTributaryInflows"))

        # get number of stream nodes in the model
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # convert unit conversion factor to ctypes
        inflow_conversion_factor = ctypes.c_double(inflow_conversion_factor)

        # initialize output variables
        small_watershed_inflows = (ctypes.c_double*n_stream_nodes.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmTributaryInflows(ctypes.byref(n_stream_nodes),
                                                  ctypes.byref(inflow_conversion_factor),
                                                  small_watershed_inflows,
                                                  ctypes.byref(self.status))

        return np.array(small_watershed_inflows)

    def get_stream_rainfall_runoff(self, runoff_conversion_factor=1.0):
        ''' Returns rainfall runoff at every stream node for the current timestep
        
        Parameters
        ----------
        runoff_conversion_factor : float
            conversion factor for inflows due to rainfall-runoff from 
            the simulation units of volume to a desired unit of volume

        Returns
        -------
        np.ndarray
            inflows from rainfall-runoff for all stream nodes for the
            current simulation timestep

        Note
        ----
        This method is designed for use when is_for_inquiry=0 to return
        inflows from rainfall-runoff at the current timestep during a simulation.

        stream nodes without rainfall-runoff draining to it will be 0
        
        See Also
        --------
        IWFMModel.get_stream_tributary_inflows : Returns small watershed inflows at every stream node for the current timestep
        IWFMModel.get_stream_return_flows : Returns agricultural and urban return flows at every stream node for the current timestep
        IWFMModel.get_stream_tile_drain_flows : Returns tile drain flows into every stream node for the current timestep
        IWFMModel.get_stream_riparian_evapotranspiration : Returns riparian evapotranspiration from every stream node for the current timestep
        IWFMModel.get_stream_gain_from_groundwater : Returns gain from groundwater for every stream node for the current timestep
        IWFMModel.get_stream_gain_from_lakes : Returns gain from lakes for every stream node for the current timestep
        IWFMModel.get_net_bypass_inflows : Returns net bypass inflows for every stream node for the current timestep
        IWFMModel.get_actual_stream_diversions_at_some_locations : Returns actual diversion amounts for a list of diversions during a model simulation
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmRainfallRunoff"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmRainfallRunoff"))

        # get number of stream nodes in the model
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # convert unit conversion factor to ctypes
        runoff_conversion_factor = ctypes.c_double(runoff_conversion_factor)

        # initialize output variables
        rainfall_runoff_inflows = (ctypes.c_double*n_stream_nodes.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmRainfallRunoff(ctypes.byref(n_stream_nodes),
                                                ctypes.byref(runoff_conversion_factor),
                                                rainfall_runoff_inflows,
                                                ctypes.byref(self.status))

        return np.array(rainfall_runoff_inflows)

    def get_stream_return_flows(self, return_flow_conversion_factor=1.0):
        ''' Returns agricultural and urban return flows at every stream
        node for the current timestep
        
        Parameters
        ----------
        return_flow_conversion_factor : float
            conversion factor for return flows from 
            the simulation units of volume to a desired unit of volume

        Returns
        -------
        np.ndarray
            return flows for all stream nodes for the
            current simulation timestep

        Note
        ----
        This method is designed for use when is_for_inquiry=0 to return
        return flows at the current timestep during a simulation.

        stream nodes without return flows will be 0
        
        See Also
        --------
        IWFMModel.get_stream_tributary_inflows : Returns small watershed inflows at every stream node for the current timestep
        IWFMModel.get_stream_rainfall_runoff : Returns rainfall runoff at every stream node for the current timestep
        IWFMModel.get_stream_tile_drain_flows : Returns tile drain flows into every stream node for the current timestep
        IWFMModel.get_stream_riparian_evapotranspiration : Returns riparian evapotranspiration from every stream node for the current timestep
        IWFMModel.get_stream_gain_from_groundwater : Returns gain from groundwater for every stream node for the current timestep
        IWFMModel.get_stream_gain_from_lakes : Returns gain from lakes for every stream node for the current timestep
        IWFMModel.get_net_bypass_inflows : Returns net bypass inflows for every stream node for the current timestep
        IWFMModel.get_actual_stream_diversions_at_some_locations : Returns actual diversion amounts for a list of diversions during a model simulation
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmReturnFlows"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmReturnFlows"))

        # get number of stream nodes in the model
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # convert unit conversion factor to ctypes
        return_flow_conversion_factor = ctypes.c_double(return_flow_conversion_factor)

        # initialize output variables
        return_flows = (ctypes.c_double*n_stream_nodes.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmReturnFlows(ctypes.byref(n_stream_nodes),
                                             ctypes.byref(return_flow_conversion_factor),
                                             return_flows,
                                             ctypes.byref(self.status))

        return np.array(return_flows)

    def get_stream_tile_drain_flows(self, tile_drain_conversion_factor=1.0):
        ''' Returns tile drain flows into every stream node for the current timestep
        
        Parameters
        ----------
        tile_drain_conversion_factor : float
            conversion factor for tile drain flows from 
            the simulation units of volume to a desired unit of volume

        Returns
        -------
        np.ndarray
            tile drain flows for all stream nodes for the current 
            simulation timestep

        Note
        ----
        This method is designed for use when is_for_inquiry=0 to return
        tile drain flows at the current timestep during a simulation.

        stream nodes without tile drain flows will be 0
        
        See Also
        --------
        IWFMModel.get_stream_tributary_inflows : Returns small watershed inflows at every stream node for the current timestep
        IWFMModel.get_stream_rainfall_runoff : Returns rainfall runoff at every stream node for the current timestep
        IWFMModel.get_stream_return_flows : Returns agricultural and urban return flows at every stream node for the current timestep
        IWFMModel.get_stream_riparian_evapotranspiration : Returns riparian evapotranspiration from every stream node for the current timestep
        IWFMModel.get_stream_gain_from_groundwater : Returns gain from groundwater for every stream node for the current timestep
        IWFMModel.get_stream_gain_from_lakes : Returns gain from lakes for every stream node for the current timestep
        IWFMModel.get_net_bypass_inflows : Returns net bypass inflows for every stream node for the current timestep
        IWFMModel.get_actual_stream_diversions_at_some_locations : Returns actual diversion amounts for a list of diversions during a model simulation
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmTileDrains"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmTileDrains"))

        # get number of stream nodes in the model
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # convert unit conversion factor to ctypes
        tile_drain_conversion_factor = ctypes.c_double(tile_drain_conversion_factor)

        # initialize output variables
        tile_drain_flows = (ctypes.c_double*n_stream_nodes.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmTileDrains(ctypes.byref(n_stream_nodes),
                                             ctypes.byref(tile_drain_conversion_factor),
                                             tile_drain_flows,
                                             ctypes.byref(self.status))

        return np.array(tile_drain_flows)

    def get_stream_riparian_evapotranspiration(self, evapotranspiration_conversion_factor=1.0):
        ''' Returns riparian evapotranspiration from every stream node for the current timestep
        
        Parameters
        ----------
        evapotranspiration_conversion_factor : float
            conversion factor for riparian evapotranspiration from 
            the simulation units of volume to a desired unit of volume

        Returns
        -------
        np.ndarray
            riparian evapotranspiration for all stream nodes for the current 
            simulation timestep

        Note
        ----
        This method is designed for use when is_for_inquiry=0 to return
        riparian evapotranspiration at the current timestep during a 
        simulation.

        stream nodes without riparian evapotranspiration will be 0
        
        See Also
        --------
        IWFMModel.get_stream_tributary_inflows : Returns small watershed inflows at every stream node for the current timestep
        IWFMModel.get_stream_rainfall_runoff : Returns rainfall runoff at every stream node for the current timestep
        IWFMModel.get_stream_return_flows : Returns agricultural and urban return flows at every stream node for the current timestep
        IWFMModel.get_stream_tile_drain_flows : Returns tile drain flows into every stream node for the current timestep
        IWFMModel.get_stream_gain_from_groundwater : Returns gain from groundwater for every stream node for the current timestep
        IWFMModel.get_stream_gain_from_lakes : Returns gain from lakes for every stream node for the current timestep
        IWFMModel.get_net_bypass_inflows : Returns net bypass inflows for every stream node for the current timestep
        IWFMModel.get_actual_stream_diversions_at_some_locations : Returns actual diversion amounts for a list of diversions during a model simulation
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmRiparianETs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmRiparianETs"))

        # get number of stream nodes in the model
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # convert unit conversion factor to ctypes
        evapotranspiration_conversion_factor = ctypes.c_double(evapotranspiration_conversion_factor)

        # initialize output variables
        riparian_evapotranspiration = (ctypes.c_double*n_stream_nodes.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmRiparianETs(ctypes.byref(n_stream_nodes),
                                             ctypes.byref(evapotranspiration_conversion_factor),
                                             riparian_evapotranspiration,
                                             ctypes.byref(self.status))

        return np.array(riparian_evapotranspiration)

    def get_stream_gain_from_groundwater(self, stream_gain_conversion_factor=1.0):
        ''' Returns gain from groundwater for every stream node for the current timestep
        
        Parameters
        ----------
        stream_gain_conversion_factor : float
            conversion factor for gain from groundwater from 
            the simulation units of volume to a desired unit of volume

        Returns
        -------
        np.ndarray
            gain from groundwater for all stream nodes for the current 
            simulation timestep

        Note
        ----
        This method is designed for use when is_for_inquiry=0 to return
        gain from groundwater at the current timestep during a 
        simulation.

        stream nodes with gain from groundwater will be +
        stream nodes with loss to groundwater will be -
        
        See Also
        --------
        IWFMModel.get_stream_tributary_inflows : Returns small watershed inflows at every stream node for the current timestep
        IWFMModel.get_stream_rainfall_runoff : Returns rainfall runoff at every stream node for the current timestep
        IWFMModel.get_stream_return_flows : Returns agricultural and urban return flows at every stream node for the current timestep
        IWFMModel.get_stream_tile_drain_flows : Returns tile drain flows into every stream node for the current timestep
        IWFMModel.get_stream_riparian_evapotranspiration : Returns riparian evapotranspiration from every stream node for the current timestep
        IWFMModel.get_stream_gain_from_lakes : Returns gain from lakes for every stream node for the current timestep
        IWFMModel.get_net_bypass_inflows : Returns net bypass inflows for every stream node for the current timestep
        IWFMModel.get_actual_stream_diversions_at_some_locations : Returns actual diversion amounts for a list of diversions during a model simulation
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmGainFromGW"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmGainFromGW"))

        # get number of stream nodes in the model
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # convert unit conversion factor to ctypes
        stream_gain_conversion_factor = ctypes.c_double(stream_gain_conversion_factor)

        # initialize output variables
        gain_from_groundwater = (ctypes.c_double*n_stream_nodes.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmGainFromGW(ctypes.byref(n_stream_nodes),
                                            ctypes.byref(stream_gain_conversion_factor),
                                            gain_from_groundwater,
                                            ctypes.byref(self.status))

        return np.array(gain_from_groundwater)

    def get_stream_gain_from_lakes(self, lake_inflow_conversion_factor=1.0):
        ''' Returns gain from lakes for every stream node for the current timestep
        
        Parameters
        ----------
        lake_inflow_conversion_factor : float
            conversion factor for gain from lakes from 
            the simulation units of volume to a desired unit of volume

        Returns
        -------
        np.ndarray
            gain from lakes for all stream nodes for the current 
            simulation timestep

        Note
        ----
        This method is designed for use when is_for_inquiry=0 to return
        gain from groundwater at the current timestep during a 
        simulation.

        stream nodes without gain from lakes will be 0
        
        See Also
        --------
        IWFMModel.get_stream_tributary_inflows : Returns small watershed inflows at every stream node for the current timestep
        IWFMModel.get_stream_rainfall_runoff : Returns rainfall runoff at every stream node for the current timestep
        IWFMModel.get_stream_return_flows : Returns agricultural and urban return flows at every stream node for the current timestep
        IWFMModel.get_stream_tile_drain_flows : Returns tile drain flows into every stream node for the current timestep
        IWFMModel.get_stream_riparian_evapotranspiration : Returns riparian evapotranspiration from every stream node for the current timestep
        IWFMModel.get_stream_gain_from_groundwater : Returns gain from groundwater for every stream node for the current timestep
        IWFMModel.get_net_bypass_inflows : Returns net bypass inflows for every stream node for the current timestep
        IWFMModel.get_actual_stream_diversions_at_some_locations : Returns actual diversion amounts for a list of diversions during a model simulation
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmGainFromLakes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmGainFromLakes"))

        # get number of stream nodes in the model
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # convert unit conversion factor to ctypes
        lake_inflow_conversion_factor = ctypes.c_double(lake_inflow_conversion_factor)

        # initialize output variables
        gain_from_lakes = (ctypes.c_double*n_stream_nodes.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmGainFromLakes(ctypes.byref(n_stream_nodes),
                                               ctypes.byref(lake_inflow_conversion_factor),
                                               gain_from_lakes,
                                               ctypes.byref(self.status))

        return np.array(gain_from_lakes)

    def get_net_bypass_inflows(self, bypass_inflow_conversion_factor=1.0):
        ''' Returns net bypass inflows for every stream node for the current timestep
        
        Parameters
        ----------
        bypass_inflow_conversion_factor : float
            conversion factor for net bypass inflow from 
            the simulation units of volume to a desired unit of volume

        Returns
        -------
        np.ndarray
            net bypass inflow for all stream nodes for the current 
            simulation timestep

        Note
        ----
        This method is designed for use when is_for_inquiry=0 to return
        net bypass inflow to streams at the current timestep during a 
        simulation.

        stream nodes without net bypass inflow will be 0
        
        See Also
        --------
        IWFMModel.get_stream_tributary_inflows : Returns small watershed inflows at every stream node for the current timestep
        IWFMModel.get_stream_rainfall_runoff : Returns rainfall runoff at every stream node for the current timestep
        IWFMModel.get_stream_return_flows : Returns agricultural and urban return flows at every stream node for the current timestep
        IWFMModel.get_stream_tile_drain_flows : Returns tile drain flows into every stream node for the current timestep
        IWFMModel.get_stream_riparian_evapotranspiration : Returns riparian evapotranspiration from every stream node for the current timestep
        IWFMModel.get_stream_gain_from_groundwater : Returns gain from groundwater for every stream node for the current timestep
        IWFMModel.get_stream_gain_from_lakes : Returns gain from lakes for every stream node for the current timestep
        IWFMModel.get_actual_stream_diversions_at_some_locations : Returns actual diversion amounts for a list of diversions during a model simulation
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmGainFromLakes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmGainFromLakes"))

        # get number of stream nodes in the model
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # convert unit conversion factor to ctypes
        bypass_inflow_conversion_factor = ctypes.c_double(bypass_inflow_conversion_factor)

        # initialize output variables
        net_bypass_inflow = (ctypes.c_double*n_stream_nodes.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmGainFromLakes(ctypes.byref(n_stream_nodes),
                                               ctypes.byref(bypass_inflow_conversion_factor),
                                               net_bypass_inflow,
                                               ctypes.byref(self.status))

        return np.array(net_bypass_inflow)

    def get_actual_stream_diversions_at_some_locations(self, diversion_locations='all', diversion_conversion_factor=1.0):
        ''' Returns actual diversion amounts for a list of diversions during a model simulation
        
        Parameters
        ----------
        diversion_locations : int, list, tuple, np.ndarray, or str='all', default='all'
            one or more diversion ids where actual diversions are
            returned.

        diversion_conversion_factor: float, default=1.0
            conversion factor for actual diversions from the simulation 
            unit of volume to a desired unit of volume
        
        Returns
        -------
        np.ndarray
            actual diversions for the diversion ids provided
        
        Note
        ----
        This method is designed for use when is_for_inquiry=0 to return
        actual diversions amounts for selected diversion locations at 
        the current timestep during a simulation.

        Actual diversion amounts can be less than the required diversion 
        amount if stream goes dry at the stream node where the diversion 
        occurs
        
        See Also
        --------
        IWFMModel.get_stream_tributary_inflows : Returns small watershed inflows at every stream node for the current timestep
        IWFMModel.get_stream_rainfall_runoff : Returns rainfall runoff at every stream node for the current timestep
        IWFMModel.get_stream_return_flows : Returns agricultural and urban return flows at every stream node for the current timestep
        IWFMModel.get_stream_tile_drain_flows : Returns tile drain flows into every stream node for the current timestep
        IWFMModel.get_stream_riparian_evapotranspiration : Returns riparian evapotranspiration from every stream node for the current timestep
        IWFMModel.get_stream_gain_from_groundwater : Returns gain from groundwater for every stream node for the current timestep
        IWFMModel.get_stream_gain_from_lakes : Returns gain from lakes for every stream node for the current timestep
        IWFMModel.get_net_bypass_inflows : Returns net bypass inflows for every stream node for the current timestep
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmActualDiversions_AtSomeDiversions"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmActualDiversions_AtSomeDiversions"))

        # check that diversion locations are provided in correct format
        # get possible stream inflow locations
        diversion_ids = self.get_diversion_ids()

        if isinstance(diversion_locations, str):
            if diversion_locations.lower() == 'all':
                diversion_locations = diversion_ids
            else:
                raise ValueError('if diversion_locations is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(diversion_locations, int):
            diversion_locations = np.array([diversion_locations])
        
        # if list or tuple convert to np.ndarray
        if isinstance(diversion_locations, (list, tuple)):
            diversion_locations = np.array(diversion_locations)

        # if stream_inflow_locations were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(diversion_locations, np.ndarray):
            raise TypeError('diversion_locations must be an int, list, or np.ndarray')

        # check if all of the provided stream_inflow_locations are valid
        if not np.all(np.isin(diversion_locations, diversion_ids)):
            raise ValueError('One or more diversion locations are invalid')

        # convert stream_inflow_locations to stream inflow indices
        # add 1 to convert between python indices and fortran indices
        diversion_indices = np.array([np.where(diversion_ids == item)[0][0] for item in diversion_locations]) + 1
        
        # initialize input variables
        n_diversions = ctypes.c_int(len(diversion_indices))
        diversion_indices = (ctypes.c_int*n_diversions.value)(*diversion_indices)
        diversion_conversion_factor = ctypes.c_double(diversion_conversion_factor)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        actual_diversion_amounts = (ctypes.c_double*n_diversions.value)()

        self.dll.IW_Model_GetStrmActualDiversions_AtSomeDiversions(ctypes.byref(n_diversions),
                                                                   diversion_indices,
                                                                   ctypes.byref(diversion_conversion_factor),
                                                                   actual_diversion_amounts,
                                                                   ctypes.byref(self.status))
        
        return np.array(actual_diversion_amounts)

    def get_stream_diversion_locations(self, diversion_locations='all'):
        ''' Returns the stream node IDs corresponding to diversion locations

        Parameters
        ----------
        diversion_locations : int, list, tuple, np.ndarray, str='all', default='all'
            one or more diversion IDs used to return the corresponding stream node ID
        
        Returns
        -------
        np.ndarray
            array of stream node IDs corresponding to where diversions are exported

        See Also
        --------
        IWFMModel.get_n_diversions : Returns the number of surface water diversions in an IWFM model
        IWFMModel.get_diversion_ids : Returns the surface water diversion identification numbers specified in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stream_diversion_locations()
        array([ 9, 12, 12, 22, 23])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmDiversionsExportNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format("IW_Model_GetStrmDiversionsExportNodes"))

        # check that diversion locations are provided in correct format
        # get possible stream inflow locations
        diversion_ids = self.get_diversion_ids()

        if isinstance(diversion_locations, str):
            if diversion_locations.lower() == 'all':
                diversion_locations = diversion_ids
            else:
                raise ValueError('if diversion_locations is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(diversion_locations, int):
            diversion_locations = np.array([diversion_locations])
        
        # if list or tuple convert to np.ndarray
        if isinstance(diversion_locations, (list, tuple)):
            diversion_locations = np.array(diversion_locations)

        # if stream_inflow_locations were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(diversion_locations, np.ndarray):
            raise TypeError('diversion_locations must be an int, list, or np.ndarray')

        # check if all of the provided stream_inflow_locations are valid
        if not np.all(np.isin(diversion_locations, diversion_ids)):
            raise ValueError('One or more diversion locations are invalid')

        # convert stream_inflow_locations to stream inflow indices
        # add 1 to convert between python indices and fortran indices
        diversion_indices = np.array([np.where(diversion_ids == item)[0][0] for item in diversion_locations]) + 1
        
        # set input variables
        n_diversions = ctypes.c_int(len(diversion_indices))
        diversion_list = (ctypes.c_int*n_diversions.value)(*diversion_indices)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        diversion_stream_nodes = (ctypes.c_int*n_diversions.value)()

        self.dll.IW_Model_GetStrmDiversionsExportNodes(ctypes.byref(n_diversions),
                                                       diversion_list,
                                                       diversion_stream_nodes,
                                                       ctypes.byref(self.status))

        # convert stream node indices to stream node ids
        stream_node_ids = self.get_stream_node_ids()
        stream_diversion_indices = np.array(diversion_stream_nodes)

        return stream_node_ids[stream_diversion_indices - 1]

    def get_n_stream_reaches(self):
        ''' Returns the number of stream reaches in an IWFM model

        Returns
        -------
        int
            number of stream reaches in the IWFM model

        See Also
        --------
        IWFMModel.get_stream_reach_ids : Returns the user-specified identification numbers for the stream reaches in an IWFM model
        IWFMModel.get_n_nodes_in_stream_reach : Returns the number of stream nodes in a stream reach
        IWFMModel.get_stream_reach_groundwater_nodes : Returns the groundwater node IDs corresponding to stream nodes in a specified reach 
        IWFMModel.get_stream_reach_stream_nodes : Returns the stream node IDs corresponding to stream nodes in a specified reach
        IWFMModel.get_stream_reaches_for_stream_nodes : Returns the stream reach indices that correspond to a list of stream nodes
        IWFMModel.get_upstream_nodes_in_stream_reaches : Returns the IDs for the upstream stream node in each stream reach
        IWFMModel.get_n_reaches_upstream_of_reach : Returns the number of stream reaches immediately upstream of the specified reach
        IWFMModel.get_reaches_upstream_of_reach : Returns the IDs of the reaches that are immediately upstream of the specified reach
        IWFMModel.get_downstream_node_in_stream_reaches : Returns the IDs for the downstream stream node in each stream reach
        IWFMModel.get_reach_outflow_destination : Returns the destination index that each stream reach flows into
        IWFMModel.get_reach_outflow_destination_types : Returns the outflow destination types that each stream reach flows into.

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_stream_reaches()
        3
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNReaches"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_ModelGetNReaches'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
            
        # initialize n_stream_reaches variable
        n_stream_reaches = ctypes.c_int(0)
            
        self.dll.IW_Model_GetNReaches(ctypes.byref(n_stream_reaches),
                                      ctypes.byref(self.status))
        
        return n_stream_reaches.value

    def get_stream_reach_ids(self):
        ''' Returns the user-specified identification numbers for the
        stream reaches in an IWFM model 
        
        Returns
        -------
        stream reach_ids : np.ndarray of ints
            integer array containing stream reach ids

        See Also
        --------
        IWFMModel.get_n_stream_reaches : Returns the number of stream reaches in an IWFM model
        IWFMModel.get_n_nodes_in_stream_reach : Returns the number of stream nodes in a stream reach
        IWFMModel.get_stream_reach_groundwater_nodes : Returns the groundwater node IDs corresponding to stream nodes in a specified reach 
        IWFMModel.get_stream_reach_stream_nodes : Returns the stream node IDs corresponding to stream nodes in a specified reach
        IWFMModel.get_stream_reaches_for_stream_nodes : Returns the stream reach IDs that correspond to a list of stream nodes
        IWFMModel.get_upstream_nodes_in_stream_reaches : Returns the IDs for the upstream stream node in each stream reach
        IWFMModel.get_n_reaches_upstream_of_reach : Returns the number of stream reaches immediately upstream of the specified reach
        IWFMModel.get_reaches_upstream_of_reach : Returns the IDs of the reaches that are immediately upstream of the specified reach
        IWFMModel.get_downstream_node_in_stream_reaches : Returns the IDs for the downstream stream node in each stream reach
        IWFMModel.get_reach_outflow_destination : Returns the destination index that each stream reach flows into
        IWFMModel.get_reach_outflow_destination_types : Returns the outflow destination types that each stream reach flows into.

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stream_ids()
        array([2, 1, 3])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetReachIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachIDs"))

        # set input variables
        n_stream_reaches = ctypes.c_int(self.get_n_stream_reaches())
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        stream_reach_ids = (ctypes.c_int*n_stream_reaches.value)()

        self.dll.IW_Model_GetReachIDs(ctypes.byref(n_stream_reaches),
                                      stream_reach_ids,
                                      ctypes.byref(self.status))

        return np.array(stream_reach_ids)

    def get_n_nodes_in_stream_reach(self, reach_id):
        ''' Returns the number of stream nodes in a stream reach
        
        Parameters
        ----------
        reach_id : int
            ID for stream reach used to retrieve the number of stream nodes contained in it 
            
        Returns
        -------
        int
            number of stream nodes specified in the stream reach

        See Also
        --------
        IWFMModel.get_n_stream_reaches : Returns the number of stream reaches in an IWFM model
        IWFMModel.get_stream_reach_ids : Returns the user-specified identification numbers for the stream reaches in an IWFM model
        IWFMModel.get_stream_reach_groundwater_nodes : Returns the groundwater node IDs corresponding to stream nodes in a specified reach 
        IWFMModel.get_stream_reach_stream_nodes : Returns the stream node IDs corresponding to stream nodes in a specified reach
        IWFMModel.get_stream_reaches_for_stream_nodes : Returns the stream reach IDs that correspond to a list of stream nodes
        IWFMModel.get_upstream_nodes_in_stream_reaches : Returns the IDs for the upstream stream node in each stream reach
        IWFMModel.get_n_reaches_upstream_of_reach : Returns the number of stream reaches immediately upstream of the specified reach
        IWFMModel.get_reaches_upstream_of_reach : Returns the IDs of the reaches that are immediately upstream of the specified reach
        IWFMModel.get_downstream_node_in_stream_reaches : Returns the IDs for the downstream stream node in each stream reach
        IWFMModel.get_reach_outflow_destination : Returns the destination index that each stream reach flows into
        IWFMModel.get_reach_outflow_destination_types : Returns the outflow destination types that each stream reach flows into.

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_nodes_in_stream_reach(1)
        10
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetReachNNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachNNodes"))

        # make sure reach_id is an integer
        if not isinstance(reach_id, int):
            raise TypeError('reach_id must be an integer')
        
        # get all possible stream reach ids
        reach_ids = self.get_stream_reach_ids()

        # check that provided reach_id is valid
        if not np.any(reach_ids == reach_id):
            raise ValueError('reach_id provided is not valid')
        
        # convert reach_id to reach index
        # add 1 to index to convert between python index and fortran index
        reach_index = np.where(reach_ids == reach_id)[0][0] + 1

        # convert reach index to ctypes
        reach_index = ctypes.c_int(reach_index)

        # initialize output variables
        n_nodes_in_reach = ctypes.c_int(0)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetReachNNodes(ctypes.byref(reach_index),
                                         ctypes.byref(n_nodes_in_reach),
                                         ctypes.byref(self.status))

        return n_nodes_in_reach.value

    def get_stream_reach_groundwater_nodes(self, reach_id):
        ''' Returns the groundwater node IDs corresponding to stream
        nodes in a specified reach 

        Parameters
        ----------
        reach_id : int
            stream reach ID used to obtain the corresponding groundwater nodes

        Returns
        -------
        np.ndarray
            integer array of groundwater node IDs corresponding to the stream reach

        Note
        ----
        in the case where wide streams are simulated, more than one groundwater node
        can be identified for a corresponding stream node. As of this version, only 
        the first groundwater node specified for each stream node will be returned.

        See Also
        --------
        IWFMModel.get_n_stream_reaches : Returns the number of stream reaches in an IWFM model
        IWFMModel.get_stream_reach_ids : Returns the user-specified identification numbers for the stream reaches in an IWFM model
        IWFMModel.get_n_nodes_in_stream_reach : Returns the number of stream nodes in a stream reach
        IWFMModel.get_stream_reach_stream_nodes : Returns the stream node IDs corresponding to stream nodes in a specified reach
        IWFMModel.get_stream_reaches_for_stream_nodes : Returns the stream reach IDs that correspond to a list of stream nodes
        IWFMModel.get_upstream_nodes_in_stream_reaches : Returns the IDs for the upstream stream node in each stream reach
        IWFMModel.get_n_reaches_upstream_of_reach : Returns the number of stream reaches immediately upstream of the specified reach
        IWFMModel.get_reaches_upstream_of_reach : Returns the IDs of the reaches that are immediately upstream of the specified reach
        IWFMModel.get_downstream_node_in_stream_reaches : Returns the IDs for the downstream stream node in each stream reach
        IWFMModel.get_reach_outflow_destination : Returns the destination index that each stream reach flows into
        IWFMModel.get_reach_outflow_destination_types : Returns the outflow destination types that each stream reach flows into.
        
        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stream_reach_groundwater_nodes(1)
        array([433, 412, 391, 370, 349, 328, 307, 286, 265, 264])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetReachGWNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachGWNodes"))

        # make sure reach_id is an integer
        if not isinstance(reach_id, int):
            raise TypeError('reach_id must be an integer')
        
        # get all possible stream reach ids
        reach_ids = self.get_stream_reach_ids()

        # check that provided reach_id is valid
        if not np.any(reach_ids == reach_id):
            raise ValueError('reach_id provided is not valid')
        
        # convert reach_id to reach index
        # add 1 to index to convert between python index and fortran index
        reach_index = np.where(reach_ids == reach_id)[0][0] + 1

        # convert reach index to ctypes
        reach_index = ctypes.c_int(reach_index)

        # get number of nodes in stream reach
        n_nodes_in_reach = ctypes.c_int(self.get_n_nodes_in_stream_reach(reach_id))

        # initialize output variables
        reach_groundwater_nodes = (ctypes.c_int*n_nodes_in_reach.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetReachGWNodes(ctypes.byref(reach_index),
                                          ctypes.byref(n_nodes_in_reach),
                                          reach_groundwater_nodes,
                                          ctypes.byref(self.status))

        # convert groundwater node indices to groundwater node IDs
        groundwater_node_ids = self.get_node_ids()
        reach_groundwater_node_indices = np.array(reach_groundwater_nodes)

        return groundwater_node_ids[reach_groundwater_node_indices - 1]

    def get_stream_reach_stream_nodes(self, reach_id):
        ''' Returns the stream node IDs corresponding to stream
        nodes in a specified reach 

        Parameters
        ----------
        reach_id : int
            stream reach ID to obtain the corresponding stream nodes

        Returns
        -------
        np.ndarray
            integer array of stream node IDs corresponding to the stream reach

        See Also
        --------
        IWFMModel.get_n_stream_reaches : Returns the number of stream reaches in an IWFM model
        IWFMModel.get_stream_reach_ids : Returns the user-specified identification numbers for the stream reaches in an IWFM model
        IWFMModel.get_n_nodes_in_stream_reach : Returns the number of stream nodes in a stream reach
        IWFMModel.get_stream_reach_groundwater_nodes : Returns the groundwater node IDs corresponding to stream nodes in a specified reach 
        IWFMModel.get_stream_reaches_for_stream_nodes : Returns the stream reach IDs that correspond to a list of stream nodes
        IWFMModel.get_upstream_nodes_in_stream_reaches : Returns the IDs for the upstream stream node in each stream reach
        IWFMModel.get_n_reaches_upstream_of_reach : Returns the number of stream reaches immediately upstream of the specified reach
        IWFMModel.get_reaches_upstream_of_reach : Returns the IDs of the reaches that are immediately upstream of the specified reach
        IWFMModel.get_downstream_node_in_stream_reaches : Returns the IDs for the downstream stream node in each stream reach
        IWFMModel.get_reach_outflow_destination : Returns the destination index that each stream reach flows into
        IWFMModel.get_reach_outflow_destination_types : Returns the outflow destination types that each stream reach flows into.

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stream_reach_stream_nodes(1)
        array([ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetReachStrmNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachStrmNodes"))

        # make sure reach_id is an integer
        if not isinstance(reach_id, int):
            raise TypeError('reach_id must be an integer')
        
        # get all possible stream reach ids
        reach_ids = self.get_stream_reach_ids()

        # check that provided reach_id is valid
        if not np.any(reach_ids == reach_id):
            raise ValueError('reach_id provided is not valid')
        
        # convert reach_id to reach index
        # add 1 to index to convert between python index and fortran index
        reach_index = np.where(reach_ids == reach_id)[0][0] + 1

        # convert reach index to ctypes
        reach_index = ctypes.c_int(reach_index)

        # get number of nodes in stream reach
        n_nodes_in_reach = ctypes.c_int(self.get_n_nodes_in_stream_reach(reach_id))

        # initialize output variables
        reach_stream_nodes = (ctypes.c_int*n_nodes_in_reach.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetReachStrmNodes(ctypes.byref(reach_index),
                                            ctypes.byref(n_nodes_in_reach),
                                            reach_stream_nodes,
                                            ctypes.byref(self.status))

        # convert stream node indices to IDs
        stream_node_ids = self.get_stream_node_ids()
        stream_node_indices = np.array(reach_stream_nodes)

        return stream_node_ids[stream_node_indices - 1]

    def get_stream_reaches_for_stream_nodes(self, stream_nodes='all'):
        ''' Returns the stream reach IDs that correspond to one or more stream node IDs

        Parameters
        ---------
        stream_node_ids : int, list, tuple, np.ndarray, str='all', default='all'
            one or more stream node IDs where the stream reach IDs will be returned

        Returns
        -------
        np.ndarray
            array of stream reach IDs corresponding to stream node IDs provided

        See Also
        --------
        IWFMModel.get_n_stream_reaches : Returns the number of stream reaches in an IWFM model
        IWFMModel.get_stream_reach_ids : Returns the user-specified identification numbers for the stream reaches in an IWFM model
        IWFMModel.get_n_nodes_in_stream_reach : Returns the number of stream nodes in a stream reach
        IWFMModel.get_stream_reach_groundwater_nodes : Returns the groundwater node IDs corresponding to stream nodes in a specified reach 
        IWFMModel.get_stream_reach_stream_nodes : Returns the stream node IDs corresponding to stream nodes in a specified reach
        IWFMModel.get_upstream_nodes_in_stream_reaches : Returns the IDs for the upstream stream node in each stream reach
        IWFMModel.get_n_reaches_upstream_of_reach : Returns the number of stream reaches immediately upstream of the specified reach
        IWFMModel.get_reaches_upstream_of_reach : Returns the IDs of the reaches that are immediately upstream of the specified reach
        IWFMModel.get_downstream_node_in_stream_reaches : Returns the IDs for the downstream stream node in each stream reach
        IWFMModel.get_reach_outflow_destination : Returns the destination index that each stream reach flows into
        IWFMModel.get_reach_outflow_destination_types : Returns the outflow destination types that each stream reach flows into.

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stream_reaches_for_stream_nodes()
        array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetReaches_ForStrmNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReaches_ForStrmNodes"))

        # get possible stream nodes locations
        stream_node_ids = self.get_stream_node_ids()

        if isinstance(stream_nodes, str):
            if stream_nodes.lower() == 'all':
                stream_nodes = stream_node_ids
            else:
                raise ValueError('if stream_nodes is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(stream_nodes, int):
            stream_nodes = np.array([stream_nodes])
        
        # if list or tuple convert to np.ndarray
        if isinstance(stream_nodes, (list, tuple)):
            stream_nodes = np.array(stream_nodes)

        # if stream_inflow_locations were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(stream_nodes, np.ndarray):
            raise TypeError('stream_nodes must be an int, list, tuple, np.ndarray, or "all"')

        # check if all of the provided stream_inflow_locations are valid
        if not np.all(np.isin(stream_nodes, stream_node_ids)):
            raise ValueError('One or more stream nodes provided are invalid')

        # convert stream_inflow_locations to stream inflow indices
        # add 1 to convert between python indices and fortran indices
        stream_node_indices = np.array([np.where(stream_node_ids == item)[0][0] for item in stream_nodes]) + 1
        
        # get number of stream nodes indices provided
        n_stream_nodes = ctypes.c_int(len(stream_node_indices))

        # convert stream node indices to ctypes
        stream_node_indices = (ctypes.c_int*n_stream_nodes.value)(*stream_node_indices)

        # initialize output variables
        stream_reaches = (ctypes.c_int*n_stream_nodes.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
        
        self.dll.IW_Model_GetReaches_ForStrmNodes(ctypes.byref(n_stream_nodes),
                                                  stream_node_indices,
                                                  stream_reaches,
                                                  ctypes.byref(self.status))

        # convert stream reach indices to stream reach IDs
        stream_reach_ids = self.get_stream_reach_ids()
        stream_reach_indices = np.array(stream_reaches)

        return stream_reach_ids[stream_reach_indices - 1]

    def get_upstream_nodes_in_stream_reaches(self):
        ''' Returns the IDs for the upstream stream node in each
        stream reach

        Returns
        -------
        np.ndarray
            array of stream node IDs corresponding to the most 
            upstream stream node in each stream reach

        See Also
        --------
        IWFMModel.get_n_stream_reaches : Returns the number of stream reaches in an IWFM model
        IWFMModel.get_stream_reach_ids : Returns the user-specified identification numbers for the stream reaches in an IWFM model
        IWFMModel.get_n_nodes_in_stream_reach : Returns the number of stream nodes in a stream reach
        IWFMModel.get_stream_reach_groundwater_nodes : Returns the groundwater node IDs corresponding to stream nodes in a specified reach 
        IWFMModel.get_stream_reach_stream_nodes : Returns the stream node IDs corresponding to stream nodes in a specified reach
        IWFMModel.get_stream_reaches_for_stream_nodes : Returns the stream reach IDs that correspond to a list of stream nodes
        IWFMModel.get_n_reaches_upstream_of_reach : Returns the number of stream reaches immediately upstream of the specified reach
        IWFMModel.get_reaches_upstream_of_reach : Returns the IDs of the reaches that are immediately upstream of the specified reach
        IWFMModel.get_downstream_node_in_stream_reaches : Returns the IDs for the downstream stream node in each stream reach
        IWFMModel.get_reach_outflow_destination : Returns the destination index that each stream reach flows into
        IWFMModel.get_reach_outflow_destination_types : Returns the outflow destination types that each stream reach flows into.

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_upstream_nodes_in_stream_reaches()
        array([11,  1, 17])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetReachUpstrmNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachUpstrmNodes"))

        # get number of reaches specified in the model
        n_reaches = ctypes.c_int(self.get_n_stream_reaches())

        # initialize output variables
        upstream_stream_nodes = (ctypes.c_int*n_reaches.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
        
        self.dll.IW_Model_GetReachUpstrmNodes(ctypes.byref(n_reaches),
                                              upstream_stream_nodes,
                                              ctypes.byref(self.status))

        # convert upstream stream node indices to stream node IDs
        stream_node_ids = self.get_stream_node_ids()
        upstream_stream_node_indices = np.array(upstream_stream_nodes)

        return stream_node_ids[upstream_stream_node_indices - 1]

    def get_n_reaches_upstream_of_reach(self, reach_id):
        ''' Returns the number of stream reaches immediately upstream 
        of the specified reach

        Parameters
        ----------
        reach_id : int
            stream reach ID to obtain the corresponding stream nodes

        Returns
        -------
        int
            number of stream reaches immediately upstream of specified
            stream reach.

        Note
        ----
        if there are no stream reaches upstream, this method returns 0
        if the reach is downstream of a confluence of tributaries, this method returns the number 
        of tributary reaches. Otherwise, this method returns 1

        See Also
        --------
        IWFMModel.get_n_stream_reaches : Returns the number of stream reaches in an IWFM model
        IWFMModel.get_stream_reach_ids : Returns the user-specified identification numbers for the stream reaches in an IWFM model
        IWFMModel.get_n_nodes_in_stream_reach : Returns the number of stream nodes in a stream reach
        IWFMModel.get_stream_reach_groundwater_nodes : Returns the groundwater node IDs corresponding to stream nodes in a specified reach 
        IWFMModel.get_stream_reach_stream_nodes : Returns the stream node IDs corresponding to stream nodes in a specified reach
        IWFMModel.get_stream_reaches_for_stream_nodes : Returns the stream reach IDs that correspond to a list of stream nodes
        IWFMModel.get_upstream_nodes_in_stream_reaches : Returns the IDs for the upstream stream node in each stream reach
        IWFMModel.get_reaches_upstream_of_reach : Returns the IDs of the reaches that are immediately upstream of the specified reach
        IWFMModel.get_downstream_node_in_stream_reaches : Returns the IDs for the downstream stream node in each stream reach
        IWFMModel.get_reach_outflow_destination : Returns the destination index that each stream reach flows into
        IWFMModel.get_reach_outflow_destination_types : Returns the outflow destination types that each stream reach flows into.

        Examples
        --------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_reaches_upstream_of_reach(1)
        0
        >>> model.kill()

        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_reaches_upstream_of_reach(3)
        1
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetReachNUpstrmReaches"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachNUpstrmReaches"))

        # make sure reach_id is an integer
        if not isinstance(reach_id, int):
            raise TypeError('reach_id must be an integer')
        
        # get all possible stream reach ids
        reach_ids = self.get_stream_reach_ids()

        # check that provided reach_id is valid
        if not np.any(reach_ids == reach_id):
            raise ValueError('reach_id provided is not valid')
        
        # convert reach_id to reach index
        # add 1 to index to convert between python index and fortran index
        reach_index = np.where(reach_ids == reach_id)[0][0] + 1

        # convert reach_index to ctypes
        reach_index = ctypes.c_int(reach_index)

        # initialize output variables
        n_upstream_reaches = ctypes.c_int(0)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
        
        self.dll.IW_Model_GetReachNUpstrmReaches(ctypes.byref(reach_index),
                                                 ctypes.byref(n_upstream_reaches),
                                                 ctypes.byref(self.status))

        return n_upstream_reaches.value

    def get_reaches_upstream_of_reach(self, reach_id):
        ''' Returns the IDs of the reaches that are immediately 
        upstream of the specified reach

        Parameters
        ----------
        reach_id : int
            stream reach ID to obtain the corresponding stream nodes

        Returns
        -------
        np.ndarray
            array of reach IDs immediately upstream of the specified reach

        See Also
        --------
        IWFMModel.get_n_stream_reaches : Returns the number of stream reaches in an IWFM model
        IWFMModel.get_stream_reach_ids : Returns the user-specified identification numbers for the stream reaches in an IWFM model
        IWFMModel.get_n_nodes_in_stream_reach : Returns the number of stream nodes in a stream reach
        IWFMModel.get_stream_reach_groundwater_nodes : Returns the groundwater node IDs corresponding to stream nodes in a specified reach 
        IWFMModel.get_stream_reach_stream_nodes : Returns the stream node IDs corresponding to stream nodes in a specified reach
        IWFMModel.get_stream_reaches_for_stream_nodes : Returns the stream reach IDs that correspond to a list of stream nodes
        IWFMModel.get_upstream_nodes_in_stream_reaches : Returns the IDs for the upstream stream node in each stream reach
        IWFMModel.get_n_reaches_upstream_of_reach : Returns the number of stream reaches immediately upstream of the specified reach
        IWFMModel.get_downstream_node_in_stream_reaches : Returns the IDs for the downstream stream node in each stream reach
        IWFMModel.get_reach_outflow_destination : Returns the destination index that each stream reach flows into
        IWFMModel.get_reach_outflow_destination_types : Returns the outflow destination types that each stream reach flows into.

        Examples
        --------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> print(model.get_n_reaches_upstream_of_reach(1))
        None
        >>> model.kill()

        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_reaches_upstream_of_reach(3)
        array([2])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetReachUpstrmReaches"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachUpstrmReaches"))

        # make sure reach_id is an integer
        if not isinstance(reach_id, int):
            raise TypeError('reach_id must be an integer')
        
        # get all possible stream reach ids
        reach_ids = self.get_stream_reach_ids()

        # check that provided reach_id is valid
        if not np.any(reach_ids == reach_id):
            raise ValueError('reach_id provided is not valid')
        
        # convert reach_id to reach index
        # add 1 to index to convert between python index and fortran index
        reach_index = np.where(reach_ids == reach_id)[0][0] + 1

        # get the number of reaches upstream of the specified reach
        n_upstream_reaches = ctypes.c_int(self.get_n_reaches_upstream_of_reach(reach_id))

        # if there are no upstream reaches, then return
        if n_upstream_reaches.value == 0:
            return

        # convert reach index to ctypes
        reach_index = ctypes.c_int(reach_index)

        # initialize output variables
        upstream_reaches = (ctypes.c_int*n_upstream_reaches.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
        
        self.dll.IW_Model_GetReachUpstrmReaches(ctypes.byref(reach_index),
                                                ctypes.byref(n_upstream_reaches),
                                                upstream_reaches,
                                                ctypes.byref(self.status))

        # convert reach indices to reach IDs
        stream_reach_ids = self.get_stream_reach_ids()
        upstream_reach_indices = np.array(upstream_reaches)

        return stream_reach_ids[upstream_reach_indices - 1]

    def get_downstream_node_in_stream_reaches(self):
        ''' Returns the IDs for the downstream stream node in each 
        stream reach

        Returns
        -------
        np.ndarray
            array of stream node IDs for the downstream stream node
            in each stream reach

        See Also
        --------
        IWFMModel.get_n_stream_reaches : Returns the number of stream reaches in an IWFM model
        IWFMModel.get_stream_reach_ids : Returns the user-specified identification numbers for the stream reaches in an IWFM model
        IWFMModel.get_n_nodes_in_stream_reach : Returns the number of stream nodes in a stream reach
        IWFMModel.get_stream_reach_groundwater_nodes : Returns the groundwater node IDs corresponding to stream nodes in a specified reach 
        IWFMModel.get_stream_reach_stream_nodes : Returns the stream node IDs corresponding to stream nodes in a specified reach
        IWFMModel.get_stream_reaches_for_stream_nodes : Returns the stream reach IDs that correspond to a list of stream nodes
        IWFMModel.get_upstream_nodes_in_stream_reaches : Returns the IDs for the upstream stream node in each stream reach
        IWFMModel.get_n_reaches_upstream_of_reach : Returns the number of stream reaches immediately upstream of the specified reach
        IWFMModel.get_reaches_upstream_of_reach : Returns the IDs of the reaches that are immediately upstream of the specified reach
        IWFMModel.get_reach_outflow_destination : Returns the destination index that each stream reach flows into
        IWFMModel.get_reach_outflow_destination_types : Returns the outflow destination types that each stream reach flows into.

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_downstream_node_in_stream_reaches()
        array([16, 10, 23])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetReachDownstrmNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachDownstrmNodes"))

        # get number of reaches specified in the model
        n_reaches = ctypes.c_int(self.get_n_stream_reaches())

        # initialize output variables
        downstream_stream_nodes = (ctypes.c_int*n_reaches.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)        
        
        self.dll.IW_Model_GetReachDownstrmNodes(ctypes.byref(n_reaches),
                                                downstream_stream_nodes,
                                                ctypes.byref(self.status))

        # convert stream node indices to stream node IDs
        stream_node_ids = self.get_stream_node_ids()
        downstream_stream_node_indices = np.array(downstream_stream_nodes)
        
        return stream_node_ids[downstream_stream_node_indices - 1]

    def get_reach_outflow_destination(self):
        ''' Returns the destination index that each stream reach flows 
        into.

        Returns
        -------
        np.ndarray
            array of destination indices corresponding to the destination 
            of flows exiting each stream reach

        Note
        ----
        To find out the type of destination (i.e. lake, another 
        stream node or outside the model domain) that the reaches 
        flow into, it is necessary to call:
        IWFMModel.get_reach_outflow_destination_types

        See Also
        --------
        IWFMModel.get_n_stream_reaches : Returns the number of stream reaches in an IWFM model
        IWFMModel.get_stream_reach_ids : Returns the user-specified identification numbers for the stream reaches in an IWFM model
        IWFMModel.get_n_nodes_in_stream_reach : Returns the number of stream nodes in a stream reach
        IWFMModel.get_stream_reach_groundwater_nodes : Returns the groundwater node IDs corresponding to stream nodes in a specified reach 
        IWFMModel.get_stream_reach_stream_nodes : Returns the stream node IDs corresponding to stream nodes in a specified reach
        IWFMModel.get_stream_reaches_for_stream_nodes : Returns the stream reach IDs that correspond to a list of stream nodes
        IWFMModel.get_upstream_nodes_in_stream_reaches : Returns the IDs for the upstream stream node in each stream reach
        IWFMModel.get_n_reaches_upstream_of_reach : Returns the number of stream reaches immediately upstream of the specified reach
        IWFMModel.get_reaches_upstream_of_reach : Returns the IDs of the reaches that are immediately upstream of the specified reach
        IWFMModel.get_downstream_node_in_stream_reaches : Returns the IDs for the downstream stream node in each stream reach
        IWFMModel.get_reach_outflow_destination_types : Returns the outflow destination types that each stream reach flows into.

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_reach_outflow_destination()
        array([17, 1, 0])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetReachOutflowDest"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachOutflowDest"))
        
        # get number of reaches
        n_reaches = ctypes.c_int(self.get_n_stream_reaches())

        # initialize output variables
        reach_outflow_destinations = (ctypes.c_int*n_reaches.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetReachOutflowDest(ctypes.byref(n_reaches),
                                              reach_outflow_destinations,
                                              ctypes.byref(self.status))

        return np.array(reach_outflow_destinations)

    def get_reach_outflow_destination_types(self):
        ''' Returns the outflow destination types that each stream reach
        flows into.

        Returns
        -------
        np.ndarray
            array of destination types for each reach in the IWFM model

        Note
        ----
        A return value of 0 corresponds to flow leaving the model domain
        A return value of 1 corresponds to flow to a stream node in another reach
        A return value of 3 corresponds to flow to a lake
        
        See Also
        --------
        IWFMModel.get_n_stream_reaches : Returns the number of stream reaches in an IWFM model
        IWFMModel.get_stream_reach_ids : Returns the user-specified identification numbers for the stream reaches in an IWFM model
        IWFMModel.get_n_nodes_in_stream_reach : Returns the number of stream nodes in a stream reach
        IWFMModel.get_stream_reach_groundwater_nodes : Returns the groundwater node IDs corresponding to stream nodes in a specified reach 
        IWFMModel.get_stream_reach_stream_nodes : Returns the stream node IDs corresponding to stream nodes in a specified reach
        IWFMModel.get_stream_reaches_for_stream_nodes : Returns the stream reach IDs that correspond to a list of stream nodes
        IWFMModel.get_upstream_nodes_in_stream_reaches : Returns the IDs for the upstream stream node in each stream reach
        IWFMModel.get_n_reaches_upstream_of_reach : Returns the number of stream reaches immediately upstream of the specified reach
        IWFMModel.get_reaches_upstream_of_reach : Returns the IDs of the reaches that are immediately upstream of the specified reach
        IWFMModel.get_downstream_node_in_stream_reaches : Returns the IDs for the downstream stream node in each stream reach
        IWFMModel.get_reach_outflow_destination : Returns the destination index that each stream reach flows into
        
        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_reach_outflow_destination_types()
        array([1, 3, 0])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetReachOutflowDestTypes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachOutflowDestTypes"))
        
        # get number of reaches
        n_reaches = ctypes.c_int(self.get_n_stream_reaches())

        # initialize output variables
        reach_outflow_destination_types = (ctypes.c_int*n_reaches.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetReachOutflowDestTypes(ctypes.byref(n_reaches),
                                                   reach_outflow_destination_types,
                                                   ctypes.byref(self.status))

        return np.array(reach_outflow_destination_types)

    def get_n_diversions(self):
        ''' Returns the number of surface water diversions in an IWFM model

        Returns
        -------
        int
            number of surface water diversions in the IWFM Model

        See Also
        --------
        IWFMModel.get_diversion_ids : Returns the surface water diversion identification numbers specified in an IWFM model
        IWFMModel.get_stream_diversion_locations : Returns the stream node IDs corresponding to diversion locations

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_diversions()
        5
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNDiversions"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNDiversions'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
            
        # initialize n_stream_reaches variable
        n_diversions = ctypes.c_int(0)
            
        self.dll.IW_Model_GetNDiversions(ctypes.byref(n_diversions),
                                         ctypes.byref(self.status))
                    
        return n_diversions.value

    def get_diversion_ids(self):
        ''' Returns the surface water diversion identification numbers
        specified in an IWFM model
        
        Returns
        -------
        np.ndarray
            array of diversion IDs

        See Also
        --------
        IWFMModel.get_n_diversions : Returns the number of surface water diversions in an IWFM model
        IWFMModel.get_stream_diversion_locations : Returns the stream node IDs corresponding to diversion locations

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_diversion_ids()
        array([1, 2, 3, 4, 5])
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetDiversionIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetDiversionIDs"))

        # set input variables
        n_diversions = ctypes.c_int(self.get_n_diversions())
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        diversion_ids = (ctypes.c_int*n_diversions.value)()

        self.dll.IW_Model_GetDiversionIDs(ctypes.byref(n_diversions),
                                          diversion_ids,
                                          ctypes.byref(self.status))

        return np.array(diversion_ids)

    def get_n_lakes(self):
        ''' Returns the number of lakes in an IWFM model

        Returns
        -------
        int
            number of lakes in the IWFM model

        See Also
        --------
        IWFMModel.get_lake_ids : Returns the lake IDs specified by the user
        IWFMModel.get_n_elements_in_lake : Returns the number of finite element grid cells that make up a lake 
        IWFMModel.get_elements_in_lake : Returns the element ids with the specified lake ID

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_lakes()
        1
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNLakes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNLakes'))
          
        # initialize n_stream_reaches variable
        n_lakes = ctypes.c_int(0)
            
        # set instance variable status to 0
        self.status = ctypes.c_int(0)
        
        self.dll.IW_Model_GetNLakes(ctypes.byref(n_lakes),
                                    ctypes.byref(self.status))
        
        return n_lakes.value

    def get_lake_ids(self):
        ''' Returns the lake IDs specified by the user

        Returns
        -------
        np.ndarray
            array of lake identification numbers for each lake in the model

        See Also
        --------
        IWFMModel.get_n_lakes : Returns the number of lakes in an IWFM model
        IWFMModel.get_n_elements_in_lake : Returns the number of finite element grid cells that make up a lake 
        IWFMModel.get_elements_in_lake : Returns the element ids with the specified lake ID

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_lake_ids()
        array([1])
        >>> model.kill() 
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetLakeIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetLakeIDs'))

        # initialize n_stream_reaches variable
        n_lakes = ctypes.c_int(self.get_n_lakes())

        # stop here if no lakes are specified
        if n_lakes.value == 0:
            return

        # initialize output variables
        lake_ids = (ctypes.c_int*n_lakes.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetLakeIDs(ctypes.byref(n_lakes),
                                     lake_ids,
                                     ctypes.byref(self.status))

        return np.array(lake_ids)

    def get_n_elements_in_lake(self, lake_id):
        ''' Returns the number of finite element grid cells that make
        up a lake

        Parameters
        ----------
        lake_id : int
            lake identification number used to obtain number of elements
            contained in the lake

        Returns
        -------
        int
            number of elements representing the lake with the provided
            id number

        See Also
        --------
        IWFMModel.get_n_lakes : Returns the number of lakes in an IWFM model
        IWFMModel.get_lake_ids : Returns the lake IDs specified by the user
        IWFMModel.get_elements_in_lake : Returns the element ids with the specified lake ID

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_elements_in_lake()
        10
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetLakeIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetLakeIDs'))
        
        # check if any lakes exist
        n_lakes = self.get_n_lakes()

        # if no lakes exist, return 0
        if n_lakes == 0:
            return 0

        # check that lake_id is an integer
        if not isinstance(lake_id, int):
            raise TypeError('lake_id must be an integer')

        # get all lake ids
        lake_ids = self.get_lake_ids()

        # check to see if the lake_id provided is a valid lake ID
        if not np.any(lake_ids == lake_id):
            raise ValueError('lake_id specified is not valid')

        # convert lake_id to lake index
        # add 1 to index to convert from python index to fortran index
        lake_index = np.where(lake_ids == lake_id)[0][0] + 1
        
        # convert lake id to ctypes
        lake_index = ctypes.c_int(lake_index)
        
        # initialize output variables
        n_elements_in_lake = ctypes.c_int(0)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetNElementsInLake(ctypes.byref(lake_index),
                                             ctypes.byref(n_elements_in_lake),
                                             ctypes.byref(self.status))

        return n_elements_in_lake.value

    def get_elements_in_lake(self, lake_id):
        ''' Returns the element ids with the specified lake ID
        
        Parameters
        ----------
        lake_id : int
            lake ID used to obtain element IDs that correspond to the lake

        Returns
        -------
        np.ndarray
            array of element IDs representing the lake with the provided
            ID number

        See Also
        --------
        IWFMModel.get_n_lakes : Returns the number of lakes in an IWFM model
        IWFMModel.get_lake_ids : Returns the lake IDs specified by the user
        IWFMModel.get_n_elements_in_lake : Returns the number of finite element grid cells that make up a lake

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_elements_in_lake(1)
        array([169, 170, 171, 188, 189, 190, 207, 208, 209, 210])
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetLakeIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetLakeIDs'))

        # get number of lakes
        n_lakes = self.get_n_lakes()

        # if no lakes exist in the model return
        if n_lakes == 0:
            return

        # check that lake_id is an integer
        if not isinstance(lake_id, int):
            raise TypeError('lake_id must be an integer')

        # get all lake ids
        lake_ids = self.get_lake_ids()

        # check to see if the lake_id provided is a valid lake ID
        if not np.any(lake_ids == lake_id):
            raise ValueError('lake_id specified is not valid')

        # convert lake_id to lake index
        # add 1 to index to convert from python index to fortran index
        lake_index = np.where(lake_ids == lake_id)[0][0] + 1
        
        # convert lake id to ctypes
        lake_index = ctypes.c_int(lake_index)
        
        # get number of elements in lake
        n_elements_in_lake = ctypes.c_int(self.get_n_elements_in_lake(lake_id))

        # initialize output variables
        elements_in_lake = (ctypes.c_int*n_elements_in_lake.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetElementsInLake(ctypes.byref(lake_index),
                                            ctypes.byref(n_elements_in_lake),
                                            elements_in_lake,
                                            ctypes.byref(self.status))

        # convert element indices to element IDs
        element_ids = self.get_element_ids()
        lake_element_indices = np.array(elements_in_lake)

        return element_ids[lake_element_indices - 1]

    def get_n_tile_drains(self):
        ''' Returns the number of tile drain nodes in an IWFM model

        Returns
        -------
        int
            number of tile drains simulated in the IWFM model 
            application

        See Also
        --------
        IWFMModel.get_tile_drain_ids : Returns the user-specified IDs for tile drains simulated in an IWFM model
        IWFMModel.get_tile_drain_nodes : Returns the node ids where tile drains are specified

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_tile_drains()
        21
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNTileDrainNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNTileDrainNodes'))

        # initialize output variables
        n_tile_drains = ctypes.c_int(0)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
            
        self.dll.IW_Model_GetNTileDrainNodes(ctypes.byref(n_tile_drains),
                                             ctypes.byref(self.status))
        
        return n_tile_drains.value

    def get_tile_drain_ids(self):
        ''' Returns the user-specified IDs for tile drains simulated in an IWFM model

        Returns
        -------
        np.ndarray
            array of tile drain IDs specified in an IWFM model

        See Also
        --------
        IWFMModel.get_n_tile_drains : Returns the number of tile drain nodes in an IWFM model
        IWFMModel.get_tile_drain_nodes : Returns the node ids where tile drains are specified

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_tile_drain_ids()
        array([ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17,
               18, 19, 20, 21])
        >>> model.kill()
        '''
         # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetTileDrainIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetTileDrainIDs'))

        # initialize n_stream_reaches variable
        n_tile_drains = ctypes.c_int(self.get_n_tile_drains())

        # stop here if no lakes are specified
        if n_tile_drains.value == 0:
            return

        # initialize output variables
        tile_drain_ids = (ctypes.c_int*n_tile_drains.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetTileDrainIDs(ctypes.byref(n_tile_drains),
                                          tile_drain_ids,
                                          ctypes.byref(self.status))

        return np.array(tile_drain_ids)

    def get_tile_drain_nodes(self):
        ''' Returns the node ids where tile drains are specified
        
        Returns
        -------
        np.ndarray
            array of node ids where tiles drains are specified

        See Also
        --------
        IWFMModel.get_n_tile_drains : Returns the number of tile drain nodes in an IWFM model
        IWFMModel.get_tile_drain_ids : Returns the user-specified IDs for tile drains simulated in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_tile_drain_nodes()
        array([  6,  27,  48,  69,  90, 111, 132, 153, 174, 195, 216, 237, 258,
               279, 300, 321, 342, 363, 384, 405, 426])
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetTileDrainNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetTileDrainNodes'))

        # get number of tile_drains
        n_tile_drains = ctypes.c_int(self.get_n_tile_drains())

        # if no tile drains exist in the model return None
        if n_tile_drains.value == 0:
            return
        
        # initialize output variables
        tile_drain_nodes = (ctypes.c_int*n_tile_drains.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetTileDrainNodes(ctypes.byref(n_tile_drains),
                                            tile_drain_nodes,
                                            ctypes.byref(self.status))

        # convert tile drain node indices to node IDs
        node_ids = self.get_node_ids()
        tile_drain_node_indices = np.array(tile_drain_nodes)

        return node_ids[tile_drain_node_indices - 1]

    def get_n_layers(self):
        ''' Returns the number of layers in an IWFM model

        Returns
        -------
        int
            number of layers specified in an IWFM model

        See Also
        --------
        IWFMModel.get_n_nodes : Returns the number of nodes in an IWFM model
        IWFMModel.get_n_elements : Returns the number of elements in an IWFM model
        IWFMModel.get_n_subregions : Returns the number of subregions in an IWFM model
        IWFMModel.get_n_stream_nodes : Returns the number of stream nodes in an IWFM model
        IWFMModel.get_n_stream_inflows : Returns the number of stream boundary inflows specified by the user as timeseries input data

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_layers()
        2
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNLayers"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNLayers'))
    
        # initialize n_layers variable
        n_layers = ctypes.c_int(0)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
            
        self.dll.IW_Model_GetNLayers(ctypes.byref(n_layers),
                                     ctypes.byref(self.status))
          
        return n_layers.value

    def get_ground_surface_elevation(self):
        ''' Returns the ground surface elevation for each node specified 
        in the IWFM model

        Returns
        -------
        np.ndarray
            array of ground surface elevation at every finite element 
            node in an IWFM model

        See Also
        --------
        IWFMModel.get_aquifer_top_elevation : Returns the aquifer top elevations for each finite element node and each layer
        IWFMModel.get_aquifer_bottom_elevation : Returns the aquifer bottom elevations for each finite element node and each layer
        IWFMModel.get_stratigraphy_atXYcoordinate : Returns the stratigraphy at given X,Y coordinates

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_ground_surface_elevation()
        array([500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               270., 270., 270., 270., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 270., 270.,
               250., 270., 270., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 270., 270., 250., 250.,
               270., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 270., 270., 270., 270., 270.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
               500.])
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetGSElev"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetGSElev'))
        
        # get number of model nodes
        n_nodes = ctypes.c_int(self.get_n_nodes())

        # initialize output variables
        gselev = (ctypes.c_double*n_nodes.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
        
        self.dll.IW_Model_GetGSElev(ctypes.byref(n_nodes),
                                    gselev,
                                    ctypes.byref(self.status))
        
        return np.array(gselev)

    def get_aquifer_top_elevation(self):
        ''' Returns the aquifer top elevations for each finite element 
        node and each layer

        Returns
        -------
        np.ndarray
            array of aquifer top elevations for each model layer

        Note
        ----
        Resulting array has a shape of (n_layers, n_nodes)
        
        See Also
        --------
        IWFMModel.get_ground_surface_elevation : Returns the ground surface elevation for each node specified in the IWFM model
        IWFMModel.get_aquifer_bottom_elevation : Returns the aquifer bottom elevations for each finite element node and each layer
        IWFMModel.get_stratigraphy_atXYcoordinate : Returns the stratigraphy at given X,Y coordinates

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_aquifer_top_elevation()
        array([[500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                270., 270., 270., 270., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 270., 270.,
                250., 270., 270., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 270., 270., 250., 250.,
                270., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 270., 270., 270., 270., 270.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500., 500., 500., 500., 500., 500., 500., 500., 500., 500., 500.,
                500.],
               [-10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,   0.,
                  0.]])
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetAquiferTopElev"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetAquiferTopElev'))
        
        # get number of model nodes
        n_nodes = ctypes.c_int(self.get_n_nodes())

        # get number of model layers
        n_layers = ctypes.c_int(self.get_n_layers())
        
        # initialize output variables
        aquifer_top_elevations = ((ctypes.c_double*n_nodes.value)*n_layers.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetAquiferTopElev(ctypes.byref(n_nodes),
                                            ctypes.byref(n_layers),
                                            aquifer_top_elevations,
                                            ctypes.byref(self.status))

        return np.array(aquifer_top_elevations)

    def get_aquifer_bottom_elevation(self):
        ''' Returns the aquifer bottom elevations for each finite element 
        node and each layer

        Returns
        -------
        np.ndarray
            array of aquifer bottom elevations 

        Note
        ----
        Resulting array has a shape of (n_layers, n_nodes)
        
        See Also
        --------
        IWFMModel.get_ground_surface_elevation : Returns the ground surface elevation for each node specified in the IWFM model
        IWFMModel.get_aquifer_top_elevation : Returns the aquifer top elevations for each finite element node and each layer
        IWFMModel.get_stratigraphy_atXYcoordinate : Returns the stratigraphy at given X,Y coordinates

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_aquifer_bottom_elevation()
        array([[   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,
                   0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.,    0.],
               [-110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -110., -110., -110.,
                -110., -110., -110., -110., -110., -110., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.,
                -100., -100., -100., -100., -100., -100., -100., -100., -100.]])
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetAquiferBottomElev"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetAquiferBottomElev'))
        
        # get number of model nodes
        n_nodes = ctypes.c_int(self.get_n_nodes())

        # get number of model layers
        n_layers = ctypes.c_int(self.get_n_layers())
        
        # initialize output variables
        aquifer_bottom_elevations = ((ctypes.c_double*n_nodes.value)*n_layers.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetAquiferBottomElev(ctypes.byref(n_nodes),
                                            ctypes.byref(n_layers),
                                            aquifer_bottom_elevations,
                                            ctypes.byref(self.status))

        return np.array(aquifer_bottom_elevations)

    def get_stratigraphy_atXYcoordinate(self, x, y, fact=1.0, output_options=1):
        ''' Returns the stratigraphy at given X,Y coordinates

        Parameters
        ----------
        x : int, float
            x-coordinate for spatial location

        y : int, float
            y-coordinate for spatial location

        fact : int, float, default=1.0
            conversion factor for x,y coordinates to model length units

        output_options : int, string, default=1
            selects how output is returned by the function {1 or 'combined', 2 or 'gse', 3 or 'tops', 4 or 'bottoms'}

        Returns
        -------
        np.ndarray : if output_options == 1 or 'combined',
            array contains ground surface elevation and the bottoms of all layers
        
        float : if output_options == 2 or 'gse',
            ground surface elevation at x,y coordinates
        
        np.ndarray : if output_options == 3 or 'tops':
            array containing the top elevations of each model layer

        np.ndarray : if output_options == 4 or 'bottoms':
            array containing the bottom elevations of each model layer
        
        tuple : length 3, if output_options is some other integer or string not defined above, 
            ground surface elevation at x,y coordinates,
            numpy array of top elevation of each layer,
            numpy array of bottom elevation of each layer

        Note
        ----
        All return values will be zero if the coordinates provided do not fall within a model element

        If model units are in feet and x,y coordinates are provided in meters, then FACT=3.2808

        See Also
        --------
        IWFMModel.get_ground_surface_elevation : Returns the ground surface elevation for each node specified in the IWFM model
        IWFMModel.get_aquifer_top_elevation : Returns the aquifer top elevations for each finite element node and each layer
        IWFMModel.get_aquifer_bottom_elevation : Returns the aquifer bottom elevations for each finite element node and each layer
        
        Examples
        --------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stratigraphy_atXYcoordinate(590000.0, 4440000.0, 3.2808, 5)
        (500.0, array([500.,   0.]), array([   0., -100.]))
        >>> model.kill()

        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stratigraphy_atXYcoordinate(590000.0, 4440000.0, 3.2808, 1)
        array([ 500.,    0., -100.])
        >>> model.kill()

        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stratigraphy_atXYcoordinate(590000.0, 4440000.0, 3.2808, ''gse')
        500.0
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetStratigraphy_AtXYCoordinate"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetStratigraphy_AtXYCoordinate'))

        if not isinstance(x, (int, float)):
            raise TypeError('X-coordinate must be an int or float')

        if not isinstance(y, (int, float)):
            raise TypeError('Y-coordinate must be an int or float')

        if not isinstance(fact, (int, float)):
            raise TypeError('conversion factor must be an int or float')

        if not isinstance(output_options, (int, str)):
            raise TypeError('output_options must be an integer or string')
        
        # get number of model layers
        n_layers = ctypes.c_int(self.get_n_layers())
            
        # convert input variables to ctypes
        x = ctypes.c_double(x * fact)
        y = ctypes.c_double(y * fact)
            
        # initialize output variables
        gselev = ctypes.c_double(0.0)
        top_elevs = (ctypes.c_double*n_layers.value)()
        bottom_elevs = (ctypes.c_double*n_layers.value)()

        # set instance variable status to 0 
        self.status = ctypes.c_int(0)        
    
        self.dll.IW_Model_GetStratigraphy_AtXYCoordinate(ctypes.byref(n_layers), 
                                                         ctypes.byref(x), 
                                                         ctypes.byref(y), 
                                                         ctypes.byref(gselev), 
                                                         top_elevs, 
                                                         bottom_elevs, 
                                                         ctypes.byref(self.status))
            
        # user output options
        if output_options == 1 or output_options == 'combined':
            output = np.concatenate((gselev.value, np.array(bottom_elevs)), axis=None)
        elif output_options == 2 or output_options == 'gse':
            output = gselev.value
        elif output_options == 3 or output_options == 'tops':
            output = np.array(top_elevs)
        elif output_options == 4 or output_options == 'bottoms':
            output = np.array(bottom_elevs)
        else:
            output = (gselev.value, np.array(top_elevs), np.array(bottom_elevs))
        
        return output

    def get_aquifer_horizontal_k(self):
        ''' Returns the aquifer horizontal hydraulic conductivity for 
        each finite element node and each layer

        Returns
        -------
        np.ndarray
            array of aquifer horizontal hydraulic conductivity

        See Also
        --------
        IWFMModel.get_aquifer_vertical_k : Returns the aquifer vertical hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquitard_vertical_k : Returns the aquitard vertical hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquifer_specific_yield : Returns the aquifer specific yield for each finite element node and each layer
        IWFMModel.get_aquifer_specific_storage : Returns the aquifer specific storage for each finite element node and each layer
        IWFMModel.get_aquifer_parameters : Returns all aquifer parameters at each model node and layer

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_aquifer_horizontal_k()
        array([[50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.],
               [50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.,
                50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50., 50.]])
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetAquiferHorizontalK"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetAquiferHorizontalK'))
        
        # get number of model nodes
        n_nodes = ctypes.c_int(self.get_n_nodes())

        # get number of model layers
        n_layers = ctypes.c_int(self.get_n_layers())
        
        # initialize output variables
        aquifer_horizontal_k = ((ctypes.c_double*n_nodes.value)*n_layers.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetAquiferHorizontalK(ctypes.byref(n_nodes),
                                            ctypes.byref(n_layers),
                                            aquifer_horizontal_k,
                                            ctypes.byref(self.status))

        return np.array(aquifer_horizontal_k)

    def get_aquifer_vertical_k(self):
        ''' Returns the aquifer vertical hydraulic conductivity for each finite element 
        node and each layer

        Returns
        -------
        np.ndarray
            array of aquifer vertical hydraulic conductivity

        See Also
        --------
        IWFMModel.get_aquifer_horizontal_k : Returns the aquifer horizontal hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquitard_vertical_k : Returns the aquitard vertical hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquifer_specific_yield : Returns the aquifer specific yield for each finite element node and each layer
        IWFMModel.get_aquifer_specific_storage : Returns the aquifer specific storage for each finite element node and each layer
        IWFMModel.get_aquifer_parameters : Returns all aquifer parameters at each model node and layer

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_aquifer_vertical_k()
        array([[1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1.],
               [1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                1., 1., 1., 1., 1., 1., 1., 1., 1.]])
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetAquiferVerticalK"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetAquiferVerticalK'))
        
        # get number of model nodes
        n_nodes = ctypes.c_int(self.get_n_nodes())

        # get number of model layers
        n_layers = ctypes.c_int(self.get_n_layers())
        
        # initialize output variables
        aquifer_vertical_k = ((ctypes.c_double*n_nodes.value)*n_layers.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetAquiferVerticalK(ctypes.byref(n_nodes),
                                            ctypes.byref(n_layers),
                                            aquifer_vertical_k,
                                            ctypes.byref(self.status))

        return np.array(aquifer_vertical_k)

    def get_aquitard_vertical_k(self):
        ''' Returns the aquitard vertical hydraulic conductivity for 
        each finite element node and each layer

        Returns
        -------
        np.ndarray
            array of aquitard vertical hydraulic conductivity

        See Also
        --------
        IWFMModel.get_aquifer_horizontal_k : Returns the aquifer horizontal hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquifer_vertical_k : Returns the aquifer vertical hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquifer_specific_yield : Returns the aquifer specific yield for each finite element node and each layer
        IWFMModel.get_aquifer_specific_storage : Returns the aquifer specific storage for each finite element node and each layer
        IWFMModel.get_aquifer_parameters : Returns all aquifer parameters at each model node and layer

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_aquitard_vertical_k()
        array([[0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
               [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]])
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetAquitardVerticalK"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetAquitardVerticalK'))
        
        # get number of model nodes
        n_nodes = ctypes.c_int(self.get_n_nodes())

        # get number of model layers
        n_layers = ctypes.c_int(self.get_n_layers())
        
        # initialize output variables
        aquitard_vertical_k = ((ctypes.c_double*n_nodes.value)*n_layers.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetAquitardVerticalK(ctypes.byref(n_nodes),
                                               ctypes.byref(n_layers),
                                               aquitard_vertical_k,
                                               ctypes.byref(self.status))

        return np.array(aquitard_vertical_k)

    def get_aquifer_specific_yield(self):
        ''' Returns the aquifer specific yield for each finite element 
        node and each layer

        Returns
        -------
        np.ndarray
            array of aquifer specific yield

        See Also
        --------
        IWFMModel.get_aquifer_horizontal_k : Returns the aquifer horizontal hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquifer_vertical_k : Returns the aquifer vertical hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquitard_vertical_k : Returns the aquitard vertical hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquifer_specific_storage : Returns the aquifer specific storage for each finite element node and each layer
        IWFMModel.get_aquifer_parameters : Returns all aquifer parameters at each model node and layer

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_aquifer_specific_yield()
        array([[0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25],
               [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                0.25]])
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetAquiferSy"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetAquiferSy'))
        
        # get number of model nodes
        n_nodes = ctypes.c_int(self.get_n_nodes())

        # get number of model layers
        n_layers = ctypes.c_int(self.get_n_layers())
        
        # initialize output variables
        aquifer_specific_yield = ((ctypes.c_double*n_nodes.value)*n_layers.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetAquiferSy(ctypes.byref(n_nodes),
                                       ctypes.byref(n_layers),
                                       aquifer_specific_yield,
                                       ctypes.byref(self.status))

        return np.array(aquifer_specific_yield)

    def get_aquifer_specific_storage(self):
        ''' Returns the aquifer specific storage for each finite element 
        node and each layer

        Returns
        -------
        np.ndarray
            array of aquifer specific storage

        See Also
        --------
        IWFMModel.get_aquifer_horizontal_k : Returns the aquifer horizontal hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquifer_vertical_k : Returns the aquifer vertical hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquitard_vertical_k : Returns the aquitard vertical hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquifer_specific_yield : Returns the aquifer specific yield for each finite element node and each layer
        IWFMModel.get_aquifer_parameters : Returns all aquifer parameters at each model node and layer

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_aquifer_specific_yield()
        array([[2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01,
                2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01, 2.5e-01],
               [9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05,
                9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05, 9.0e-05]])
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetAquiferSs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetAquiferSs'))
        
        # get number of model nodes
        n_nodes = ctypes.c_int(self.get_n_nodes())

        # get number of model layers
        n_layers = ctypes.c_int(self.get_n_layers())
        
        # initialize output variables
        aquifer_specific_storage = ((ctypes.c_double*n_nodes.value)*n_layers.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetAquiferSs(ctypes.byref(n_nodes),
                                       ctypes.byref(n_layers),
                                       aquifer_specific_storage,
                                       ctypes.byref(self.status))

        return np.array(aquifer_specific_storage)

    def get_aquifer_parameters(self):
        ''' Returns all aquifer parameters at each model node and layer 
        
        Returns
        -------
        tuple of np.ndarray
            aquifer horizontal hydraulic conductivity for each node and layer,
            aquifer vertical hydraulic conductivity for each node and layer,
            aquitard vertical hydraulic conductivity for each node and layer,
            aquifer specific yield for each node and layer,
            aquifer specific storage for each node and layer

        See Also
        --------
        IWFMModel.get_aquifer_horizontal_k : Returns the aquifer horizontal hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquifer_vertical_k : Returns the aquifer vertical hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquitard_vertical_k : Returns the aquitard vertical hydraulic conductivity for each finite element node and each layer
        IWFMModel.get_aquifer_specific_yield : Returns the aquifer specific yield for each finite element node and each layer
        IWFMModel.get_aquifer_specific_storage : Returns the aquifer specific storage for each finite element node and each layer
        
        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> hk, vk, avk, sy, ss = model.get_aquifer_parameters()
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetAquiferParameters"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetAquiferParameters'))
        
        # get number of model nodes
        n_nodes = ctypes.c_int(self.get_n_nodes())

        # get number of model layers
        n_layers = ctypes.c_int(self.get_n_layers())
        
        # initialize output variables
        aquifer_horizontal_k = ((ctypes.c_double*n_nodes.value)*n_layers.value)()
        aquifer_vertical_k = ((ctypes.c_double*n_nodes.value)*n_layers.value)()
        aquitard_vertical_k = ((ctypes.c_double*n_nodes.value)*n_layers.value)()
        aquifer_specific_yield = ((ctypes.c_double*n_nodes.value)*n_layers.value)()
        aquifer_specific_storage = ((ctypes.c_double*n_nodes.value)*n_layers.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
        
        self.dll.IW_Model_GetAquiferParameters(ctypes.byref(n_nodes),
                                               ctypes.byref(n_layers),
                                               aquifer_horizontal_k,
                                               aquifer_vertical_k,
                                               aquitard_vertical_k,
                                               aquifer_specific_yield,
                                               aquifer_specific_storage,
                                               ctypes.byref(self.status))

        return (np.array(aquifer_horizontal_k), np.array(aquifer_vertical_k), 
               np.array(aquitard_vertical_k), np.array(aquifer_specific_yield), 
               np.array(aquifer_specific_storage))

    def get_n_ag_crops(self):
        ''' Returns the number of agricultural crops simulated in an 
        IWFM model

        Returns
        -------
        int
            number of agricultural crops (both non-ponded and ponded)

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_ag_crops()
        7
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNAgCrops"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNAgCrops'))
        
        # initialize output variables
        n_ag_crops = ctypes.c_int(0)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetNAgCrops(ctypes.byref(n_ag_crops),
                                      ctypes.byref(self.status))

        return n_ag_crops.value

    def get_n_wells(self):
        ''' Returns the number of wells simulated in an 
        IWFM model

        Returns
        -------
        int
            number of wells simulated in the IWFM model

        Note
        ----
        This method is intended to be used when is_for_inquiry=0 when performing a model simulation

        See Also
        --------
        IWFMModel.get_well_ids : Returns the well IDs specified in an IWFM model
        IWFMModel.get_n_element_pumps : Returns the number of element pumping wells in an IWFM model
        IWFMModel.get_element_pump_ids : Returns the element pump IDs specified in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_wells()
        0
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNWells"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNWells'))
        
        # initialize output variables
        n_wells = ctypes.c_int(0)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetNWells(ctypes.byref(n_wells),
                                      ctypes.byref(self.status))

        return n_wells.value

    def get_well_ids(self):
        ''' Returns the pumping well IDs specified in an IWFM model
        
        Returns
        -------
        np.ndarray
            array of well IDs

        Note
        ----
        This method is intended to be used when is_for_inquiry=0 when performing a model simulation

        See Also
        --------
        IWFMModel.get_n_wells : Returns the number of pumping wells in an IWFM model
        IWFMModel.get_n_element_pumps : Returns the number of element pumping wells in an IWFM model
        IWFMModel.get_element_pump_ids : Returns the element pump IDs specified in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file, is_for_inquiry=0)
        >>> model.get_well_ids()
        
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetWellIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetWellIDs"))

        # set input variables
        n_wells = ctypes.c_int(self.get_n_wells())
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        well_ids = (ctypes.c_int*n_wells.value)()

        self.dll.IW_Model_GetWellIDs(ctypes.byref(n_wells),
                                          well_ids,
                                          ctypes.byref(self.status))

        return np.array(well_ids)

    def get_n_element_pumps(self):
        ''' Returns the number of element pumps simulated in an 
        IWFM model

        Returns
        -------
        int
            number of element pumps simulated in the IWFM model

        Note
        ----
        This method is intended to be used when is_for_inquiry=0 when performing a model simulation

        See Also
        --------
        IWFMModel.get_n_wells : Returns the number of wells simulated in an IWFM model
        IWFMModel.get_well_ids : Returns the pumping well IDs specified in an IWFM model
        IWFMModel.get_element_pump_ids : Returns the element pump IDs specified in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file, is_for_inquiry=0)
        >>> model.get_n_element_pumps()
        5
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNElemPumps"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNElemPumps'))
        
        # initialize output variables
        n_elem_pumps = ctypes.c_int(0)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetNElemPumps(ctypes.byref(n_elem_pumps),
                                      ctypes.byref(self.status))

        return n_elem_pumps.value

    def get_element_pump_ids(self):
        ''' Returns the element pump IDs specified in an IWFM model
        
        Returns
        -------
        np.ndarray
            array of element pump IDs

        Note
        ----
        This method is intended to be used when is_for_inquiry=0 when performing a model simulation

        See Also
        --------
        IWFMModel.get_well_ids : Returns the well IDs specified in an IWFM model
        IWFMModel.get_n_wells : Returns the number of pumping wells in an IWFM model
        IWFMModel.get_n_element_pumps : Returns the number of element pumping wells in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file, is_for_inquiry=0)
        >>> model.get_element_pump_ids()
        
        >>> model.kill()
        '''
        if not hasattr(self.dll, "IW_Model_GetElemPumpIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetElemPumpIDs"))

        # set input variables
        n_element_pumps = ctypes.c_int(self.get_n_element_pumps())
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        element_pump_ids = (ctypes.c_int*n_element_pumps.value)()

        self.dll.IW_Model_GetWellIDs(ctypes.byref(n_element_pumps),
                                          element_pump_ids,
                                          ctypes.byref(self.status))

        return np.array(element_pump_ids)

    def _get_supply_purpose(self, supply_type_id, supply_indices):
        ''' private method returning the flags for the initial assignment of water supplies
        (diversions, well pumping, element pumping) designating if they serve
        agricultural, urban, or both

        Parameters
        ----------
        supply_type_id : int
            supply type identification number used by IWFM for surface water
            diversions, well pumping, or element pumping

        supply_indices : np.ndarray
            indices of supplies for which flags are being retrieved. This is
            one or more indices for the supply type chosen
            e.g. supply_type_id for diversions supply indices would be one or 
            more diversion ids.

        Returns
        -------
        np.ndarray
            array of flags for each supply index provided

        Note
        ----
        flag equal to 10 for agricultural water demand
        flag equal to 01 for urban water demands
        flag equal to 11 for both ag and urban

        automatic supply adjustment in IWFM allows the supply purpose 
        to change dynamically, so this only returns the user-specified
        initial value.

        It is assumed that type checking and validation is performed in
        the calling method
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetSupplyPurpose"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetSupplyPurpose'))
        
        # convert supply_type_id to ctypes
        supply_type_id = ctypes.c_int(supply_type_id)

        # get number of supply indices
        n_supply_indices = ctypes.c_int(len(supply_indices))

        # convert supply_indices to ctypes
        supply_indices = (ctypes.c_int*n_supply_indices.value)(*supply_indices)

        # initialize output variables
        supply_purpose_flags = (ctypes.c_int*n_supply_indices.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetSupplyPurpose(ctypes.byref(supply_type_id),
                                           ctypes.byref(n_supply_indices),
                                           supply_indices,
                                           supply_purpose_flags,
                                           ctypes.byref(self.status))

        return np.array(supply_purpose_flags)

    def get_diversion_purpose(self, diversions='all'):
        ''' Returns the flags for the initial purpose of the diversions as ag, urban, or both

        Parameters
        ----------
        diversions : int, list, tuple, np.ndarray, or str='all', default='all'
            One or more diversion identification numbers used to return
            the supply purpose.

        Returns
        -------
        np.ndarray
            array of flags for each supply index provided

        Note
        ----
        This method is intended to be used during a model simulation (is_for_inquiry=0)
        after the timeseries data are read
        If it is used when is_for_inquiry=1, it will return the urban flag for each diversion
        regardless if it is urban, ag, or both

        flag equal to 1 for urban water demands
        flag equal to 10 for agricultural water demand
        flag equal to 11 for both ag and urban

        automatic supply adjustment in IWFM allows the supply purpose 
        to change dynamically, so this only returns the user-specified
        initial value.

        See Also
        --------
        IWFMModel.get_well_pumping_purpose : Returns the flags for the initial purpose of the well pumping as ag, urban, or both
        IWFMModel.get_element_pumping_purpose : Returns the flags for the initial purpose of the element pumping as ag, urban, or both

        Examples
        --------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file, is_for_inquiry=0)
        >>> while not model.is_end_of_simulation():
        ...     # advance the simulation time one time step forward
        ...     model.advance_time()
        ...
        ...     # read all time series data from input files
        ...     model.read_timeseries_data()
        ...
        ...     # get diversion supply purpose
        ...     print(model.get_diversion_purpose())
        ...
        ...     # Simulate the hydrologic process for the timestep
        ...     model.simulate_for_one_timestep()
        ...
        ...     # print the results to the user-specified output files
        ...     model.print_results()
        ...
        ...     # advance the state of the hydrologic system in time
        ...     model.advance_state()
        .
        .
        .
        [ 1  1 10 10 10]
        *   TIME STEP 2 AT 10/02/1990_24:00
        [ 1  1 10 10 10]
        *   TIME STEP 3 AT 10/03/1990_24:00
        [ 1  1 10 10 10]
        .
        .
        .
        *   TIME STEP 3652 AT 09/29/2000_24:00
        [ 1  1 10 10 10]
        *   TIME STEP 3653 AT 09/30/2000_24:00
        [ 1  1 10 10 10]
        >>> model.kill()

        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_diversion_purpose()
        array([1, 1, 1, 1, 1])
        >>> model.kill()
        '''
        supply_type_id = self.get_supply_type_id_diversion()

        # get all diversion IDs
        diversion_ids = self.get_diversion_ids()

        if isinstance(diversions, str):
            if diversions.lower() == 'all':
                diversions = diversion_ids
            else:
                raise ValueError('if diversions is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(diversions, int):
            diversions = np.array([diversions])
        
        # if list or tuple convert to np.ndarray
        if isinstance(diversions, (list, tuple)):
            diversions = np.array(diversions)

        # if diversions were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(diversions, np.ndarray):
            raise TypeError('diversions must be an int, list, tuple, np.ndarray, or "all"')

        # check if all of the provided diversion IDs are valid
        if not np.all(np.isin(diversions, diversion_ids)):
            raise ValueError('One or more diversion IDs provided are invalid')

        # convert diversion IDs to diversion indices
        # add 1 to convert between python indices and fortran indices
        diversion_indices = np.array([np.where(diversion_ids == item)[0][0] for item in diversions]) + 1

        return self._get_supply_purpose(supply_type_id, diversion_indices)

    def get_well_pumping_purpose(self, wells='all'):
        ''' Returns the flags for the initial purpose of the well pumping as ag, urban, or both

        Parameters
        ----------
        wells : int, list, tuple, np.ndarray, or str='all', default='all'
            One or more well identification numbers used to return
            the supply purpose.

        Returns
        -------
        np.ndarray
            array of flags for each supply index provided

        Note
        ----
        This method is intended to be used during a model simulation (is_for_inquiry=0)
        after the timeseries data are read
        If it is used when is_for_inquiry=1, it will return the urban flag for each diversion
        regardless if it is urban, ag, or both

        flag equal to 1 for urban water demands
        flag equal to 10 for agricultural water demand
        flag equal to 11 for both ag and urban

        automatic supply adjustment in IWFM allows the supply purpose 
        to change dynamically, so this only returns the user-specified
        initial value.

        See Also
        --------
        IWFMModel.get_diversion_purpose : Returns the flags for the initial purpose of the diversions as ag, urban, or both
        IWFMModel.get_element_pump_purpose : Returns the flags for the initial purpose of the element pumping as ag, urban, or both

        Examples
        --------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file, is_for_inquiry=0)
        >>> while not model.is_end_of_simulation():
        ...     # advance the simulation time one time step forward
        ...     model.advance_time()
        ...
        ...     # read all time series data from input files
        ...     model.read_timeseries_data()
        ...
        ...     # get well pumping supply purpose
        ...     print(model.get_well_pumping_purpose())
        ...
        ...     # Simulate the hydrologic process for the timestep
        ...     model.simulate_for_one_timestep()
        ...
        ...     # print the results to the user-specified output files
        ...     model.print_results()
        ...
        ...     # advance the state of the hydrologic system in time
        ...     model.advance_state()
        .
        .
        .
        [ 1  1 10 10 10]
        *   TIME STEP 2 AT 10/02/1990_24:00
        [ 1  1 10 10 10]
        *   TIME STEP 3 AT 10/03/1990_24:00
        [ 1  1 10 10 10]
        .
        .
        .
        *   TIME STEP 3652 AT 09/29/2000_24:00
        [ 1  1 10 10 10]
        *   TIME STEP 3653 AT 09/30/2000_24:00
        [ 1  1 10 10 10]
        >>> model.kill()

        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_well_pumping_purpose()
        array([1, 1, 1, 1, 1])
        >>> model.kill()'''
        supply_type_id = self.get_supply_type_id_well()

        # get all well IDs
        well_ids = self.get_well_ids()

        if isinstance(wells, str):
            if wells.lower() == 'all':
                wells = well_ids
            else:
                raise ValueError('if wells is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(wells, int):
            wells = np.array([wells])
        
        # if list or tuple convert to np.ndarray
        if isinstance(wells, (list, tuple)):
            wells = np.array(wells)

        # if wells were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(wells, np.ndarray):
            raise TypeError('wells must be an int, list, tuple, np.ndarray, or "all"')

        # check if all of the provided well IDs are valid
        if not np.all(np.isin(wells, well_ids)):
            raise ValueError('One or more well IDs provided are invalid')

        # convert well IDs to well indices
        # add 1 to convert between python indices and fortran indices
        well_indices = np.array([np.where(well_ids == item)[0][0] for item in wells]) + 1

        return self._get_supply_purpose(supply_type_id, well_indices)

    def get_element_pump_purpose(self, element_pumps='all'):
        ''' Returns the flags for the initial purpose of the element pumping as ag, urban, or both

        Parameters
        ----------
        element_pumps : int, list, tuple, np.ndarray, or str='all', default='all'
            One or more element pump identification numbers used to return
            the supply purpose.

        Returns
        -------
        np.ndarray
            array of flags for each supply index provided

        Note
        ----
        This method is intended to be used during a model simulation (is_for_inquiry=0)
        after the timeseries data are read
        If it is used when is_for_inquiry=1, it will return the urban flag for each diversion
        regardless if it is urban, ag, or both

        flag equal to 1 for urban water demands
        flag equal to 10 for agricultural water demand
        flag equal to 11 for both ag and urban

        automatic supply adjustment in IWFM allows the supply purpose 
        to change dynamically, so this only returns the user-specified
        initial value.

        See Also
        --------
        IWFMModel.get_diversion_purpose : Returns the flags for the initial purpose of the diversions as ag, urban, or both
        IWFMModel.get_well_pumping_purpose : Returns the flags for the initial purpose of the well pumping as ag, urban, or both

        Examples
        --------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file, is_for_inquiry=0)
        >>> while not model.is_end_of_simulation():
        ...     # advance the simulation time one time step forward
        ...     model.advance_time()
        ...
        ...     # read all time series data from input files
        ...     model.read_timeseries_data()
        ...
        ...     # get well pumping supply purpose
        ...     print(model.get_element_pumping_purpose())
        ...
        ...     # Simulate the hydrologic process for the timestep
        ...     model.simulate_for_one_timestep()
        ...
        ...     # print the results to the user-specified output files
        ...     model.print_results()
        ...
        ...     # advance the state of the hydrologic system in time
        ...     model.advance_state()
        .
        .
        .
        
        >>> model.kill()

        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_element_pumping_purpose()
        
        >>> model.kill()'''
        supply_type_id = self.get_supply_type_id_well()

        # get all element pump IDs
        element_pump_ids = self.get_element_pump_ids()

        if isinstance(element_pumps, str):
            if element_pumps.lower() == 'all':
                element_pumps = element_pump_ids
            else:
                raise ValueError('if element_pumps is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(element_pumps, int):
            element_pumps = np.array([element_pumps])
        
        # if list or tuple convert to np.ndarray
        if isinstance(element_pumps, (list, tuple)):
            element_pumps = np.array(element_pumps)

        # if element_pumps were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(element_pumps, np.ndarray):
            raise TypeError('element_pumps must be an int, list, tuple, np.ndarray, or "all"')

        # check if all of the provided element pump IDs are valid
        if not np.all(np.isin(element_pumps, element_pump_ids)):
            raise ValueError('One or more element pump IDs provided are invalid')

        # convert element pump IDs to element pump indices
        # add 1 to convert between python indices and fortran indices
        element_pump_indices = np.array([np.where(element_pump_ids == item)[0][0] for item in element_pumps]) + 1

        return self._get_supply_purpose(supply_type_id, element_pump_indices)

    def _get_supply_requirement_ag(self, location_type_id, locations_list, 
                                   conversion_factor):
        ''' Returns the agricultural water supply requirement at a 
        specified set of locations

        Parameters
        ----------
        location_type_id : int
            location type identification number used by IWFM for elements
            or subregions. 

        locations_list : list or np.ndarray
            indices of locations where ag supply requirements are returned

        conversion_factor : float
            factor to convert ag supply requirement from model units to
            desired output units

        Returns
        -------
        np.ndarray
            array of ag supply requirement for locations specified
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetSupplyRequirement_Ag"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetSupplyRequirement_Ag'))
        
        # convert location_type_id to ctypes
        location_type_id = ctypes.c_int(location_type_id)

        # get number of locations
        n_locations = ctypes.c_int(len(locations_list))

        # convert locations_list to ctypes
        locations_list = (ctypes.c_int*n_locations.value)(*locations_list)

        # convert conversion_factor to ctypes
        conversion_factor = ctypes.c_double(conversion_factor)

        # initialize output variables
        ag_supply_requirement = (ctypes.c_double*n_locations.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetSupplyRequirement_Ag(ctypes.byref(location_type_id),
                                                  ctypes.byref(n_locations),
                                                  locations_list,
                                                  ctypes.byref(conversion_factor),
                                                  ag_supply_requirement,
                                                  ctypes.byref(self.status))

        return np.array(ag_supply_requirement)

    def get_supply_requirement_ag_elements(self, elements='all', conversion_factor=1.0):
        ''' Returns the agricultural supply requirement for one or more model elements

        Parameters
        ----------
        elements : int, list, tuple, np.ndarray, or str='all', default='all'
            one or more element identification numbers used to return 
            the ag supply requirement

        conversion_factor : float, default=1.0
            factor to convert ag supply requirement from model units to
            desired output units

        Returns
        -------
        np.ndarray
            array of ag supply requirement for elements specified

        Note
        ----
        This method is intended to be used during a model simulation (is_for_inquiry=0)

        See Also
        --------
        IWFMModel.get_supply_requirement_ag_subregions : Returns the agricultural supply requirement for one or more model subregions
        IWFMModel.get_supply_requirement_urban_elements : Returns the urban supply requirement for one or more model elements 
        IWFMModel.get_supply_requirement_urban_subregions : Returns the urban supply requirement for one or more model subregions

        '''
        location_type_id = self.get_location_type_id_element()

        # get all element IDs
        element_ids = self.get_element_ids()

        if isinstance(elements, str):
            if elements.lower() == 'all':
                elements = element_ids
            else:
                raise ValueError('if elements is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(elements, int):
            elements = np.array([elements])
        
        # if list or tuple convert to np.ndarray
        if isinstance(elements, (list, tuple)):
            elements = np.array(elements)

        # if elements were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(elements, np.ndarray):
            raise TypeError('element must be an int, list, tuple, np.ndarray, or "all"')

        # check if all of the provided element IDs are valid
        if not np.all(np.isin(elements, element_ids)):
            raise ValueError('One or more element IDs provided are invalid')

        # convert element IDs to element indices
        # add 1 to convert between python indices and fortran indices
        element_indices = np.array([np.where(element_ids == item)[0][0] for item in elements]) + 1

        return self._get_supply_requirement_ag(location_type_id, element_indices, conversion_factor)

    def get_supply_requirement_ag_subregions(self, subregions='all', conversion_factor=1.0):
        ''' Returns the agricultural supply requirement for one or more model subregions

        Parameters
        ----------
        subregions : int, list, tuple, np.ndarray, or str='all', default='all'
            one or more subregion identification numbers used to return 
            the ag supply requirement

        conversion_factor : float, default=1.0
            factor to convert ag supply requirement from model units to
            desired output units

        Returns
        -------
        np.ndarray
            array of ag supply requirement for subregions specified

        Note
        ----
        This method is intended to be used during a model simulation (is_for_inquiry=0)

        See Also
        --------
        IWFMModel.get_supply_requirement_ag_elements : Returns the agricultural supply requirement for one or more model elements
        IWFMModel.get_supply_requirement_urban_elements : Returns the urban supply requirement for one or more model elements 
        IWFMModel.get_supply_requirement_urban_subregions : Returns the urban supply requirement for one or more model subregions

        '''
        location_type_id = self.get_location_type_id_subregion()

        # get all subregion IDs
        subregion_ids = self.get_subregion_ids()

        if isinstance(subregions, str):
            if subregions.lower() == 'all':
                subregions = subregion_ids
            else:
                raise ValueError('if subregions is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(subregions, int):
            subregions = np.array([subregions])
        
        # if list or tuple convert to np.ndarray
        if isinstance(subregions, (list, tuple)):
            subregions = np.array(subregions)

        # if subregions were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(subregions, np.ndarray):
            raise TypeError('subregions must be an int, list, tuple, np.ndarray, or "all"')

        # check if all of the provided subregion IDs are valid
        if not np.all(np.isin(subregions, subregion_ids)):
            raise ValueError('One or more subegion IDs provided are invalid')

        # convert subregion IDs to subregion indices
        # add 1 to convert between python indices and fortran indices
        subregion_indices = np.array([np.where(subregion_ids == item)[0][0] for item in subregions]) + 1

        return self._get_supply_requirement_ag(location_type_id, subregion_indices, conversion_factor)

    def _get_supply_requirement_urban(self, location_type_id, locations_list, conversion_factor):
        ''' Returns the urban water supply requirement at a 
        specified set of locations

        Parameters
        ----------
        location_type_id : int
            location type identification number used by IWFM for elements
            or subregions. 

        locations_list : list or np.ndarray
            indices of locations where ag supply requirements are returned

        conversion_factor : float
            factor to convert ag supply requirement from model units to
            desired output units

        Returns
        -------
        np.ndarray
            array of urban supply requirement for locations specified
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetSupplyRequirement_Urb"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetSupplyRequirement_Urb'))
        
        # convert location_type_id to ctypes
        location_type_id = ctypes.c_int(location_type_id)

        # get number of locations
        n_locations = ctypes.c_int(len(locations_list))

        # convert locations_list to ctypes
        locations_list = (ctypes.c_int*n_locations.value)(*locations_list)

        # convert conversion_factor to ctypes
        conversion_factor = ctypes.c_double(conversion_factor)

        # initialize output variables
        urban_supply_requirement = (ctypes.c_double*n_locations.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetSupplyRequirement_Urb(ctypes.byref(location_type_id),
                                                   ctypes.byref(n_locations),
                                                   locations_list,
                                                   ctypes.byref(conversion_factor),
                                                   urban_supply_requirement,
                                                   ctypes.byref(self.status))

        return np.array(urban_supply_requirement)

    def get_supply_requirement_urban_elements(self, elements='all', conversion_factor=1.0):
        ''' Returns the urban supply requirement for one or more model elements

        Parameters
        ----------
        elements : int, list, tuple, np.ndarray, or str='all', default='all'
            one or more element identification numbers used to return 
            the urban supply requirement

        conversion_factor : float, default=1.0
            factor to convert urban supply requirement from model units to
            desired output units

        Returns
        -------
        np.ndarray
            array of urban supply requirement for elements specified

        Note
        ----
        This method is intended to be used during a model simulation (is_for_inquiry=0)

        See Also
        --------
        IWFMModel.get_supply_requirement_ag_elements : Returns the agricultural supply requirement for one or more model elements 
        IWFMModel.get_supply_requirement_ag_subregions : Returns the agricultural supply requirement for one or more model subregions
        IWFMModel.get_supply_requirement_urban_subregions : Returns the urban supply requirement for one or more model subregions

        '''
        location_type_id = self.get_location_type_id_element()

        # get all element IDs
        element_ids = self.get_element_ids()

        if isinstance(elements, str):
            if elements.lower() == 'all':
                elements = element_ids
            else:
                raise ValueError('if elements is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(elements, int):
            elements = np.array([elements])
        
        # if list or tuple convert to np.ndarray
        if isinstance(elements, (list, tuple)):
            elements = np.array(elements)

        # if elements were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(elements, np.ndarray):
            raise TypeError('element must be an int, list, tuple, np.ndarray, or "all"')

        # check if all of the provided element IDs are valid
        if not np.all(np.isin(elements, element_ids)):
            raise ValueError('One or more element IDs provided are invalid')

        # convert element IDs to element indices
        # add 1 to convert between python indices and fortran indices
        element_indices = np.array([np.where(element_ids == item)[0][0] for item in elements]) + 1

        return self._get_supply_requirement_urban(location_type_id, element_indices, conversion_factor)

    def get_supply_requirement_urban_subregions(self, subregions='all', conversion_factor=1.0):
        ''' Returns the urban supply requirement for one or more model subregions

        Parameters
        ----------
        subregions : int, list, tuple, np.ndarray, or str='all', default='all'
            one or more subregion identification numbers used to return 
            the urban supply requirement

        conversion_factor : float, default=1.0
            factor to convert urban supply requirement from model units to
            desired output units

        Returns
        -------
        np.ndarray
            array of urban supply requirement for subregions specified

        Note
        ----
        This method is intended to be used during a model simulation (is_for_inquiry=0)

        See Also
        --------
        IWFMModel.get_supply_requirement_ag_elements : Returns the agricultural supply requirement for one or more model elements
        IWFMModel.get_supply_requirement_ag_subregions : Returns the agricultural supply requirement for one or more model subregions
        IWFMModel.get_supply_requirement_urban_elements : Returns the urban supply requirement for one or more model elements 

        '''
        location_type_id = self.get_location_type_id_subregion()

        # get all subregion IDs
        subregion_ids = self.get_subregion_ids()

        if isinstance(subregions, str):
            if subregions.lower() == 'all':
                subregions = subregion_ids
            else:
                raise ValueError('if subregions is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(subregions, int):
            subregions = np.array([subregions])
        
        # if list or tuple convert to np.ndarray
        if isinstance(subregions, (list, tuple)):
            subregions = np.array(subregions)

        # if subregions were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(subregions, np.ndarray):
            raise TypeError('subregions must be an int, list, tuple, np.ndarray, or "all"')

        # check if all of the provided subregion IDs are valid
        if not np.all(np.isin(subregions, subregion_ids)):
            raise ValueError('One or more subegion IDs provided are invalid')

        # convert subregion IDs to subregion indices
        # add 1 to convert between python indices and fortran indices
        subregion_indices = np.array([np.where(subregion_ids == item)[0][0] for item in subregions]) + 1

        return self._get_supply_requirement_urban(location_type_id, subregion_indices, conversion_factor)

    def _get_supply_shortage_at_origin_ag(self, supply_type_id, supply_location_list, supply_conversion_factor):
        ''' private method returning the supply shortage for agriculture at the destination of those 
        supplies plus any conveyance losses
        
        Parameters
        ----------
        supply_type_id : int
            supply identification number used by IWFM for diversions, 
            well pumping, or element pumping

        supply_location_list : list or np.ndarray
            indices of supplies where ag supply shortages are returned

        supply_conversion_factor : float
            factor to convert agricultural supply shortage from model 
            units to the desired output units

        Returns
        -------
        np.ndarray
            array of agricultural supply shortages for each supply location
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetSupplyShortAtOrigin_Ag"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetSupplyShortAtOrigin_Ag'))
        
        # convert location_type_id to ctypes
        supply_type_id = ctypes.c_int(supply_type_id)

        # get number of locations
        n_locations = ctypes.c_int(len(supply_location_list))

        # convert locations_list to ctypes
        supply_location_list = (ctypes.c_int*n_locations.value)(*supply_location_list)

        # convert conversion_factor to ctypes
        supply_conversion_factor = ctypes.c_double(supply_conversion_factor)

        # initialize output variables
        ag_supply_shortage = (ctypes.c_double*n_locations.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetSupplyShortAtOrigin_Ag(ctypes.byref(supply_type_id),
                                                    ctypes.byref(n_locations),
                                                    supply_location_list,
                                                    ctypes.byref(supply_conversion_factor),
                                                    ag_supply_shortage,
                                                    ctypes.byref(self.status))

        return np.array(ag_supply_shortage)

    def get_ag_diversion_supply_shortage_at_origin(self, diversions='all', conversion_factor=1.0):
        ''' Returns the supply shortage for agricultural diversions at the destination of those 
        supplies plus any conveyance losses
        
        Parameters
        ----------
        diversions : int, list, tuple, np.ndarray, or str='all', default='all'
            indices of diversions where ag supply shortages are returned

        conversion_factor : float, default=1.0
            factor to convert agricultural supply shortage from model 
            units to the desired output units

        Returns
        -------
        np.ndarray
            array of agricultural supply shortages for each diversion location

        Note
        ----
        This method is intended to be used during a model simulation (is_for_inquiry=0)

        See Also
        --------
        IWFMModel.get_ag_well_supply_shortage_at_origin : Returns the supply shortage for agricultural wells at the destination of those supplies plus any conveyance losses
        IWFMModel.get_ag_elempump_supply_shortage_at_origin : Returns the supply shortage for agricultural element pumping at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_diversion_supply_shortage_at_origin : Returns the supply shortage for urban diversions at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_well_supply_shortage_at_origin : Returns the supply shortage for urban wells at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_elempump_supply_shortage_at_origin : Returns the supply shortage for urban element pumping at the destination of those supplies plus any conveyance losses

        '''
        supply_type_id = self.get_supply_type_id_diversion()

        # get all diversion IDs
        diversion_ids = self.get_diversion_ids()

        if isinstance(diversions, str):
            if diversions.lower() == 'all':
                diversions = diversion_ids
            else:
                raise ValueError('if diversions is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(diversions, int):
            diversions = np.array([diversions])
        
        # if list or tuple convert to np.ndarray
        if isinstance(diversions, (list, tuple)):
            diversions = np.array(diversions)

        # if diversions were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(diversions, np.ndarray):
            raise TypeError('diversions must be an int, list, tuple, np.ndarray, or "all"')

        # check if all of the provided diversion IDs are valid
        if not np.all(np.isin(diversions, diversion_ids)):
            raise ValueError('One or more diversion IDs provided are invalid')

        # convert diversion IDs to diversion indices
        # add 1 to convert between python indices and fortran indices
        diversion_indices = np.array([np.where(diversion_ids == item)[0][0] for item in diversions]) + 1

        return self._get_supply_shortage_at_origin_ag(supply_type_id, 
                                                      diversion_indices, 
                                                      conversion_factor)

    def get_ag_well_supply_shortage_at_origin(self, wells='all', conversion_factor=1.0):
        ''' Returns the supply shortage for agricultural wells at the destination of those 
        supplies plus any conveyance losses
        
        Parameters
        ----------
        wells : int, list, tuple, np.ndarray, or str='all', default='all'
            indices of wells where ag supply shortages are returned

        conversion_factor : float, default=1.0
            factor to convert agricultural supply shortage from model 
            units to the desired output units

        Returns
        -------
        np.ndarray
            array of agricultural supply shortages for each well location

        Note
        ----
        This method is intended to be used during a model simulation (is_for_inquiry=0)

        See Also
        --------
        IWFMModel.get_ag_diversion_supply_shortage_at_origin : Returns the supply shortage for agricultural diversions at the destination of those supplies plus any conveyance losses
        IWFMModel.get_ag_elempump_supply_shortage_at_origin : Returns the supply shortage for agricultural element pumping at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_diversion_supply_shortage_at_origin : Returns the supply shortage for urban diversions at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_well_supply_shortage_at_origin : Returns the supply shortage for urban wells at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_elempump_supply_shortage_at_origin : Returns the supply shortage for urban element pumping at the destination of those supplies plus any conveyance losses

        '''
        supply_type_id = self.get_supply_type_id_well()

        # get all well IDs
        well_ids = self.get_well_ids()

        if isinstance(wells, str):
            if wells.lower() == 'all':
                wells = well_ids
            else:
                raise ValueError('if wells is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(wells, int):
            wells = np.array([wells])
        
        # if list or tuple convert to np.ndarray
        if isinstance(wells, (list, tuple)):
            wells = np.array(wells)

        # if wells were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(wells, np.ndarray):
            raise TypeError('wells must be an int, list, tuple, np.ndarray, or "all"')

        # check if all of the provided well IDs are valid
        if not np.all(np.isin(wells, well_ids)):
            raise ValueError('One or more well IDs provided are invalid')

        # convert well IDs to well indices
        # add 1 to convert between python indices and fortran indices
        well_indices = np.array([np.where(well_ids == item)[0][0] for item in wells]) + 1

        return self._get_supply_shortage_at_origin_ag(supply_type_id, 
                                                      well_indices, 
                                                      conversion_factor)

    def get_ag_elempump_supply_shortage_at_origin(self, element_pumps='all', conversion_factor=1.0):
        ''' Returns the supply shortage for agricultural element pumping 
        at the destination of those supplies plus any conveyance losses
        
        Parameters
        ----------
        element_pumps : int, list, tuple, np.ndarray, or str='all', default='all'
            indices of element pumping locations where ag supply shortages are returned

        conversion_factor : float, default=1.0
            factor to convert agricultural supply shortage from model 
            units to the desired output units

        Returns
        -------
        np.ndarray
            array of agricultural supply shortages for each element pumping location

        Note
        ----
        This method is intended to be used during a model simulation (is_for_inquiry=0)

        See Also
        --------
        IWFMModel.get_ag_diversion_supply_shortage_at_origin : Returns the supply shortage for agricultural diversions at the destination of those supplies plus any conveyance losses
        IWFMModel.get_ag_well_supply_shortage_at_origin : Returns the supply shortage for agricultural wells at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_diversion_supply_shortage_at_origin : Returns the supply shortage for urban diversions at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_well_supply_shortage_at_origin : Returns the supply shortage for urban wells at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_elempump_supply_shortage_at_origin : Returns the supply shortage for urban element pumping at the destination of those supplies plus any conveyance losses

        '''
        supply_type_id = self.get_supply_type_id_elempump()

        # get all element pump IDs
        element_pump_ids = self.get_element_pump_ids()

        if isinstance(element_pumps, str):
            if element_pumps.lower() == 'all':
                element_pumps = element_pump_ids
            else:
                raise ValueError('if element_pumps is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(element_pumps, int):
            element_pumps = np.array([element_pumps])
        
        # if list or tuple convert to np.ndarray
        if isinstance(element_pumps, (list, tuple)):
            element_pumps = np.array(element_pumps)

        # if element_pumps were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(element_pumps, np.ndarray):
            raise TypeError('element_pumps must be an int, list, tuple, np.ndarray, or "all"')

        # check if all of the provided element pump IDs are valid
        if not np.all(np.isin(element_pumps, element_pump_ids)):
            raise ValueError('One or more element pump IDs provided are invalid')

        # convert element pump IDs to element pump indices
        # add 1 to convert between python indices and fortran indices
        element_pump_indices = np.array([np.where(element_pump_ids == item)[0][0] for item in element_pumps]) + 1

        return self._get_supply_shortage_at_origin_ag(supply_type_id, 
                                                      element_pump_indices, 
                                                      conversion_factor)

    def _get_supply_shortage_at_origin_urban(self, supply_type_id, supply_location_list, supply_conversion_factor):
        ''' Returns the supply shortage for agriculture at the destination of those 
        supplies plus any conveyance losses
        
        Parameters
        ----------
        supply_type_id : int
            supply identification number used by IWFM for diversions, 
            well pumping, or element pumping

        supply_location_list : list or np.ndarray
            indices of supplies where ag supply shortages are returned

        supply_conversion_factor : float
            factor to convert agricultural supply shortage from model 
            units to the desired output units

        Returns
        -------
        np.ndarray
            array of agricultural supply shortages for each supply location
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetSupplyShortAtOrigin_Urb"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetSupplyShortAtOrigin_Urb'))
        
        # convert location_type_id to ctypes
        supply_type_id = ctypes.c_int(supply_type_id)

        # get number of locations
        n_locations = ctypes.c_int(len(supply_location_list))

        # convert locations_list to ctypes
        supply_location_list = (ctypes.c_int*n_locations.value)(*supply_location_list)

        # convert conversion_factor to ctypes
        supply_conversion_factor = ctypes.c_double(supply_conversion_factor)

        # initialize output variables
        urban_supply_shortage = (ctypes.c_double*n_locations.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetSupplyShortAtOrigin_Urb(ctypes.byref(supply_type_id),
                                                    ctypes.byref(n_locations),
                                                    supply_location_list,
                                                    ctypes.byref(supply_conversion_factor),
                                                    urban_supply_shortage,
                                                    ctypes.byref(self.status))

        return np.array(urban_supply_shortage)

    def get_urban_diversion_supply_shortage_at_origin(self, diversions='all', conversion_factor=1.0):
        ''' Returns the supply shortage for urban diversions at the destination of those 
        supplies plus any conveyance losses
        
        Parameters
        ----------
        diversions : int, list, tuple, np.ndarray, or str='all', default='all'
            indices of diversions where urban supply shortages are returned

        conversion_factor : float, default=1.0
            factor to convert urban supply shortage from model 
            units to the desired output units

        Returns
        -------
        np.ndarray
            array of urban supply shortages for each diversion location

        Note
        ----
        This method is intended to be used during a model simulation (is_for_inquiry=0)

        See Also
        --------
        IWFMModel.get_ag_diversion_supply_shortage_at_origin : Returns the supply shortage for agricultural diversions at the destination of those supplies plus any conveyance losses
        IWFMModel.get_ag_well_supply_shortage_at_origin : Returns the supply shortage for agricultural wells at the destination of those supplies plus any conveyance losses
        IWFMModel.get_ag_elempump_supply_shortage_at_origin : Returns the supply shortage for agricultural element pumping at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_well_supply_shortage_at_origin : Returns the supply shortage for urban wells at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_elempump_supply_shortage_at_origin : Returns the supply shortage for urban element pumping at the destination of those supplies plus any conveyance losses

        '''
        supply_type_id = self.get_supply_type_id_diversion()

        # get all diversion IDs
        diversion_ids = self.get_diversion_ids()

        if isinstance(diversions, str):
            if diversions.lower() == 'all':
                diversions = diversion_ids
            else:
                raise ValueError('if diversions is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(diversions, int):
            diversions = np.array([diversions])
        
        # if list or tuple convert to np.ndarray
        if isinstance(diversions, (list, tuple)):
            diversions = np.array(diversions)

        # if diversions were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(diversions, np.ndarray):
            raise TypeError('diversions must be an int, list, tuple, np.ndarray, or "all"')

        # check if all of the provided diversion IDs are valid
        if not np.all(np.isin(diversions, diversion_ids)):
            raise ValueError('One or more diversion IDs provided are invalid')

        # convert diversion IDs to diversion indices
        # add 1 to convert between python indices and fortran indices
        diversion_indices = np.array([np.where(diversion_ids == item)[0][0] for item in diversions]) + 1

        return self._get_supply_shortage_at_origin_urban(supply_type_id, 
                                                         diversion_indices, 
                                                         conversion_factor)

    def get_urban_well_supply_shortage_at_origin(self, wells='all', conversion_factor=1.0):
        ''' Returns the supply shortage for urban wells at the destination of those 
        supplies plus any conveyance losses
        
        Parameters
        ----------
        wells : int, list, tuple, np.ndarray, or str='all', default='all'
            indices of wells where urban supply shortages are returned

        conversion_factor : float, default=1.0
            factor to convert urban supply shortage from model 
            units to the desired output units

        Returns
        -------
        np.ndarray
            array of urban supply shortages for each well location

        Note
        ----
        This method is intended to be used during a model simulation (is_for_inquiry=0)

        See Also
        --------
        IWFMModel.get_ag_diversion_supply_shortage_at_origin : Returns the supply shortage for agricultural diversions at the destination of those supplies plus any conveyance losses
        IWFMModel.get_ag_well_supply_shortage_at_origin : Returns the supply shortage for agricultural wells at the destination of those supplies plus any conveyance losses
        IWFMModel.get_ag_elempump_supply_shortage_at_origin : Returns the supply shortage for agricultural element pumping at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_diversion_supply_shortage_at_origin : Returns the supply shortage for urban diversions at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_elempump_supply_shortage_at_origin : Returns the supply shortage for urban element pumping at the destination of those supplies plus any conveyance losses

        '''
        supply_type_id = self.get_supply_type_id_well()

        # get all well IDs
        well_ids = self.get_well_ids()

        if isinstance(wells, str):
            if wells.lower() == 'all':
                wells = well_ids
            else:
                raise ValueError('if wells is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(wells, int):
            wells = np.array([wells])
        
        # if list or tuple convert to np.ndarray
        if isinstance(wells, (list, tuple)):
            wells = np.array(wells)

        # if wells were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(wells, np.ndarray):
            raise TypeError('wells must be an int, list, tuple, np.ndarray, or "all"')

        # check if all of the provided well IDs are valid
        if not np.all(np.isin(wells, well_ids)):
            raise ValueError('One or more well IDs provided are invalid')

        # convert well IDs to well indices
        # add 1 to convert between python indices and fortran indices
        well_indices = np.array([np.where(well_ids == item)[0][0] for item in wells]) + 1

        return self._get_supply_shortage_at_origin_urban(supply_type_id, 
                                                         well_indices, 
                                                         conversion_factor)

    def get_urban_elempump_supply_shortage_at_origin(self, element_pumps='all', conversion_factor=1.0):
        ''' Returns the supply shortage for urban element pumping 
        at the destination of those supplies plus any conveyance losses
        
        Parameters
        ----------
        element_pumps : int, list, tuple, np.ndarray, or str='all', default='all'
            indices of element pumping locations where urban supply shortages are returned

        conversion_factor : float, default=1.0
            factor to convert urban supply shortage from model 
            units to the desired output units

        Returns
        -------
        np.ndarray
            array of urban supply shortages for each element pumping location

        Note
        ----
        This method is intended to be used during a model simulation (is_for_inquiry=0)

        See Also
        --------
        IWFMModel.get_ag_diversion_supply_shortage_at_origin : Returns the supply shortage for agricultural diversions at the destination of those supplies plus any conveyance losses
        IWFMModel.get_ag_well_supply_shortage_at_origin : Returns the supply shortage for agricultural wells at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_elempump_supply_shortage_at_origin : Returns the supply shortage for agricultural element pumping at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_diversion_supply_shortage_at_origin : Returns the supply shortage for urban diversions at the destination of those supplies plus any conveyance losses
        IWFMModel.get_urban_well_supply_shortage_at_origin : Returns the supply shortage for urban wells at the destination of those supplies plus any conveyance losses

        '''
        supply_type_id = self.get_supply_type_id_elempump()

        # get all element pump IDs
        element_pump_ids = self.get_element_pump_ids()

        if isinstance(element_pumps, str):
            if element_pumps.lower() == 'all':
                element_pumps = element_pump_ids
            else:
                raise ValueError('if element_pumps is a string, must be "all"')

        # if int convert to np.ndarray
        if isinstance(element_pumps, int):
            element_pumps = np.array([element_pumps])
        
        # if list or tuple convert to np.ndarray
        if isinstance(element_pumps, (list, tuple)):
            element_pumps = np.array(element_pumps)

        # if element_pumps were provided as an int, list, or 
        # np.ndarray they should now all be np.ndarray, so check if np.ndarray
        if not isinstance(element_pumps, np.ndarray):
            raise TypeError('element_pumps must be an int, list, tuple, np.ndarray, or "all"')

        # check if all of the provided element pump IDs are valid
        if not np.all(np.isin(element_pumps, element_pump_ids)):
            raise ValueError('One or more element pump IDs provided are invalid')

        # convert element pump IDs to element pump indices
        # add 1 to convert between python indices and fortran indices
        element_pump_indices = np.array([np.where(element_pump_ids == item)[0][0] for item in element_pumps]) + 1

        return self._get_supply_shortage_at_origin_urban(supply_type_id, 
                                                         element_pump_indices, 
                                                         conversion_factor)

    def _get_names(self, location_type_id):
        ''' Returns the available names for a given location_type

        Parameters
        ----------
        location_type_id : int
            location type identifier used by IWFM to represent model 
            features

        Returns
        -------
        list of strings
            list containing names for the provided location_type_id. Returns
            empty list if no names are available for given feature_type.
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNames"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNames'))

        # convert location type id to ctypes
        location_type_id = ctypes.c_int(location_type_id)

        # get number of locations for specified location type
        if location_type_id.value == 8:
            #num_names = ctypes.c_int(self.get_n_nodes())
            raise NotImplementedError('IWFM does not allow names for groundwater nodes')

        elif location_type_id.value == 2:
            #num_names = ctypes.c_int(self.get_n_elements())
            raise NotImplementedError('IWFM does not allow names for elements')

        elif location_type_id.value == 4:
            num_names = ctypes.c_int(self.get_n_subregions())

        elif location_type_id.value == 7:
            # need to determine if API call exists for this
            raise NotImplementedError('The IWFM Model Object does not include zone definitions')

        elif location_type_id.value == 3:
            #num_names = ctypes.c_int(self.get_n_lakes())
            raise NotImplementedError('IWFM does not allow names for lakes')

        elif location_type_id.value == 1:
            #num_names = ctypes.c_int(self.get_n_stream_nodes())
            raise NotImplementedError('IWFM does not allow names for stream nodes')

        elif location_type_id.value == 11:
            num_names = ctypes.c_int(self.get_n_stream_reaches())

        elif location_type_id.value == 13:
            #num_names = ctypes.c_int(self.get_n_tile_drains())
            raise NotImplementedError('IWFM does not allow names for tile drains')

        elif location_type_id.value == 14:
            #self.get_n_small_watersheds()
            raise NotImplementedError('IWFM does not allow names for small watersheds')

        elif location_type_id.value in [9, 10, 12]:
            num_names = ctypes.c_int(self._get_n_hydrographs(location_type_id.value))

        # initialize output variables
        delimiter_position_array = (ctypes.c_int*num_names.value)()
        names_string_length = ctypes.c_int(30 * num_names.value)
        raw_names_string = ctypes.create_string_buffer(names_string_length.value)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetNames(ctypes.byref(location_type_id),
                                   ctypes.byref(num_names), 
                                   delimiter_position_array,
                                   ctypes.byref(names_string_length),
                                   raw_names_string,
                                   ctypes.byref(self.status))

        return self._string_to_list_by_array(raw_names_string, delimiter_position_array, num_names)

    def get_subregion_names(self):
        ''' Returns the subregions names specified
        in an IWFM model
        
        Returns
        -------
        list
            list of names for each subregion in the model

        See Also
        --------
        IWFMModel.get_subregion_name : Returns the name corresponding to the subregion_id in an IWFM model
        IWFMModel.get_n_subregions : Returns the number of subregions in an IWFM model
        IWFMModel.get_subregion_ids : Returns an array of IDs for subregions identified in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_subregion_names()
        ['Region1 (SR1)', 'Region2 (SR2)']
        >>> model.kill()        
        '''
        location_type_id = self.get_location_type_id_subregion()

        return self._get_names(location_type_id)

    def get_stream_reach_names(self):
        ''' Returns the stream reach names specified in an IWFM model
        
        Returns
        -------
        list
            list of names for each stream reach in the model

        See Also
        --------
        IWFMModel.get_subregion_names : Returns the subregion names specified in an IWFM model
        IWFMModel.get_groundwater_observation_names : Returns the groundwater head observation location names specified in an IWFM model
        IWFMModel.get_stream_observation_names : Returns the stream flow observation location names specified in an IWFM model
        IWFMModel.get_subsidence_observation_names : Returns the subsidence observation location names specified in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stream_reach_names()
        ['Reach2', 'Reach1', 'Reach3']
        >>> model.kill()
        '''
        location_type_id = self.get_location_type_id_streamreach()

        return self._get_names(location_type_id)

    def get_groundwater_observation_names(self):
        ''' Returns the groundwater head observation location names
        specified in an IWFM model

        Returns
        -------
        list
            list of names for each groundwater head observation location

        See Also
        --------
        IWFMModel.get_subregion_names : Returns the subregion names specified in an IWFM model
        IWFMModel.get_stream_reach_names : Returns the stream reach names specified in an IWFM model
        IWFMModel.get_stream_observation_names : Returns the stream flow observation location names specified in an IWFM model
        IWFMModel.get_subsidence_observation_names : Returns the subsidence observation location names specified in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_groundwater_observation_names()
        ['GWHyd1',
         'GWHyd2',
         'GWHyd3',
         'GWHyd4',
         'GWHyd5',
         'GWHyd6',
         'GWHyd7',
         'GWHyd8',
         'GWHyd9',
         'GWHyd10',
         'GWHyd11',
         'GWHyd12',
         'GWHyd13',
         'GWHyd14',
         'GWHyd15',
         'GWHyd16',
         'GWHyd17',
         'GWHyd18',
         'GWHyd19',
         'GWHyd20',
         'GWHyd21',
         'GWHyd22',
         'GWHyd23',
         'GWHyd24',
         'GWHyd25',
         'GWHyd26',
         'GWHyd27',
         'GWHyd28',
         'GWHyd29',
         'GWHyd30',
         'GWHyd31',
         'GWHyd32',
         'GWHyd33',
         'GWHyd34',
         'GWHyd35',
         'GWHyd36',
         'GWHyd37',
         'GWHyd38',
         'GWHyd39',
         'GWHyd40',
         'GWHyd41',
         'GWHyd42']
        >>> model.kill()
        '''
        location_type_id = self.get_location_type_id_gwheadobs()

        return self._get_names(location_type_id)

    def get_stream_observation_names(self):
        ''' Returns the stream flow observation location names specified
        in an IWFM model
        
        Returns
        -------
        list
            list of names for each stream observation location

        See Also
        --------
        IWFMModel.get_subregion_names : Returns the subregion names specified in an IWFM model
        IWFMModel.get_stream_reach_names : Returns the stream reach names specified in an IWFM model
        IWFMModel.get_groundwater_observation_names : Returns the groundwater observation location names specified in an IWFM model
        IWFMModel.get_subsidence_observation_names : Returns the subsidence observation location names specified in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stream_observation_names()
        ['StrmHyd_1',
         'StrmHyd_2',
         'StrmHyd_3',
         'StrmHyd_4',
         'StrmHyd_5',
         'StrmHyd_6',
         'StrmHyd_7',
         'StrmHyd_8',
         'StrmHyd_9',
         'StrmHyd_10',
         'StrmHyd_11',
         'StrmHyd_12',
         'StrmHyd_13',
         'StrmHyd_14',
         'StrmHyd_15',
         'StrmHyd_16',
         'StrmHyd_17',
         'StrmHyd_18',
         'StrmHyd_19',
         'StrmHyd_20',
         'StrmHyd_21',
         'StrmHyd_22',
         'StrmHyd_23']
        >>> model.kill()
        '''
        location_type_id = self.get_location_type_id_streamhydobs()

        return self._get_names(location_type_id)

    def get_subsidence_observation_names(self):
        ''' Returns the subsidence observation location names specified
        in an IWFM model

        Returns
        -------
        list
            list of names for each subsidence observation locations

        See Also
        --------
        IWFMModel.get_subregion_names : Returns the subregion names specified in an IWFM model
        IWFMModel.get_stream_reach_names : Returns the stream reach names specified in an IWFM model
        IWFMModel.get_stream_observation_names : Returns the stream flow observation location names specified in an IWFM model
        IWFMModel.get_groundwater_observation_names : Returns the groundwater observation location names specified in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_subsidence_observation_names()
        ['SubsHyd1', 'SubsHyd2', 'SubsHyd3', 'SubsHyd4', 'SubsHyd5']
        >>> model.kill()
        '''
        location_type_id = self.get_location_type_id_subsidenceobs()

        return self._get_names(location_type_id)

    def get_n_hydrograph_types(self):
        ''' Returns the number of different hydrograph types being
        printed by the IWFM model
        
        Returns
        -------
        int
            number of hydrograph types produced by the model

        See Also
        --------
        IWFMModel.get_hydrograph_type_list : Returns a list of different hydrograph types being printed by the IWFM model
        IWFMModel.get_n_groundwater_hydrographs : Returns the number of groundwater hydrographs specified in an IWFM model
        IWFMModel.get_n_subsidence_hydrographs : Returns the number of subsidence hydrographs specified in an IWFM model
        IWFMModel.get_n_stream_hydrographs : Returns the number of stream flow hydrographs specified in an IWFM model
        IWFMModel.get_n_tile_drain_hydrographs : Returns the number of tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_ids : Returns the IDs for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_ids : Returns the IDs for the subsidence hydrographs specified in an IWFM model
        IWFMModel.get_stream_hydrograph_ids : Returns the IDs for the stream hydrographs specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_ids : Returns the IDs for the tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_coordinates : Returns the x,y-coordinates for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_coordinates : Returns the x,y-coordinates for the subsidence hydrograph locations specified in an IWFM model
        IWFMModel.get_stream_hydrograph_coordinates : Returns the x,y-coordinates for the stream flow observation locations specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_coordinates : Returns the x,y-coordinates for the tile drain observations specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph : Returns the simulated groundwater hydrograph for the provided groundwater hydrograph id
        IWFMModel.get_groundwater_hydrograph_at_node_and_layer : Returns a simulated groundwater hydrograph for a node and layer
        IWFMModel.get_subsidence_hydrograph : Returns the simulated subsidence hydrograph for the provided subsidence hydrograph id
        IWFMModel.get_stream_hydrograph : Returns the simulated stream hydrograph for the provided stream hydrograph id
        IWFMModel.get_tile_drain_hydrograph : Returns the simulated tile drain hydrograph for the provided tile drain hydrograph id

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_hydrograph_types()
        5
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNHydrographTypes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNHydrographTypes'))

        # initialize output variables
        n_hydrograph_types = ctypes.c_int(0)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetNHydrographTypes(ctypes.byref(n_hydrograph_types),
                                              ctypes.byref(self.status))

        return n_hydrograph_types.value

    def get_hydrograph_type_list(self):
        ''' Returns a list of different hydrograph types being printed
        by the IWFM model 
        
        Returns
        -------
        dict
            keys are different hydrograph types printed by the IWFM model
            values are corresponding hydrograph type ids

        See Also
        --------
        IWFMModel.get_n_hydrograph_types : Returns the number of different hydrograph types being printed by the IWFM model
        IWFMModel.get_n_groundwater_hydrographs : Returns the number of groundwater hydrographs specified in an IWFM model
        IWFMModel.get_n_subsidence_hydrographs : Returns the number of subsidence hydrographs specified in an IWFM model
        IWFMModel.get_n_stream_hydrographs : Returns the number of stream flow hydrographs specified in an IWFM model
        IWFMModel.get_n_tile_drain_hydrographs : Returns the number of tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_ids : Returns the IDs for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_ids : Returns the IDs for the subsidence hydrographs specified in an IWFM model
        IWFMModel.get_stream_hydrograph_ids : Returns the IDs for the stream hydrographs specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_ids : Returns the IDs for the tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_coordinates : Returns the x,y-coordinates for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_coordinates : Returns the x,y-coordinates for the subsidence hydrograph locations specified in an IWFM model
        IWFMModel.get_stream_hydrograph_coordinates : Returns the x,y-coordinates for the stream flow observation locations specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_coordinates : Returns the x,y-coordinates for the tile drain observations specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph : Returns the simulated groundwater hydrograph for the provided groundwater hydrograph id
        IWFMModel.get_groundwater_hydrograph_at_node_and_layer : Returns a simulated groundwater hydrograph for a node and layer
        IWFMModel.get_subsidence_hydrograph : Returns the simulated subsidence hydrograph for the provided subsidence hydrograph id
        IWFMModel.get_stream_hydrograph : Returns the simulated stream hydrograph for the provided stream hydrograph id
        IWFMModel.get_tile_drain_hydrograph : Returns the simulated tile drain hydrograph for the provided tile drain hydrograph id

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_hydrograph_type_list()
        {'Groundwater hydrograph': 9,
         'Groundwater hydrograph at node and layer': 8,
         'Subsidence hydrograph': 10,
         'Tile drain hydrograph': 13,
         'Stream hydrograph (flow)': 12}
        >>> model.kill()
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetHydrographTypeList"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetHydrographTypeList'))

        # get number of hydrograph types
        n_hydrograph_types = ctypes.c_int(self.get_n_hydrograph_types())

        # set length of hydrograph type list string
        length_hydrograph_type_list = ctypes.c_int(3000)

        # initialize output variables
        raw_hydrograph_type_string = ctypes.create_string_buffer(length_hydrograph_type_list.value)
        delimiter_position_array = (ctypes.c_int*n_hydrograph_types.value)()
        hydrograph_location_type_list = (ctypes.c_int*n_hydrograph_types.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetHydrographTypeList(ctypes.byref(n_hydrograph_types),
                                                delimiter_position_array,
                                                ctypes.byref(length_hydrograph_type_list),
                                                raw_hydrograph_type_string,
                                                hydrograph_location_type_list,
                                                ctypes.byref(self.status))

        hydrograph_type_list = self._string_to_list_by_array(raw_hydrograph_type_string, delimiter_position_array, n_hydrograph_types)

        return dict(zip(hydrograph_type_list, np.array(hydrograph_location_type_list)))

    def _get_n_hydrographs(self, location_type_id):
        '''private method returning the number of hydrographs for a given IWFM feature type
        
        Parameters
        ----------
        location_type_id : int
            integer id used internally to IWFM for location types

        Returns
        -------
        int
            number of hydrographs for the provided feature type

        Notes
        -----
        this method only works with location_type_ids
        - 9 (groundwater hydrographs)
        - 10 (subsidence hydrographs)
        - 12 (stream hydrographs)
        - 13 (tile drains)
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNHydrographs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNHydrographs'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        n_hydrographs = ctypes.c_int(0)

        # convert location_type_id to ctypes
        location_type_id = ctypes.c_int(location_type_id)

        self.dll.IW_Model_GetNHydrographs(ctypes.byref(location_type_id), 
                                          ctypes.byref(n_hydrographs), 
                                          ctypes.byref(self.status))

        return n_hydrographs.value

    def get_n_groundwater_hydrographs(self):
        ''' Returns the number of groundwater hydrographs specified in
        an IWFM model

        Returns
        -------
        int
            number of groundwater hydrographs

        See Also
        --------
        IWFMModel.get_n_hydrograph_types : Returns the number of different hydrograph types being printed by the IWFM model
        IWFMModel.get_hydrograph_type_list : Returns a list of different hydrograph types being printed by the IWFM model
        IWFMModel.get_n_subsidence_hydrographs : Returns the number of subsidence hydrographs specified in an IWFM model
        IWFMModel.get_n_stream_hydrographs : Returns the number of stream flow hydrographs specified in an IWFM model
        IWFMModel.get_n_tile_drain_hydrographs : Returns the number of tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_ids : Returns the IDs for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_ids : Returns the IDs for the subsidence hydrographs specified in an IWFM model
        IWFMModel.get_stream_hydrograph_ids : Returns the IDs for the stream hydrographs specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_ids : Returns the IDs for the tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_coordinates : Returns the x,y-coordinates for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_coordinates : Returns the x,y-coordinates for the subsidence hydrograph locations specified in an IWFM model
        IWFMModel.get_stream_hydrograph_coordinates : Returns the x,y-coordinates for the stream flow observation locations specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_coordinates : Returns the x,y-coordinates for the tile drain observations specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph : Returns the simulated groundwater hydrograph for the provided groundwater hydrograph id
        IWFMModel.get_groundwater_hydrograph_at_node_and_layer : Returns a simulated groundwater hydrograph for a node and layer
        IWFMModel.get_subsidence_hydrograph : Returns the simulated subsidence hydrograph for the provided subsidence hydrograph id
        IWFMModel.get_stream_hydrograph : Returns the simulated stream hydrograph for the provided stream hydrograph id
        IWFMModel.get_tile_drain_hydrograph : Returns the simulated tile drain hydrograph for the provided tile drain hydrograph id

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_groundwater_hydrographs()
        42
        >>> model.kill()
        '''
        location_type_id = self.get_location_type_id_gwheadobs()

        return self._get_n_hydrographs(location_type_id)

    def get_n_subsidence_hydrographs(self):
        ''' Returns the number of subsidence hydrographs specified in 
        an IWFM model

        Returns
        -------
        int
            number of subsidence hydrographs

        See Also
        --------
        IWFMModel.get_n_hydrograph_types : Returns the number of different hydrograph types being printed by the IWFM model
        IWFMModel.get_hydrograph_type_list : Returns a list of different hydrograph types being printed by the IWFM model
        IWFMModel.get_n_groundwater_hydrographs : Returns the number of groundwater hydrographs specified in an IWFM model
        IWFMModel.get_n_stream_hydrographs : Returns the number of stream flow hydrographs specified in an IWFM model
        IWFMModel.get_n_tile_drain_hydrographs : Returns the number of tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_ids : Returns the IDs for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_ids : Returns the IDs for the subsidence hydrographs specified in an IWFM model
        IWFMModel.get_stream_hydrograph_ids : Returns the IDs for the stream hydrographs specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_ids : Returns the IDs for the tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_coordinates : Returns the x,y-coordinates for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_coordinates : Returns the x,y-coordinates for the subsidence hydrograph locations specified in an IWFM model
        IWFMModel.get_stream_hydrograph_coordinates : Returns the x,y-coordinates for the stream flow observation locations specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_coordinates : Returns the x,y-coordinates for the tile drain observations specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph : Returns the simulated groundwater hydrograph for the provided groundwater hydrograph id
        IWFMModel.get_groundwater_hydrograph_at_node_and_layer : Returns a simulated groundwater hydrograph for a node and layer
        IWFMModel.get_subsidence_hydrograph : Returns the simulated subsidence hydrograph for the provided subsidence hydrograph id
        IWFMModel.get_stream_hydrograph : Returns the simulated stream hydrograph for the provided stream hydrograph id
        IWFMModel.get_tile_drain_hydrograph : Returns the simulated tile drain hydrograph for the provided tile drain hydrograph id

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_subsidence_hydrographs()
        5
        >>> model.kill()
        '''
        location_type_id = self.get_location_type_id_subsidenceobs()

        return self._get_n_hydrographs(location_type_id)

    def get_n_stream_hydrographs(self):
        ''' Returns the number of stream flow hydrographs specified in
        an IWFM model

        Returns
        -------
        int
            number of stream hydrographs

        See Also
        --------
        IWFMModel.get_n_hydrograph_types : Returns the number of different hydrograph types being printed by the IWFM model
        IWFMModel.get_hydrograph_type_list : Returns a list of different hydrograph types being printed by the IWFM model
        IWFMModel.get_n_groundwater_hydrographs : Returns the number of groundwater hydrographs specified in an IWFM model
        IWFMModel.get_n_subsidence_hydrographs : Returns the number of subsidence hydrographs specified in an IWFM model
        IWFMModel.get_n_tile_drain_hydrographs : Returns the number of tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_ids : Returns the IDs for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_ids : Returns the IDs for the subsidence hydrographs specified in an IWFM model
        IWFMModel.get_stream_hydrograph_ids : Returns the IDs for the stream hydrographs specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_ids : Returns the IDs for the tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_coordinates : Returns the x,y-coordinates for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_coordinates : Returns the x,y-coordinates for the subsidence hydrograph locations specified in an IWFM model
        IWFMModel.get_stream_hydrograph_coordinates : Returns the x,y-coordinates for the stream flow observation locations specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_coordinates : Returns the x,y-coordinates for the tile drain observations specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph : Returns the simulated groundwater hydrograph for the provided groundwater hydrograph id
        IWFMModel.get_groundwater_hydrograph_at_node_and_layer : Returns a simulated groundwater hydrograph for a node and layer
        IWFMModel.get_subsidence_hydrograph : Returns the simulated subsidence hydrograph for the provided subsidence hydrograph id
        IWFMModel.get_stream_hydrograph : Returns the simulated stream hydrograph for the provided stream hydrograph id
        IWFMModel.get_tile_drain_hydrograph : Returns the simulated tile drain hydrograph for the provided tile drain hydrograph id

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_stream_hydrographs()
        23
        >>> model.kill()
        '''
        location_type_id = self.get_location_type_id_streamhydobs()

        return self._get_n_hydrographs(location_type_id)

    def get_n_tile_drain_hydrographs(self):
        ''' Returns the number of tile drain hydrographs specified in 
        an IWFM model

        Returns
        -------
        int
            number of tile drain hydrographs

        See Also
        --------
        IWFMModel.get_n_hydrograph_types : Returns the number of different hydrograph types being printed by the IWFM model
        IWFMModel.get_hydrograph_type_list : Returns a list of different hydrograph types being printed by the IWFM model
        IWFMModel.get_n_groundwater_hydrographs : Returns the number of groundwater hydrographs specified in an IWFM model
        IWFMModel.get_n_subsidence_hydrographs : Returns the number of subsidence hydrographs specified in an IWFM model
        IWFMModel.get_n_stream_hydrographs : Returns the number of stream flow hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_ids : Returns the IDs for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_ids : Returns the IDs for the subsidence hydrographs specified in an IWFM model
        IWFMModel.get_stream_hydrograph_ids : Returns the IDs for the stream hydrographs specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_ids : Returns the IDs for the tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_coordinates : Returns the x,y-coordinates for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_coordinates : Returns the x,y-coordinates for the subsidence hydrograph locations specified in an IWFM model
        IWFMModel.get_stream_hydrograph_coordinates : Returns the x,y-coordinates for the stream flow observation locations specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_coordinates : Returns the x,y-coordinates for the tile drain observations specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph : Returns the simulated groundwater hydrograph for the provided groundwater hydrograph id
        IWFMModel.get_groundwater_hydrograph_at_node_and_layer : Returns a simulated groundwater hydrograph for a node and layer
        IWFMModel.get_subsidence_hydrograph : Returns the simulated subsidence hydrograph for the provided subsidence hydrograph id
        IWFMModel.get_stream_hydrograph : Returns the simulated stream hydrograph for the provided stream hydrograph id
        IWFMModel.get_tile_drain_hydrograph : Returns the simulated tile drain hydrograph for the provided tile drain hydrograph id

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_n_tile_drain_hydrographs()
        6
        >>> model.kill()
        '''
        location_type_id = self.get_location_type_id_tiledrainobs()

        return self._get_n_hydrographs(location_type_id)

    def _get_hydrograph_ids(self, location_type_id):
        '''private method returning the ids of the hydrographs for a 
        provided location type

        Parameters
        ----------
        location_type_id : int
            integer id used internally to IWFM for location types

        Returns
        -------
        np.array
            integer array containing ids for hydrographs of the given location type

        Notes
        -----
        this method only works with location_type_ids
        - 9 (groundwater hydrographs)
        - 10 (subsidence hydrographs)
        - 12 (stream hydrographs)
        - 13 (tile drains)
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetHydrographIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetHydrographIDs'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # convert location_type_id to ctypes
        location_type_id = ctypes.c_int(location_type_id)

        # get number of hydrographs
        num_hydrographs = ctypes.c_int(self._get_n_hydrographs(location_type_id.value))

        
        if num_hydrographs.value != 0:
            
            # initialize output variables
            hydrograph_ids = (ctypes.c_int*num_hydrographs.value)()

            self.dll.IW_Model_GetHydrographIDs(ctypes.byref(location_type_id),
                                               ctypes.byref(num_hydrographs),
                                               hydrograph_ids,
                                               ctypes.byref(self.status))
        
            return np.array(hydrograph_ids)

    def get_groundwater_hydrograph_ids(self):
        ''' Returns the ids for the groundwater hydrographs specified
        in an IWFM model

        Returns
        -------
        np.ndarray
            integer array of ids for groundwater hydrographs

        See Also
        --------
        IWFMModel.get_n_hydrograph_types : Returns the number of different hydrograph types being printed by the IWFM model
        IWFMModel.get_hydrograph_type_list : Returns a list of different hydrograph types being printed by the IWFM model
        IWFMModel.get_n_groundwater_hydrographs : Returns the number of groundwater hydrographs specified in an IWFM model
        IWFMModel.get_n_subsidence_hydrographs : Returns the number of subsidence hydrographs specified in an IWFM model
        IWFMModel.get_n_stream_hydrographs : Returns the number of stream flow hydrographs specified in an IWFM model
        IWFMModel.get_n_tile_drain_hydrographs : Returns the number of tile drain hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_ids : Returns the IDs for the subsidence hydrographs specified in an IWFM model
        IWFMModel.get_stream_hydrograph_ids : Returns the IDs for the stream hydrographs specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_ids : Returns the IDs for the tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_coordinates : Returns the x,y-coordinates for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_coordinates : Returns the x,y-coordinates for the subsidence hydrograph locations specified in an IWFM model
        IWFMModel.get_stream_hydrograph_coordinates : Returns the x,y-coordinates for the stream flow observation locations specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_coordinates : Returns the x,y-coordinates for the tile drain observations specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph : Returns the simulated groundwater hydrograph for the provided groundwater hydrograph id
        IWFMModel.get_groundwater_hydrograph_at_node_and_layer : Returns a simulated groundwater hydrograph for a node and layer
        IWFMModel.get_subsidence_hydrograph : Returns the simulated subsidence hydrograph for the provided subsidence hydrograph id
        IWFMModel.get_stream_hydrograph : Returns the simulated stream hydrograph for the provided stream hydrograph id
        IWFMModel.get_tile_drain_hydrograph : Returns the simulated tile drain hydrograph for the provided tile drain hydrograph id

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_groundwater_hydrograph_ids()
        array([ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17,
               18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34,
               35, 36, 37, 38, 39, 40, 41, 42])
        >>> model.kill()
        '''
        # get the location type id for groundwater head observations
        location_type_id = self.get_location_type_id_gwheadobs()

        return self._get_hydrograph_ids(location_type_id)

    def get_subsidence_hydrograph_ids(self):
        ''' Returns the ids for the subsidence hydrographs specified
        in an IWFM model
        
        Returns
        -------
        np.ndarray
            integer array of ids for subsidence hydrographs

        See Also
        --------
        IWFMModel.get_n_hydrograph_types : Returns the number of different hydrograph types being printed by the IWFM model
        IWFMModel.get_hydrograph_type_list : Returns a list of different hydrograph types being printed by the IWFM model
        IWFMModel.get_n_groundwater_hydrographs : Returns the number of groundwater hydrographs specified in an IWFM model
        IWFMModel.get_n_subsidence_hydrographs : Returns the number of subsidence hydrographs specified in an IWFM model
        IWFMModel.get_n_stream_hydrographs : Returns the number of stream flow hydrographs specified in an IWFM model
        IWFMModel.get_n_tile_drain_hydrographs : Returns the number of tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_ids : Returns the IDs for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_stream_hydrograph_ids : Returns the IDs for the stream hydrographs specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_ids : Returns the IDs for the tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_coordinates : Returns the x,y-coordinates for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_coordinates : Returns the x,y-coordinates for the subsidence hydrograph locations specified in an IWFM model
        IWFMModel.get_stream_hydrograph_coordinates : Returns the x,y-coordinates for the stream flow observation locations specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_coordinates : Returns the x,y-coordinates for the tile drain observations specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph : Returns the simulated groundwater hydrograph for the provided groundwater hydrograph id
        IWFMModel.get_groundwater_hydrograph_at_node_and_layer : Returns a simulated groundwater hydrograph for a node and layer
        IWFMModel.get_subsidence_hydrograph : Returns the simulated subsidence hydrograph for the provided subsidence hydrograph id
        IWFMModel.get_stream_hydrograph : Returns the simulated stream hydrograph for the provided stream hydrograph id
        IWFMModel.get_tile_drain_hydrograph : Returns the simulated tile drain hydrograph for the provided tile drain hydrograph id

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_subsidence_hydrograph_ids()
        array([1, 2, 3, 4, 5])
        >>> model.kill()
        '''
        # get the location type id for groundwater head observations
        location_type_id = self.get_location_type_id_subsidenceobs()

        return self._get_hydrograph_ids(location_type_id)

    def get_stream_hydrograph_ids(self):
        ''' Returns the ids for the stream hydrographs specified
        in an IWFM model
        
        Returns
        -------
        np.ndarray
            integer array of ids for stream hydrographs

        See Also
        --------
        IWFMModel.get_n_hydrograph_types : Returns the number of different hydrograph types being printed by the IWFM model
        IWFMModel.get_hydrograph_type_list : Returns a list of different hydrograph types being printed by the IWFM model
        IWFMModel.get_n_groundwater_hydrographs : Returns the number of groundwater hydrographs specified in an IWFM model
        IWFMModel.get_n_subsidence_hydrographs : Returns the number of subsidence hydrographs specified in an IWFM model
        IWFMModel.get_n_stream_hydrographs : Returns the number of stream flow hydrographs specified in an IWFM model
        IWFMModel.get_n_tile_drain_hydrographs : Returns the number of tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_ids : Returns the IDs for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_ids : Returns the IDs for the subsidence hydrographs specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_ids : Returns the IDs for the tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_coordinates : Returns the x,y-coordinates for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_coordinates : Returns the x,y-coordinates for the subsidence hydrograph locations specified in an IWFM model
        IWFMModel.get_stream_hydrograph_coordinates : Returns the x,y-coordinates for the stream flow observation locations specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_coordinates : Returns the x,y-coordinates for the tile drain observations specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph : Returns the simulated groundwater hydrograph for the provided groundwater hydrograph id
        IWFMModel.get_groundwater_hydrograph_at_node_and_layer : Returns a simulated groundwater hydrograph for a node and layer
        IWFMModel.get_subsidence_hydrograph : Returns the simulated subsidence hydrograph for the provided subsidence hydrograph id
        IWFMModel.get_stream_hydrograph : Returns the simulated stream hydrograph for the provided stream hydrograph id
        IWFMModel.get_tile_drain_hydrograph : Returns the simulated tile drain hydrograph for the provided tile drain hydrograph id

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_stream_hydrograph_ids()
        array([ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17,
               18, 19, 20, 21, 22, 23])
        >>> model.kill()
        '''
        # get the location type id for stream flow observations
        location_type_id = self.get_location_type_id_streamhydobs()

        return self._get_hydrograph_ids(location_type_id)

    def get_tile_drain_hydrograph_ids(self):
        ''' Returns the ids for the tile drain hydrographs specified
        in an IWFM model
        
        Returns
        -------
        np.ndarray
            integer array of ids for tile drain hydrographs

        See Also
        --------
        IWFMModel.get_n_hydrograph_types : Returns the number of different hydrograph types being printed by the IWFM model
        IWFMModel.get_hydrograph_type_list : Returns a list of different hydrograph types being printed by the IWFM model
        IWFMModel.get_n_groundwater_hydrographs : Returns the number of groundwater hydrographs specified in an IWFM model
        IWFMModel.get_n_subsidence_hydrographs : Returns the number of subsidence hydrographs specified in an IWFM model
        IWFMModel.get_n_stream_hydrographs : Returns the number of stream flow hydrographs specified in an IWFM model
        IWFMModel.get_n_tile_drain_hydrographs : Returns the number of tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_ids : Returns the IDs for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_ids : Returns the IDs for the subsidence hydrographs specified in an IWFM model
        IWFMModel.get_stream_hydrograph_ids : Returns the IDs for the stream hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_coordinates : Returns the x,y-coordinates for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_coordinates : Returns the x,y-coordinates for the subsidence hydrograph locations specified in an IWFM model
        IWFMModel.get_stream_hydrograph_coordinates : Returns the x,y-coordinates for the stream flow observation locations specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_coordinates : Returns the x,y-coordinates for the tile drain observations specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph : Returns the simulated groundwater hydrograph for the provided groundwater hydrograph id
        IWFMModel.get_groundwater_hydrograph_at_node_and_layer : Returns a simulated groundwater hydrograph for a node and layer
        IWFMModel.get_subsidence_hydrograph : Returns the simulated subsidence hydrograph for the provided subsidence hydrograph id
        IWFMModel.get_stream_hydrograph : Returns the simulated stream hydrograph for the provided stream hydrograph id
        IWFMModel.get_tile_drain_hydrograph : Returns the simulated tile drain hydrograph for the provided tile drain hydrograph id

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_tile_drain_hydrograph_ids()
        array([ 1,  4,  7, 10, 13, 16])
        >>> model.kill()
        '''
        # get the location type id for tile drain observations
        location_type_id = self.get_location_type_id_tiledrainobs()

        return self._get_hydrograph_ids(location_type_id)

    def _get_hydrograph_coordinates(self, location_type_id):
        ''' private method returning the hydrograph coordinates for a provided feature type

        Parameters
        ----------
        location_type_id : int
            integer id used internally to IWFM for location types

        Returns
        -------
        tuple : length 2
            index 0: np.array of x-coordinates of hydrographs
            index 1: np.array of y-coordinates of hydrographs

        Notes
        -----
        this method only works with location_type_ids
        - 9 (groundwater hydrographs)
        - 10 (subsidence hydrographs)
        - 12 (stream hydrographs)
        - 13 (tile drains)
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetHydrographCoordinates"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetHydrographCoordinates'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # convert location_type_id to ctypes
        location_type_id = ctypes.c_int(location_type_id)

        # get number of hydrographs
        num_hydrographs = ctypes.c_int(self._get_n_hydrographs(location_type_id.value))

        if num_hydrographs.value != 0:
            
            # initialize output variables
            x = (ctypes.c_double*num_hydrographs.value)()
            y = (ctypes.c_double*num_hydrographs.value)() 

            self.dll.IW_Model_GetHydrographCoordinates(ctypes.byref(location_type_id), 
                                                       ctypes.byref(num_hydrographs), 
                                                       x, 
                                                       y, 
                                                       ctypes.byref(self.status))

            return np.array(x), np.array(y)

    def get_groundwater_hydrograph_coordinates(self):
        ''' Returns the x,y-coordinates for the groundwater hydrographs
        specified in an IWFM model

        Returns
        -------
        tuple
            np.ndarray of x-coordinates
            np.ndarray of y-coordinates

        See Also
        --------
        IWFMModel.get_n_hydrograph_types : Returns the number of different hydrograph types being printed by the IWFM model
        IWFMModel.get_hydrograph_type_list : Returns a list of different hydrograph types being printed by the IWFM model
        IWFMModel.get_n_groundwater_hydrographs : Returns the number of groundwater hydrographs specified in an IWFM model
        IWFMModel.get_n_subsidence_hydrographs : Returns the number of subsidence hydrographs specified in an IWFM model
        IWFMModel.get_n_stream_hydrographs : Returns the number of stream flow hydrographs specified in an IWFM model
        IWFMModel.get_n_tile_drain_hydrographs : Returns the number of tile drain hydrographs specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph_ids : Returns the IDs for the groundwater hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_ids : Returns the IDs for the subsidence hydrographs specified in an IWFM model
        IWFMModel.get_stream_hydrograph_ids : Returns the IDs for the stream hydrographs specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_ids : Returns the IDs for the tile drain hydrographs specified in an IWFM model
        IWFMModel.get_subsidence_hydrograph_coordinates : Returns the x,y-coordinates for the subsidence hydrograph locations specified in an IWFM model
        IWFMModel.get_stream_hydrograph_coordinates : Returns the x,y-coordinates for the stream flow observation locations specified in an IWFM model
        IWFMModel.get_tile_drain_hydrograph_coordinates : Returns the x,y-coordinates for the tile drain observations specified in an IWFM model
        IWFMModel.get_groundwater_hydrograph : Returns the simulated groundwater hydrograph for the provided groundwater hydrograph id
        IWFMModel.get_groundwater_hydrograph_at_node_and_layer : Returns a simulated groundwater hydrograph for a node and layer
        IWFMModel.get_subsidence_hydrograph : Returns the simulated subsidence hydrograph for the provided subsidence hydrograph id
        IWFMModel.get_stream_hydrograph : Returns the simulated stream hydrograph for the provided stream hydrograph id
        IWFMModel.get_tile_drain_hydrograph : Returns the simulated tile drain hydrograph for the provided tile drain hydrograph id

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> x, y = model.get_groundwater_hydrograph_coordinates()
        >>> x
        array([1883179.2, 1883179.2, 1883179.2, 1883179.2, 1883179.2, 1883179.2,
               1883179.2, 1883179.2, 1883179.2, 1883179.2, 1883179.2, 1883179.2,
               1883179.2, 1883179.2, 1883179.2, 1883179.2, 1883179.2, 1883179.2,
               1883179.2, 1883179.2, 1883179.2, 1883179.2, 1883179.2, 1883179.2,
               1883179.2, 1883179.2, 1883179.2, 1883179.2, 1883179.2, 1883179.2,
               1883179.2, 1883179.2, 1883179.2, 1883179.2, 1883179.2, 1883179.2,
               1883179.2, 1883179.2, 1883179.2, 1883179.2, 1883179.2, 1883179.2])
        >>> y
        array([14566752. , 14560190.4, 14553628.8, 14547067.2, 14540505.6,
               14533944. , 14527382.4, 14520820.8, 14514259.2, 14507697.6,
               14501136. , 14494574.4, 14488012.8, 14481451.2, 14474889.6,
               14468328. , 14461766.4, 14455204.8, 14448643.2, 14442081.6,
               14435520. , 14566752. , 14560190.4, 14553628.8, 14547067.2,
               14540505.6, 14533944. , 14527382.4, 14520820.8, 14514259.2,
               14507697.6, 14501136. , 14494574.4, 14488012.8, 14481451.2,
               14474889.6, 14468328. , 14461766.4, 14455204.8, 14448643.2,
               14442081.6, 14435520. ])
        >>> model.kill()
        '''
        location_type_id = self.get_location_type_id_gwheadobs()

        return self._get_hydrograph_coordinates(location_type_id)

    def get_subsidence_hydrograph_coordinates(self):
        ''' Returns the x,y-coordinates for the subsidence hydrograph
        locations specified in an IWFM model

        Returns
        -------
        tuple
            np.ndarray of x-coordinates
            np.ndarray of y-coordinates
        '''
        location_type_id = self.get_location_type_id_subsidenceobs()

        return self._get_hydrograph_coordinates(location_type_id)

    def get_stream_hydrograph_coordinates(self):
        ''' Returns the x,y-coordinates for the stream flow observation
        locations specified in an IWFM model

        Returns
        -------
        tuple
            np.ndarray of x-coordinates
            np.ndarray of y-coordinates
        '''
        location_type_id = self.get_location_type_id_streamhydobs()

        return self._get_hydrograph_coordinates(location_type_id)

    def get_tile_drain_hydrograph_coordinates(self):
        ''' Returns the x,y-coordinates for the tile drain observations
        specified in an IWFM model

        Returns
        -------
        tuple
            np.ndarray of x-coordinates
            np.ndarray of y-coordinates
        '''
        location_type_id = self.get_location_type_id_tiledrainobs()

        return self._get_hydrograph_coordinates(location_type_id)

    def _get_hydrograph(self, hydrograph_type, hydrograph_id, layer_number, 
                        begin_date, end_date, length_conversion_factor, 
                        volume_conversion_factor):
        ''' private method returning a simulated hydrograph for a selected hydrograph type and hydrograph index 
        
        Parameters
        ----------
        hydrograph_type : int
            one of the available hydrograph types for the model retrieved using
            get_hydrograph_type_list method
            
        hydrograph_id : int
            id for hydrograph being retrieved
            
        layer_number : int
            layer number for returning hydrograph. only used for groundwater hydrograph
            at node and layer
            
        begin_date : str
            IWFM-style date for the beginning date of the simulated groundwater heads

        end_date : str
            IWFM-style date for the end date of the simulated groundwater heads

        length_conversion_factor : float, int
            hydrographs with units of length are multiplied by this
            value to convert simulation units to desired output units
            
        volume_conversion_factor : float, int
            hydrographs with units of volume are multiplied by this
            value to convert simulation units to desired output units

        Returns
        -------
        np.arrays
            1-D array of dates
            1-D array of hydrograph values
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetHydrograph"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. ' 
                                 'Check for an updated version'.format('IW_Model_GetHydrograph'))

        # check that layer_number is an integer
        if not isinstance(layer_number, int):
            raise TypeError('layer_number must be an integer, '
                             'value {} provided is of type {}'.format(layer_number, type(layer_number)))

        # check layer number is valid
        n_layers = self.get_n_layers()
        if layer_number not in range(1,n_layers+1):
            raise ValueError("Layer Number provided {} is not valid. "
                             "Model only has {} layers".format(layer_number, n_layers))

        # handle start and end dates
        # get time specs
        dates_list, output_interval = self.get_time_specs()
        
        if begin_date is None:
            begin_date = dates_list[0]
        else:
            self._validate_iwfm_date(begin_date)

            if begin_date not in dates_list:
                raise ValueError('begin_date was not recognized as a model time step. use IWFMModel.get_time_specs() method to check.')
        
        if end_date is None:
            end_date = dates_list[-1]
        else:
            self._validate_iwfm_date(end_date)

            if end_date not in dates_list:
                raise ValueError('end_date was not found in the Simulation file. use IWFMModel.get_time_specs() method to check.')

        if self.is_date_greater(begin_date, end_date):
            raise ValueError('end_date must occur after begin_date')
                
        # check that length conversion factor is a number
        if not isinstance(length_conversion_factor, (int, float)):
            raise TypeError('length_conversion_factor must be a number. '
                             'value {} provides is of type {}'.format(length_conversion_factor, 
                                                                      type(length_conversion_factor)))

        # check that volume conversion factor is a number
        if not isinstance(volume_conversion_factor, (int, float)):
            raise TypeError('volume_conversion_factor must be a number. '
                             'value {} provides is of type {}'.format(volume_conversion_factor, 
                                                                      type(volume_conversion_factor)))
        
        # convert hydrograph type to ctypes
        hydrograph_type = ctypes.c_int(hydrograph_type)

        # convert hydrograph_id to ctypes
        hydrograph_id = ctypes.c_int(hydrograph_id)

        # convert layer number to ctypes
        layer_number = ctypes.c_int(layer_number)

        # get number of time intervals
        num_time_intervals = ctypes.c_int(self.get_n_intervals(begin_date, end_date, output_interval))

        # convert output interval to ctypes
        output_interval = ctypes.create_string_buffer(output_interval.encode('utf-8'))

        # get length of time interval
        length_time_interval = ctypes.c_int(ctypes.sizeof(output_interval))

        # convert dates to ctypes
        begin_date = ctypes.create_string_buffer(begin_date.encode('utf-8'))
        end_date = ctypes.create_string_buffer(end_date.encode('utf-8'))

        # get length of begin_date and end_date strings
        length_date_string = ctypes.c_int(ctypes.sizeof(begin_date))

        # convert length_conversion_factor to ctypes
        length_conversion_factor = ctypes.c_double(length_conversion_factor)

        # convert volume_conversion_factor to ctypes
        volume_conversion_factor = ctypes.c_double(volume_conversion_factor)

        # initialize output variables
        output_dates = (ctypes.c_double*num_time_intervals.value)()
        output_hydrograph = (ctypes.c_double*num_time_intervals.value)()
        data_unit_type_id = ctypes.c_int(0)
        num_time_steps = ctypes.c_int(0)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetHydrograph(ctypes.byref(hydrograph_type),
                                        ctypes.byref(hydrograph_id),
                                        ctypes.byref(layer_number),
                                        ctypes.byref(length_date_string),
                                        begin_date,
                                        end_date,
                                        ctypes.byref(length_time_interval),
                                        output_interval,
                                        ctypes.byref(length_conversion_factor),
                                        ctypes.byref(volume_conversion_factor),
                                        ctypes.byref(num_time_intervals),
                                        output_dates,
                                        output_hydrograph,
                                        ctypes.byref(data_unit_type_id),
                                        ctypes.byref(num_time_steps),
                                        ctypes.byref(self.status))

        return np.array('1899-12-30', dtype='datetime64') + np.array(output_dates, dtype='timedelta64[D]'), np.array(output_hydrograph)

    def get_groundwater_hydrograph(self, groundwater_hydrograph_id, begin_date=None,
                                   end_date=None, length_conversion_factor=1.0, 
                                   volume_conversion_factor=1.0):
        ''' Returns the simulated groundwater hydrograph for the 
        provided groundwater hydrograph id

        Parameters
        ----------
        groundwater_hydrograph_id : int
            id for hydrograph being retrieved
            
        begin_date : str or None, default=None
            IWFM-style date for the beginning date of the simulated groundwater heads

        end_date : str or None, default=None
            IWFM-style date for the end date of the simulated groundwater heads

        length_conversion_factor : float, int, default=1.0
            hydrographs with units of length are multiplied by this
            value to convert simulation units to desired output units
            
        volume_conversion_factor : float, int, default=1.0
            hydrographs with units of volume are multiplied by this
            value to convert simulation units to desired output units
            e.g. use 2.29568E-8 for ft^3 --> TAF

        Returns
        -------
        np.arrays
            1-D array of dates
            1-D array of hydrograph values
        '''
        hydrograph_type = self.get_location_type_id_gwheadobs()
        layer_number = 1

        return self._get_hydrograph(hydrograph_type, groundwater_hydrograph_id, 
                                    layer_number, begin_date, end_date, 
                                    length_conversion_factor, volume_conversion_factor)

    def get_groundwater_hydrograph_at_node_and_layer(self, node_id, layer_number, 
                        begin_date=None, end_date=None, length_conversion_factor=1.0, 
                        volume_conversion_factor=1.0):
        ''' Returns a simulated groundwater hydrograph for a node and layer

        Parameters
        ----------
        node_id : int
            id for node where hydrograph being retrieved
            
        layer_number : int
            layer number for returning hydrograph. only used for groundwater hydrograph
            at node and layer
            
        begin_date : str or None, default=None
            IWFM-style date for the beginning date of the simulated groundwater heads

        end_date : str or None, default=None
            IWFM-style date for the end date of the simulated groundwater heads

        length_conversion_factor : float or int, default=1.0
            hydrographs with units of length are multiplied by this
            value to convert simulation units to desired output units
            
        volume_conversion_factor : float or int, default=1.0
            hydrographs with units of volume are multiplied by this
            value to convert simulation units to desired output units
            e.g. use 2.29568E-8 for ft^3 --> TAF

        Returns
        -------
        np.arrays
            1-D array of dates
            1-D array of hydrograph values
        '''
        hydrograph_type = self.get_location_type_id_node()

        return self._get_hydrograph(hydrograph_type, node_id, layer_number,
                                    begin_date, end_date, length_conversion_factor,
                                    volume_conversion_factor)

    def get_subsidence_hydrograph(self, subsidence_location_id, begin_date=None,
                                   end_date=None, length_conversion_factor=1.0, 
                                   volume_conversion_factor=1.0):
        ''' Returns the simulated subsidence hydrograph for the 
        provided subsidence hydrograph id

        Parameters
        ----------
        subsidence_location_id : int
            id for subsidence hydrograph location being retrieved
            
        begin_date : str or None, default=None
            IWFM-style date for the beginning date of the simulated subsidence

        end_date : str or None, default=None
            IWFM-style date for the end date of the simulated subsidence

        length_conversion_factor : float, int, default=1.0
            hydrographs with units of length are multiplied by this
            value to convert simulation units to desired output units
            
        volume_conversion_factor : float, int, default=1.0
            hydrographs with units of volume are multiplied by this
            value to convert simulation units to desired output units
            e.g. use 2.29568E-8 for ft^3 --> TAF

        Returns
        -------
        np.arrays
            1-D array of dates
            1-D array of hydrograph values
        '''
        hydrograph_type = self.get_location_type_id_subsidenceobs()
        layer_number = 1

        return self._get_hydrograph(hydrograph_type, subsidence_location_id, 
                                    layer_number, begin_date, end_date, 
                                    length_conversion_factor, volume_conversion_factor)

    def get_stream_hydrograph(self, stream_location_id, begin_date=None,
                              end_date=None, length_conversion_factor=1.0, 
                              volume_conversion_factor=1.0):
        ''' Returns the simulated stream hydrograph for the 
        provided stream hydrograph id

        Parameters
        ----------
        stream_location_id : int
            id for stream hydrograph location being retrieved
            
        begin_date : str or None, default=None
            IWFM-style date for the beginning date of the simulated stream flows

        end_date : str or None, default=None
            IWFM-style date for the end date of the simulated stream flows

        length_conversion_factor : float, int, default=1.0
            hydrographs with units of length are multiplied by this
            value to convert simulation units to desired output units
            
        volume_conversion_factor : float, int, default=1.0
            hydrographs with units of volume are multiplied by this
            value to convert simulation units to desired output units
            e.g. use 2.29568E-8 for ft^3 --> TAF

        Returns
        -------
        np.arrays
            1-D array of dates
            1-D array of hydrograph values
        '''
        hydrograph_type = self.get_location_type_id_streamhydobs()
        layer_number = 1

        return self._get_hydrograph(hydrograph_type, stream_location_id, 
                                    layer_number, begin_date, end_date, 
                                    length_conversion_factor, volume_conversion_factor)

    def get_gwheads_foralayer(self, layer_number, begin_date=None, end_date=None, length_conversion_factor=1.0):
        ''' Returns the simulated groundwater heads for a single user-specified model layer for
        every model node over a user-specified time interval.

        Parameters
        ----------
        layer_number : int
            layer number for a layer in the model
        
        begin_date : str, default=None
            IWFM-style date for the beginning date of the simulated groundwater heads

        end_date : str, default=None
            IWFM-style date for the end date of the simulated groundwater heads

        length_conversion_factor : float, int, default=1.0
            simulated heads are multiplied by this value to convert simulation units to desired output units

        Returns
        -------
        np.arrays
            1-D array of dates
            2-D array of heads for all nodes for each date

        Note
        ----
        the interval between the begin_date and the end_date is determined from the model time interval
        using get_time_specs()

        Examples
        --------
        >>> model = IWFMModel(dll, preprocessor_file, simulation_file)

        >>> dates, heads = model.get_gwheadsall_foralayer(1, '09/30/1980_24:00', '09/30/2000_24:00')
        
        >>> dates
            ['09/30/1980',
             '10/31/1980',
             '11/30/1980',
             '12/31/1980',
             .
             .
             .
             '09/30/2000']

        >>> heads
            [[458.57, 460.32, 457.86, ..., 686.42],
             [459.86, 462.38, 459.11, ..., 689.05],
             .
             .
             .
             [435.75, 439.23, 440.99, ..., 650.78]]

        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetGWHeads_ForALayer"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. ' 
                                 'Check for an updated version'.format('IW_Model_GetGWHeads_ForALayer'))
        
        # check that layer_number is an integer
        if not isinstance(layer_number, int):
            raise TypeError('layer_number must be an integer, '
                             'value {} provided is of type {}'.format(layer_number, type(layer_number)))

        # handle start and end dates
        # get time specs
        dates_list, output_interval = self.get_time_specs()
        
        if begin_date is None:
            begin_date = dates_list[0]
        else:
            self._validate_iwfm_date(begin_date)

            if begin_date not in dates_list:
                raise ValueError('begin_date was not recognized as a model time step. use IWFMModel.get_time_specs() method to check.')
        
        if end_date is None:
            end_date = dates_list[-1]
        else:
            self._validate_iwfm_date(end_date)

            if end_date not in dates_list:
                raise ValueError('end_date was not found in the Budget file. use IWFMModel.get_time_specs() method to check.')

        if self.is_date_greater(begin_date, end_date):
            raise ValueError('end_date must occur after begin_date')
                
        # check that length conversion factor is a number
        if not isinstance(length_conversion_factor, (int, float)):
            raise TypeError('length_conversion_factor must be a number. value {} provides is of type {}'.format(length_conversion_factor, type(length_conversion_factor)))
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # convert specified layer number to ctypes
        layer_number = ctypes.c_int(layer_number)

        # get number of time intervals between dates
        num_time_intervals = ctypes.c_int(self.get_n_intervals(begin_date, end_date, output_interval))

        # convert dates to ctypes
        begin_date = ctypes.create_string_buffer(begin_date.encode('utf-8'))
        end_date = ctypes.create_string_buffer(end_date.encode('utf-8'))

        # get length of begin_date and end_date strings
        length_date_string = ctypes.c_int(ctypes.sizeof(begin_date))

        # convert length_conversion_factor to ctypes
        length_conversion_factor = ctypes.c_double(length_conversion_factor)

        # get number of model nodes
        num_nodes = ctypes.c_int(self.get_n_nodes())

        # initialize output variables
        output_dates = (ctypes.c_double*num_time_intervals.value)()
        output_gwheads = ((ctypes.c_double*num_nodes.value)*num_time_intervals.value)()

        # call DLL procedure
        self.dll.IW_Model_GetGWHeads_ForALayer(ctypes.byref(layer_number),
                                               begin_date, 
                                               end_date,
                                               ctypes.byref(length_date_string),
                                               ctypes.byref(length_conversion_factor),
                                               ctypes.byref(num_nodes), 
                                               ctypes.byref(num_time_intervals),
                                               output_dates,
                                               output_gwheads,
                                               ctypes.byref(self.status))

        return np.array('1899-12-30', dtype='datetime64') + np.array(output_dates, dtype='timedelta64[D]'), np.array(output_gwheads)

    def get_gwheads_all(self, end_of_timestep=True, head_conversion_factor=1.0):
        ''' Returns the groundwater heads at all nodes in every aquifer 
        layer for the current simulation time step
        
        Parameters
        ----------
        end_of_timestep : boolean, default=True
            flag to specify if the groundwater heads are returned for 
            the beginning of the timestep or end of the time step

        head_conversion_factor : float, default=1.0
            factor to convert groundwater heads from simulation unit
            of length to a desired unit of length

        Returns
        -------
        np.ndarray
            2-D array of heads (n_nodes x n_layers)

        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return 
        the simulated groundwater heads after one time step is simulated
        i.e. after calling simulate_for_one_time_step method
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetGWHeads_All"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. ' 
                                 'Check for an updated version'.format('IW_Model_GetGWHeads_All'))
        
        if end_of_timestep:
            previous = ctypes.c_int(0)
        else:
            previous = ctypes.c_int(1)

        # convert head_conversion_factor to ctypes equivalent
        head_conversion_factor = ctypes.c_double(head_conversion_factor)

        # get number of model nodes
        n_nodes = ctypes.c_int(self.get_n_nodes())

        # get number of model layers
        n_layers = ctypes.c_int(self.get_n_layers())

        # initialize output variables
        heads = ((ctypes.c_double*n_nodes.value)*n_layers.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetGWHeads_All(ctypes.byref(n_nodes),
                                         ctypes.byref(n_layers),
                                         ctypes.byref(previous),
                                         ctypes.byref(head_conversion_factor),
                                         heads,
                                         ctypes.byref(self.status))

        return np.array(heads)

    def get_subsidence_all(self, subsidence_conversion_factor=1.0):
        ''' Returns the groundwater heads at all nodes in every aquifer 
        layer for the current simulation time step
        
        Parameters
        ----------
        subsidence_conversion_factor : float, default=1.0
            factor to convert subsidence from simulation unit
            of length to a desired unit of length

        Returns
        -------
        np.ndarray
            2-D array of subsidence at each node and layer (n_nodes x n_layers)

        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return 
        the simulated subsidence after one time step is simulated
        i.e. after calling simulate_for_one_time_step method
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetSubsidence_All"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. ' 
                                 'Check for an updated version'.format('IW_Model_GetSubsidence_All'))
        
        # convert head_conversion_factor to ctypes equivalent
        subsidence_conversion_factor = ctypes.c_double(subsidence_conversion_factor)

        # get number of model nodes
        n_nodes = ctypes.c_int(self.get_n_nodes())

        # get number of model layers
        n_layers = ctypes.c_int(self.get_n_layers())

        # initialize output variables
        subsidence = ((ctypes.c_double*n_nodes.value)*n_layers.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetSubsidence_All(ctypes.byref(n_nodes),
                                            ctypes.byref(n_layers),
                                            ctypes.byref(subsidence_conversion_factor),
                                            subsidence,
                                            ctypes.byref(self.status))

        return np.array(subsidence)

    def get_subregion_ag_pumping_average_depth_to_water(self):
        ''' Returns subregional depth to groundwater values that are 
        weighted-average with respect to agricultural pumping rates
        during a model run

        Returns
        -------
        np.ndarray
            array of weighted-average depth to groundwater
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetSubregionAgPumpingAverageDepthToGW"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. ' 
                                 'Check for an updated version'.format('IW_Model_GetSubregionAgPumpingAverageDepthToGW'))

        # get number of subregions in model
        n_subregions = ctypes.c_int(self.get_n_subregions())

        # initialize output variables
        average_depth_to_groundwater = (ctypes.c_double*n_subregions.value)()
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetSubregionAgPumpingAverageDepthToGW(ctypes.byref(n_subregions),
                                                                average_depth_to_groundwater,
                                                                ctypes.byref(self.status))

        return np.array(average_depth_to_groundwater)

    def get_zone_ag_pumping_average_depth_to_water(self, elements_list, zones_list):
        ''' Returns average depth to groundwater for user-defined zones

        Parameters
        ----------
        elements_list : list or np.ndarray
            list of all elements corresponding to all zones where average depth to water is calculated

        zones_list : list or np.ndarray
            list of zone ids corresponding to each element in the elements list

        Returns
        -------
        np.ndarray
            average depth to water for each zone specified
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetZoneAgPumpingAverageDepthToGW"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. ' 
                                 'Check for an updated version'.format('IW_Model_GetZoneAgPumpingAverageDepthToGW'))

        # if list convert to np.ndarray
        if isinstance(elements_list, list):
            elements_list = np.array(elements_list)

        if isinstance(zones_list, list):
            zones_list = np.array(zones_list)

        if (elements_list.shape != zones_list.shape) | (len(elements_list.shape) != 1):
            raise ValueError('elements_list and zone_list should be 1D'
                             ' arrays of the same length')

        # get length of elements list
        len_elements_list = ctypes.c_int(len(elements_list))

        # get length of zones list
        n_zones = ctypes.c_int(len(np.unique(zones_list)))

        # convert elements_list to ctypes
        elements_list = (ctypes.c_int*len_elements_list.value)(*elements_list)

        # convert zones_list to ctypes
        zones_list = (ctypes.c_int*len_elements_list.value)()

        # initialize output variables
        average_depth_to_groundwater = (ctypes.c_double*n_zones.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetZoneAgPumpingAverageDepthToGW(ctypes.byref(len_elements_list),
                                                           elements_list,
                                                           zones_list,
                                                           ctypes.byref(n_zones),
                                                           average_depth_to_groundwater,
                                                           ctypes.byref(self.status))

        return np.array(average_depth_to_groundwater)

    def get_n_locations(self, location_type_id):
        ''' Returns the number of locations for a specified location
        type

        Parameters
        ----------
        location_type_id : int
            identification number used by IWFM for a particular location type
            e.g elements, nodes, subregions, etc.

        Returns
        -------
        int
            number of locations for the location type specified
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNLocations"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. ' 
                                 'Check for an updated version'.format('IW_Model_GetNLocations'))
        
        # convert location type id to ctypes
        location_type_id = ctypes.c_int(location_type_id)

        # initialize output variables
        n_locations = ctypes.c_int(0)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetNLocations(ctypes.byref(location_type_id),
                                        ctypes.byref(n_locations),
                                        ctypes.byref(self.status))

        return n_locations.value

    def get_n_small_watersheds(self):
        ''' Returns the number of small watersheds specified in an IWFM
        model
        
        Returns
        -------
        int
            number of small watersheds
        '''
        location_type_id = self.get_location_type_id_smallwatershed()

        return self.get_n_locations(ctypes.byref(location_type_id))

    def get_location_ids(self, location_type_id):
        ''' Returns the location identification numbers used by the 
        model for a specified location type

        Parameters
        ----------
        location_type_id : int
            identification number used by IWFM for a particular location type
            e.g elements, nodes, subregions, etc.
        
        Returns
        -------
        np.ndarray
            array of identification numbers 
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetLocationIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. ' 
                                 'Check for an updated version'.format('IW_Model_GetLocationIDs'))

        # get number of locations of the given location type
        n_locations = ctypes.c_int(self.get_n_locations(location_type_id))

        # convert location_type_id to ctypes
        location_type_id = ctypes.c_int(location_type_id)

        # initialize output variables
        location_ids = (ctypes.c_int*n_locations.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetLocationIDs(ctypes.byref(location_type_id),
                                         ctypes.byref(n_locations),
                                         location_ids,
                                         ctypes.byref(self.status))

        return np.array(location_ids)
    
    def get_small_watershed_ids(self):
        ''' Returns the small watershed identification numbers specified
        in the IWFM model
        
        Returns
        -------
        np.ndarray
            integer array of small watershed identification numbers
        '''
        location_type_id = self.get_location_type_id_smallwatershed()

        return self.get_location_ids(location_type_id)

    def set_preprocessor_path(self, preprocessor_path):
        ''' sets the path to the directory where the preprocessor main
        input file is located

        Parameters
        ----------
        preprocessor_path : str
            file path to where preprocessor main input file is stored
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_SetPreProcessorPath"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. ' 
                                 'Check for an updated version'.format('IW_Model_SetPreProcessorPath'))
        
        # get length of preprocessor_path string
        len_pp_path = len(preprocessor_path)

        # convert preprocessor path to ctypes character array
        preprocessor_path = ctypes.create_string_buffer(preprocessor_path.encode('utf-8'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_SetPreProcessorPath(ctypes.byref(len_pp_path),
                                              preprocessor_path,
                                              ctypes.byref(self.status))

    def set_simulation_path(self, simulation_path):
        ''' sets the path to the directory where the simulation main
        input file is located

        Parameters
        ----------
        simulation_path : str
            file path to where simulation main input file is stored
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_SetSimulationPath"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. ' 
                                 'Check for an updated version'.format('IW_Model_SetSimulationPath'))
        
        # get length of preprocessor_path string
        len_sim_path = len(simulation_path)

        # convert preprocessor path to ctypes character array
        simulation_path = ctypes.create_string_buffer(simulation_path.encode('utf-8'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_SetSimulationPath(ctypes.byref(len_sim_path),
                                            simulation_path,
                                            ctypes.byref(self.status))

    def set_supply_adjustment_max_iterations(self, max_iterations):
        ''' sets the maximum number of iterations that will be used in 
        automatic supply adjustment 
        
        Parameters
        ----------
        max_iterations : int
            maximum number of iterations for automatic supply adjustment
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_SetSupplyAdjustmentMaxIters"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. ' 
                                 'Check for an updated version'.format('IW_Model_SetSupplyAdjustmentMaxIters'))
        
        # convert max_iterations to ctypes
        max_iterations = ctypes.c_int(max_iterations)
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_SetSupplyAdjustmentMaxIters(ctypes.byref(max_iterations),
                                                      ctypes.byref(self.status))

    def set_supply_adjustment_tolerance(self, tolerance):
        ''' sets the tolerance, given as a fraction of the water demand
        that will be used in automatic supply adjustment

        Parameters
        ----------
        tolerance : float
            fraction of water demand used as the convergence criteria
            for iterative supply adjustment

        Notes
        -----
        When the automatic supply adjustment feature of IWFM is turned 
        on, IWFM iteratively tries to adjust water supplies (diversions, 
        pumping or both based on user defined specifications) to meet 
        the water demand. When the difference between water supply and 
        demand is less than the tolerance, IWFM assumes equivalency 
        between demand and supply, and terminates supply adjustment 
        iterations.
        
        0.01 represents 1% of the demand
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_SetSupplyAdjustmentTolerance"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. ' 
                                 'Check for an updated version'.format('IW_Model_SetSupplyAdjustmentTolerance'))
        
        # convert tolerance to ctypes
        tolerance = ctypes.c_double(tolerance)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_SetSupplyAdjustmentTolerance(ctypes.byref(tolerance),
                                                       ctypes.byref(self.status))

    def delete_inquiry_data_file(self):
        ''' deletes the binary file, IW_ModelData_ForInquiry.bin, 
        generated by the IWFM DLL when the Model Object is instantiated 
        
        Notes
        -----
        When this binary file exists, the entire Model Object is not created
        when the IWFMModel object is created so not all functionality is available 
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_DeleteInquiryDataFile"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_DeleteInquiryDataFile'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
        
        self.dll.IW_Model_DeleteInquiryDataFile(ctypes.byref(self.length_simulation_file_name),
                                                self.simulation_file_name,
                                                ctypes.byref(self.status))

    def simulate_for_one_timestep(self):
        ''' simulates a single timestep of the model application

        Notes
        -----
        This method is intended to be used when is_for_inquiry=0
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_SimulateForOneTimeStep"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_SimulateForOneTimeStep'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_SimulateForOneTimeStep(ctypes.byref(self.status))

    def simulate_for_an_interval(self, time_interval):
        ''' simulates the model application for a specified time interval

        Parameters
        ----------
        time_interval : str
            valid IWFM time interval greater than or equal to simulation 
            time step

        Notes
        -----
        This method is intended to be used when is_for_inquiry=0 during
        a model simulation
        specified time interval must be greater than simulation time step
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_SimulateForAnInterval"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_SimulateForAnInterval'))
        
        # get simulation time_interval
        simulation_time_interval = self.get_time_specs()[-1]

        # determine if time_interval is greater than or equal to 
        # simulation_time_interval
        if not self._is_time_interval_greater_or_equal(time_interval, simulation_time_interval):
            raise ValueError('time interval must be greater than or '
                             'equal to simulation time interval')

        # convert time_interval to ctypes
        time_interval = ctypes.create_string_buffer(time_interval.encoding('utf-8'))

        # get length of time interval
        len_time_interval = ctypes.c_int(ctypes.sizeof(time_interval))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
        
        self.dll.IW_Model_SimulateForAnInterval(ctypes.byref(len_time_interval),
                                                time_interval,
                                                ctypes.byref(self.status))

    def simulate_all(self):
        ''' performs all of the computations for the entire simulation 
        period

        Notes
        -----
        This method is intended to be used when is_for_inquiry=0 during
        a model simulation
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_SimulateAll"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_SimulateAll'))
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_SimulateAll(ctypes.byref(self.status))

    def advance_time(self):
        ''' advances the simulation time step by one simulation time step
        
        Notes
        -----
        This method is intended to be used when is_for_inquiry=0 during
        a model simulation
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_AdvanceTime"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_AdvanceTime'))
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_AdvanceTime(ctypes.byref(self.status))

    def read_timeseries_data(self):
        ''' reads in all of the time series data for the current 
        simulation time step

        Notes
        -----
        This method is intended to be used when is_for_inquiry=0 during
        a model simulation

        See Also
        --------
        IWFMModel.read_timeseries_data_overwrite : reads time series data for the current simulation time step and allows overwriting certain time series data
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_ReadTSData"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_ReadTSData'))
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_ReadTSData(ctypes.byref(self.status))

    def read_timeseries_data_overwrite(self, land_use_areas, 
                                        diversion_ids, diversions,
                                        stream_inflow_ids, stream_inflows):
        ''' reads time series data for the current simulation time step and allows overwriting certain time series data
        
        Parameters
        ----------
        land_use_areas : list or np.ndarray
            subregional land use areas to be overwritten for the current 
            time step order is non-ponded first, then ponded, then urban,
            then native, and riparian

        diversion_ids : list or np.ndarray
            diversion identification numbers to be overwritten

        diversions : list or np.ndarray
            diversion amounts to overwrite for each diversion 
            identification number provided. must be same length
            as diversion_ids

        stream_inflow_ids : list or np.ndarray
            stream inflow indices where boundary inflows will be 
            overwritten

        stream_inflows : list or np.ndarray
            stream inflow amounts to be overwritten for each stream
            flow index provided. Must be the same length as 
            stream_inflow_ids

        Returns
        -------
        None

        Notes
        -----
        This method is intended to be used when is_for_inquiry=0 during
        a model simulation

        See Also
        --------
        IWFMModel.read_timeseries_data : reads in all of the time series data for the current simulation time step
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_ReadTSData_Overwrite"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_ReadTSData_Overwrite'))

        if land_use_areas is None:
            n_landuses = ctypes.c_int(0)
            n_subregions = ctypes.c_int(0)
        else:
            # get number of land uses
            n_landuses = ctypes.c_int(self.get_n_ag_crops() + 3)

            # get number of subregions
            n_subregions = ctypes.c_int(self.get_n_subregions())
        
            # check that land_use_areas is n_subregions by n_landuses
            if isinstance(land_use_areas, list):
                land_use_areas = np.array(land_use_areas)

            if land_use_areas.shape != (n_subregions, n_landuses):
                raise ValueError('land_use areas must be provided for '
                                 'each land use and subregion in the model')

        # convert land_use_areas to ctypes
        land_use_array = ((ctypes.c_double*n_subregions.value)*n_landuses.value)()
        for i, row in enumerate(land_use_areas):
            land_use_array[i][:] = row

        # check that diversion_ids are valid
        # if either diversion_ids or diversions are None treat both as None.
        if diversion_ids is None or diversions is None:
            n_diversions = ctypes.c_int(0)
        else:
            # check that diversion_ids are provided as correct data type
            if not isinstance(diversion_ids, (np.ndarray, list)):
                raise TypeError('diversion_ids must be provided as a list or np.ndarray')

            # check that diversions are provided as the correct data type
            if not isinstance(diversions, (np.ndarray, list)):
                raise TypeError('diversions must be provided as a list or np.ndarray')
            
            # get diversion_ids specified in the model input files
            model_diversion_ids = self.get_diversion_ids()

            # if provided as a list, convert to a np.ndarray
            if isinstance(diversion_ids, list):
                diversion_ids = np.array(diversion_ids)

            if isinstance(diversions, list):
                diversions = np.array(diversions)

            # check that all diversion_ids provided are valid model diversion ids
            if not np.all(np.isin(diversion_ids, model_diversion_ids)):
                raise ValueError('diversion_ids contains diversion '
                                 'identification number not found in the model')
            
            # check diversion and diversion_ids are the same length
            if (diversion_ids.shape != diversions.shape) and (len(diversion_ids.shape) == 1):
                raise ValueError('diversion_ids and diversions must be 1D arrays of the same length')
            
            # get the number of diversions
            n_diversions = ctypes.c_int(len(diversion_ids))     

        # convert diversion_ids and diversion to ctypes
        diversion_ids = (ctypes.c_int*n_diversions.value)(*diversion_ids)
        diversions = (ctypes.c_double*n_diversions.value)(*diversions)
        
        # check that stream_inflow_ids are valid
        # if either stream_inflow_ids or stream_inflows are None treat both as None.
        if stream_inflow_ids is None or stream_inflows is None:
            n_stream_inflows = ctypes.c_int(0)
        else:
            # check that stream_inflow_ids are provided as the correct data type
            if not isinstance(stream_inflow_ids, (np.ndarray, list)):
                raise TypeError('stream_inflow_ids must be provided as a list or np.ndarray')

            # check that stream_inflows are provided as the correct data type
            if not isinstance(stream_inflows, (np.ndarray, list)):
                raise TypeError('stream_inflows must be provided as a list or np.ndarray')

            model_stream_inflow_ids = self.get_stream_inflow_ids()

            # if provided as a list, convert to a np.ndarray
            if isinstance(stream_inflow_ids, list):
                stream_inflow_ids = np.array(stream_inflow_ids)

            if isinstance(stream_inflows, list):
                stream_inflows = np.array(stream_inflows)

            # check that all stream_inflow_ids provided are valid model stream inflow ids
            if not np.all(np.isin(stream_inflow_ids, model_stream_inflow_ids)):
                raise ValueError('stream_inflow_ids contains stream inflow '
                                 'identification numbers not found in the model')
            
            # check stream_inflows and stream_inflow_ids are the same length
            if (stream_inflow_ids.shape != stream_inflows.shape) and (len(stream_inflow_ids.shape) == 1):
                raise ValueError('stream_inflow_ids and stream_inflows '
                                 'must be 1D arrays of the same length')
            
            # get the number of diversions
            n_stream_inflows = ctypes.c_int(len(stream_inflow_ids))     

        # convert diversion_ids and diversion to ctypes
        stream_inflow_ids = (ctypes.c_int*n_diversions.value)(*stream_inflow_ids)
        stream_inflows = (ctypes.c_double*n_diversions.value)(*stream_inflows)
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_ReadTSData_Overwrite(ctypes.byref(n_landuses),
                                               ctypes.byref(n_subregions),
                                               land_use_array,
                                               ctypes.byref(n_diversions),
                                               diversion_ids,
                                               diversions,
                                               ctypes.byref(n_stream_inflows),
                                               stream_inflow_ids,
                                               stream_inflows,
                                               ctypes.byref(self.status))

    def print_results(self):
        ''' prints out all the simulation results at the end of a 
        simulation
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_PrintResults"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_PrintResults'))
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_PrintResults(ctypes.byref(self.status))

    def advance_state(self):
        ''' advances the state of the hydrologic system in time (e.g. 
        groundwater heads at current timestep are switched to 
        groundwater heads at previous timestep) during a model run
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_AdvanceState"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_AdvanceState'))
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_AdvanceState(ctypes.byref(self.status))

    def is_stream_upstream_node(self, stream_node_1, stream_node_2):
        ''' checks if a specified stream node .is located upstream from
        another specified stream node within the stream network of the 
        IWFM model

        Parameters
        ----------
        stream_node_1 : int
            stream node being checked if it is upstream of stream_node_2

        stream_node_2 : int
            stream node used to determine if stream_node_1 is upstream

        Returns
        -------
        boolean
            True if stream_node_1 is upstream of stream_node_2
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_IsStrmUpstreamNode"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_IsStrmUpstreamNode'))
        
        # convert stream_node_1 and stream_node_2 to ctypes
        stream_node_1 = ctypes.c_int(stream_node_1)
        stream_node_2 = ctypes.c_int(stream_node_2)

        # initialize output variables
        is_upstream = ctypes.c_int(0)
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_IsStrmUpstreamNode(ctypes.byref(stream_node_1),
                                             ctypes.byref(stream_node_2),
                                             ctypes.byref(is_upstream),
                                             ctypes.byref(self.status))

        if is_upstream.value == 1:
            return True
        else:
            return False

    def is_end_of_simulation(self):
        ''' check if the end of simulation period has been reached during a model run

        Returns
        -------
        boolean
            True if end of simulation period otherwise False
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_IsEndOfSimulation"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_IsEndOfSimulation'))
        
        # initialize output variables
        is_end_of_simulation = ctypes.c_int(0)
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_IsEndOfSimulation(ctypes.byref(is_end_of_simulation),
                                            ctypes.byref(self.status))
        
        if is_end_of_simulation.value == 1:
            return True
        else:
            return False

    def is_model_instantiated(self):
        ''' check if a Model object is instantiated 
        
        Returns
        -------
        boolean
            True if model object is instantiated otherwise False
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_IsModelInstantiated"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_IsModelInstantiated'))
        
        # initialize output variables
        is_instantiated = ctypes.c_int(0)
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_IsModelInstantiated(ctypes.byref(is_instantiated),
                                              ctypes.byref(self.status))

        if is_instantiated.value == 1:
            return True
        else:
            return False

    def turn_supply_adjustment_on_off(self, diversion_adjustment_flag, pumping_adjustment_flag):
        ''' turns the automatic supply adjustment of diversions and 
        pumping to meet agricultural and/or urban water demands on or 
        off during a model run

        Parameters
        ----------
        diversion_adjustment_flag : int, 0 or 1 only
            1 - turn diversion supply adjustment on
            0 - turn diversion supply adjustment off

        pumping_adjustment_flag : int, 0 or 1 only
            1 - turn pumping supply adjustment on
            0 - turn pumping supply adjustment off

        Returns
        -------
        None
            updates global supply adjustment flags for diversions and 
            pumping
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_TurnSupplyAdjustOnOff"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_TurnSupplyAdjustOnOff'))

        if diversion_adjustment_flag not in [0, 1]:
            raise ValueError('diversion_adjustment_flag must be 0 or 1 '
                             'to turn diversion adjustment on use 1 '
                             'to turn diversion adjustment off use 0.')

        if pumping_adjustment_flag not in [0, 1]:
            raise ValueError('diversion_adjustment_flag must be 0 or 1 '
                             'to turn diversion adjustment on use 1 '
                             'to turn diversion adjustment off use 0.')

        # convert adjustment flags to ctypes
        diversion_adjustment_flag = ctypes.c_int(diversion_adjustment_flag)
        pumping_adjustment_flag = ctypes.c_int(pumping_adjustment_flag)
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_TurnSupplyAdjustOnOff(ctypes.byref(diversion_adjustment_flag),
                                                ctypes.byref(pumping_adjustment_flag),
                                                ctypes.byref(self.status))

    def restore_pumping_to_read_values(self):
        ''' restores the pumping rates to the values read from the 
        Pumping Rate input file during a model run. This procedure is 
        useful when it is necessary to re-simulate the hydrologic 
        system (e.g. when IWFM is linked to a reservoir operations 
        model in an iterative fashion) at a given timestep with pumping 
        adjustment is on and the pumping values need to be restored to 
        their original values
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_RestorePumpingToReadValues"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_RestorePumpingToReadValues'))
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_RestorePumpingToReadValues(ctypes.byref(self.status))

    ### methods that wrap two or more DLL calls
    def get_groundwater_hydrograph_info(self):
        ''' Returns model information for the groundwater hydrographs,
        including hydrograph id, x- and y- coordinates, name, and 
        stratigraphy.

        Returns
        -------
        pd.DataFrame
            columns: id, name, x, y, gse, bottom_layer1, bottom_layer2, ..., bottom_layern
        '''
        hydrograph_ids = self.get_groundwater_hydrograph_ids()
        hydrograph_x_coord, hydrograph_y_coord = self.get_groundwater_hydrograph_coordinates()
        hydrograph_names = self.get_groundwater_observation_names()
        df = pd.DataFrame({'id': hydrograph_ids, 'Name': hydrograph_names, 
                           'X': hydrograph_x_coord, 'Y': hydrograph_y_coord})
        
        columns = ['GSE'] + ['BTM_Lay{}'.format(layer + 1) for layer in range(self.get_n_layers())]

        func = lambda row: self.get_stratigraphy_atXYcoordinate(row['X'], row['Y'], 1.0)
        df[columns] = df.apply(func, axis=1, result_type='expand')

        return df

    def get_node_info(self):
        ''' Returns node id, x-, and y-coordinates for each node in an IWFM model

        Returns
        -------
        pd.DataFrame
            DataFrame containing IDs, x-coordinates, and y-coordinates for all nodes in an IWFM model

        See Also
        --------
        IWFMModel.get_n_nodes : Returns the number of nodes in an IWFM model
        IWFMModel.get_node_ids : Returns an array of node IDs in an IWFM model
        IWFMModel.get_node_coordinates : Returns the x,y coordinates of the nodes in an IWFM model 

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_node_info()
             NodeID          X            Y
          0       1  1804440.0   14435520.0
          1       2  1811001.6   14435520.0
          2       3  1817563.2   14435520.0
          3       4  1824124.8   14435520.0
          4       5  1830686.4   14435520.0
        ...     ...        ...          ...           
        436     437  1909425.6   14566752.0
        437     438  1915987.2   14566752.0
        438     439  1922548.8   14566752.0
        439     440  1929110.4   14566752.0
        440     441  1935672.0   14566752.0
        441 rows × 3 columns
        >>> model.kill()
        '''
        # get array of node ids
        node_ids = self.get_node_ids()
        
        # get arrays of x- and y- coordinates for each node id
        x, y = self.get_node_coordinates()
        
        # create DataFrame object to manage node info
        node_info = pd.DataFrame({'NodeID': node_ids, 'X': x, 'Y': y})

        return node_info

    def get_element_info(self):
        ''' Returns element configuration information for all 
        elements in an IWFM model

        Returns
        -------
        pd.DataFrame
            DataFrame containing subregion IDs, node order, and node IDs for each element ID

        See Also
        --------
        IWFMModel.get_n_elements : Returns the number of elements in an IWFM model
        IWFMModel.get_element_ids : Returns an array of element IDs in an IWFM model
        IWFMModel.get_element_config : Returns an array of node IDs for an IWFM element
        IWFMModel.get_subregions_by_element : Returns an array of IWFM elements contained in each subregion

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_element_info()
               IE   SR  NodeNum  NodeID
           0    1    1    Node1       1
           1    1    1    Node2       2
           2    1    1    Node3      23
           3    1    1    Node4      22
           4    2    1    Node1       2
         ...  ...  ...      ...     ...
        1595  399    2    Node4     439
        1596  400    2    Node1     419
        1597  400    2    Node2     420
        1598  400    2    Node3     441
        1599  400    2    Node4     440
        1600 rows x 4 columns
        >>> model.kill()
        '''
        df = pd.DataFrame({'IE': self.get_element_ids()})
        
        # generate column names for node id configuration
        columns = ['Node{}'.format(i+1) for i in range(4)]
        df[columns] = df.apply(lambda row: self.get_element_config(row['IE']),
                               axis=1, result_type='expand')
        
        df['SR'] = self.get_subregions_by_element()

        stacked_df = df.set_index(['IE', 'SR']).stack().reset_index()
        stacked_df.rename(columns={'level_2': 'NodeNum', 0: 'NodeID'},
                          inplace=True)

        return stacked_df[stacked_df['NodeID'] != 0]

    def get_boundary_nodes(self, subregions=False, remove_duplicates=False):
        ''' Returns nodes that make up the boundary of an IWFM model

        Parameters
        ----------
        subregions : boolean, default=False
            if True will return the nodes for the model subregion boundaries
            if False will return the nodes for the model boundary

        remove_duplicates : boolean, default=False
            if True will return only the unique nodes
            if False will return the start and end nodes

        Returns
        -------
        pd.DataFrame
            DataFrame of Node IDs for the model boundary
        '''
        element_segments = self.get_element_info()

        # add columns to dataframe
        element_segments['start_node'] = element_segments['NodeID']
        element_segments['end_node'] = 0
        element_segments['count'] = 0

        # update end_node column with values for each element
        for element in element_segments['IE'].unique():
            element_nodes = element_segments[element_segments['IE'] == element]['NodeID'].to_numpy()
            element_segments.loc[element_segments['IE'] == element, 'end_node'] = np.roll(element_nodes, -1, axis=0)
        
        # duplicate start_node and end_node
        element_segments['orig_start_node'] = element_segments['start_node']
        element_segments['orig_end_node'] = element_segments['end_node']

        # order start_nodes and end_nodes low to high
        condition = element_segments['start_node']>element_segments['end_node']
        element_segments.loc[condition, ['start_node', 'end_node']] = element_segments.loc[condition, ['end_node', 'start_node']].values
        
        if not subregions:
            # count segments interior segments should have count of 2 while edge segments have count of 1
            grouped = element_segments.groupby(['start_node', 'end_node'])['count'].count().reset_index()
        
            # filter only the edge segments with count = 1
            boundary_nodes = grouped[grouped['count'] == 1][['start_node', 'end_node']]

            if remove_duplicates:
                # organize nodes in single column and remove duplicates
                boundary_nodes = boundary_nodes.stack().reset_index().drop(['level_0', 'level_1'], axis=1)
                boundary_nodes.rename(columns={0: 'NodeID'}, inplace=True)
                boundary_nodes.drop_duplicates('NodeID', inplace=True)
            
                return boundary_nodes
            
            return pd.merge(element_segments, boundary_nodes, on=['start_node', 'end_node'])[['orig_start_node', 'orig_end_node']]

        else:
            # count segments interior segments should have count of 2 while edge segments have count of 1
            grouped = element_segments.groupby(['SR', 'start_node', 'end_node'])['count'].count().reset_index()

            # filter only the edge segments with count = 1
            boundary_nodes = grouped[grouped['count'] == 1][['SR', 'start_node', 'end_node']]

            if remove_duplicates:
                # organize nodes in single column and remove duplicates
                boundary_nodes = boundary_nodes.set_index('SR', append=True).stack().reset_index().drop(['level_0', 'level_2'], axis=1)
                boundary_nodes.rename(columns={0: 'NodeID'}, inplace=True)
                boundary_nodes.drop_duplicates('NodeID', inplace=True)

                return boundary_nodes

            return pd.merge(element_segments, boundary_nodes, on=['SR', 'start_node', 'end_node'])[['SR', 'orig_start_node', 'orig_end_node']]

    def get_element_spatial_info(self):
        ''' Returns element configuration information including x-y 
        coordinates for nodes

        Returns
        -------
        pd.DataFrame
            DataFrame containing element IDs, Subregions, NodeID for each element with x-y coordinates, and Code for matplotlib patch plotting
        
        See Also
        --------
        IWFMModel.get_element_info : Returns element configuration information for all elements in an IWFM model
        IWFMModel.get_node_info : Returns node id, x-, and y-coordinates for each node in an IWFM model

        Example
        -------
        >>> from pywfm import IWFMModel
        >>> dll = '../../DLL/Bin/IWFM2015_C_x64.dll'
        >>> pp_file = '../Preprocessor/PreProcessor_MAIN.IN'
        >>> sim_file = 'Simulation_MAIN.IN'
        >>> model = IWFMModel(dll, pp_file, sim_file)
        >>> model.get_element_spatial_info()
               IE   SR  NodeNum NodeID         X          Y Count code
           0    1    1    Node1      1 1804440.0 14435520.0     4    1
           1    1    1    Node2      2 1811001.6 14435520.0     4    2
           2    1    1    Node3     23 1811001.6 14442081.6     4    2
           3    1    1    Node4     22 1804440.0 14442081.6     4   79
           4    2    1    Node1      2 1811001.6 14435520.0     4    1
         ...  ...  ...    ...      ...       ...        ...   ...  ...
        1595  399    2    Node4    439 1922548.8 14566752.0     4   79
        1596  400    2    Node1    419 1929110.4 14560190.4     4    1
        1597  400    2    Node2    420 1935672.0 14560190.4     4    2
        1598  400    2    Node3    441 1935672.0 14566752.0     4    2
        1599  400    2    Node4    440 1929110.4 14566752.0     4   79
        1600 rows × 8 columns
        >>> model.kill()
        '''
        node_info = self.get_node_info()
        element_info = self.get_element_info()
        
        # merge element info with nodes to assign coordinates to each element vertex
        element_geometry = pd.merge(element_info, node_info, on='NodeID')
        element_geometry.sort_values(by=['IE', 'NodeNum'], inplace=True)

        # generate count of nodes for each element
        elem_node_count = element_geometry.groupby('IE')['IE'].count().to_frame()
        elem_node_count.rename(columns={'IE': 'Count'}, inplace=True)
        elem_node_count.reset_index(inplace=True)
        
        element_geometry_info = pd.merge(element_geometry, elem_node_count, on='IE')

        # create internal function to assign plotting codes
        def apply_code(node_num, node_count):
            if node_num == "Node1":
                return Path.MOVETO
            elif node_num == "Node2":
                return Path.LINETO
            elif node_num == "Node3":
                if node_count == 3:
                    return Path.CLOSEPOLY
                elif node_count == 4:
                    return Path.LINETO
            else:
                return Path.CLOSEPOLY

        func = lambda row: apply_code(row["NodeNum"], row["Count"])
        element_geometry_info["code"] = element_geometry_info.apply(func, 
                                                                    axis=1)

        return element_geometry_info

    def get_depth_to_water(self, layer_number, begin_date=None, end_date=None):
        ''' calculates a depth to water for an IWFM model layer for all dates between
        the provided start date and end date.

        Parameters
        ----------
        layer_number : int
            layer number id for a given layer in an IWFM model. Must be equal to or 
            less than total number of model layers

        start_date : str, default=None
            IWFM format date for first date used to return simulated heads

        end_date : str, default=None
            IWFM format date for last date used to return simulated heads

        Returns
        -------
        pandas DataFrame object
            depth to water by model node and date
        '''
        # check layer number is valid
        if not isinstance(layer_number, int):
            raise ValueError('layer_number must be an integer, value {} provided is of type {}'.format(layer_number, type(layer_number)))
        num_layers = self.get_n_layers()
        if layer_number < 0 or layer_number > num_layers:
            raise ValueError('layer number must be between 1 and {} (the total number of model layers)'.format(num_layers))
        
        # handle start and end dates
        # get time specs
        dates_list, output_interval = self.get_time_specs()
        
        if begin_date is None:
            begin_date = dates_list[0]
        else:
            self._validate_iwfm_date(begin_date)

            if begin_date not in dates_list:
                raise ValueError('begin_date was not recognized as a model time step. use IWFMModel.get_time_specs() method to check.')
        
        if end_date is None:
            end_date = dates_list[-1]
        else:
            self._validate_iwfm_date(end_date)

            if end_date not in dates_list:
                raise ValueError('end_date was not recognized as a model time step. use IWFMModel.get_time_specs() method to check.')

        if self.is_date_greater(begin_date, end_date):
            raise ValueError('end_date must occur after begin_date')
        
        # get ground surface elevations
        gs_elevs = self.get_ground_surface_elevation()

        # get groundwater heads
        dts, heads = self.get_gwheads_foralayer(layer_number, begin_date, end_date)

        # calculate depth to water
        depth_to_water = gs_elevs - heads

        # convert to dataframe object
        dtw_df = pd.DataFrame(data=depth_to_water, index=pd.to_datetime(dts), columns=np.arange(1,self.get_n_nodes() + 1))

        # reformat dataframe
        dtw_df = dtw_df.stack().reset_index()
        dtw_df.rename(columns={'level_0': 'Date', 'level_1': 'NodeID', 0: 'DTW'}, inplace=True)

        return pd.merge(dtw_df, self.get_node_info(), on='NodeID')


    ### plotting methods
    def plot_elements(self, axes, scale_factor=10000,
                      buffer_distance=10000, write_to_file=False, 
                      file_name=None):
        ''' plots model elements on predefined axes

        Parameters
        ----------
        axes : plt.Axes
            axes object for matplotlib figure

        scale_factor : int, default=10000
            used to scale the limits of the x and y axis of the plot
            e.g. scale_factor=1 rounds the x and y min and max values 
            down and up, respectively to the nearest whole number

        buffer_distance : int, default=10000
            value used to buffer the min and max axis values by a 
            number of units

        write_to_file : boolean, default=False
            save plot to file. if True, file_name is required

        file_name : str
            file path and name (with extension for valid matplotlib.pyplot 
            savefig output type)

        Returns
        -------
        None
            matplotlib figure is generated
        '''
        if not isinstance(axes, plt.Axes):
            raise TypeError('axes must be an instance of matplotlib.pyplot.Axes')

        if not isinstance(scale_factor, int):
            raise TypeError('scale_factor must be an integer')

        if not isinstance(buffer_distance, int):
            raise TypeError('buffer distance must be an integer')

        if not isinstance(write_to_file, bool):
            raise TypeError('write_to_file must be True or False')

        if write_to_file and file_name is None:
            raise ValueError('to save figure, user must specify a file_name')

        if file_name is not None:
            if not isinstance(file_name, str):
                raise TypeError('file_name must be a string')

            else:
                if not os.path.isdir(os.path.dirname(file_name)):
                    raise ValueError('file path: {} does not exist'.format(os.path.dirname(file_name)))

        model_data = self.get_element_spatial_info()

        xmin = math.floor(model_data['X'].min()/scale_factor)*scale_factor - buffer_distance
        xmax = math.ceil(model_data['X'].max()/scale_factor)*scale_factor + buffer_distance
        ymin = math.floor(model_data['Y'].min()/scale_factor)*scale_factor - buffer_distance
        ymax = math.ceil(model_data['Y'].max()/scale_factor)*scale_factor + buffer_distance
        
        vertices = model_data[['X', 'Y']].values
        codes = model_data['code'].values

        elempath = Path(vertices, codes)

        elempatch = patches.PathPatch(elempath, facecolor=None, edgecolor='0.6', lw=0.5)
        axes.add_patch(elempatch)
        axes.set_xlim(xmin, xmax)
        axes.set_ylim(ymin, ymax)
        #axes.grid()

        if write_to_file:
            plt.savefig(file_name)

    @staticmethod
    def order_boundary_nodes(in_boundary_nodes, start_node_column, end_node_column):
        ''' takes an unordered dataframe with two columns of node ids and orders them
        such that the start id of the next is equal to the end id of the previous. A code
        is added so the output can be used to build a matplotlib path patch.

        Parameters
        ----------
        in_boundary_nodes : pd.DataFrame
            pandas DataFrame containing two columns containing ids to be ordered in sequence

        start_node_column : str
            name of start node column

        end_node_column : str
            name of end node column

        Returns
        -------
        pd.DataFrame
            pandas DataFrame ordered into a continuous sequence or set of sequences
        '''
        # create list for dataframe
        df_list = []

        # get first segment value
        start_segment = in_boundary_nodes[in_boundary_nodes[start_node_column] == in_boundary_nodes[start_node_column].min()][[start_node_column, end_node_column]].to_numpy(dtype=int)

        # put first segment value in dataframe with code = 1 i.e. Path.MoveTo
        out_df = pd.DataFrame(data=np.append(start_segment, 1).reshape(1,3), columns=[start_node_column, end_node_column, 'code'])

        # store first_start_node
        first_start_node = out_df[start_node_column].to_numpy()[0]

        # store end_node of segment
        previous_end_node = out_df.iloc[-1][end_node_column]

        for _ in range(len(in_boundary_nodes) - 1):
            if previous_end_node == first_start_node:
                in_boundary_nodes = in_boundary_nodes.merge(out_df, on=[start_node_column,end_node_column], 
                           how='left', indicator=True)
            
                in_boundary_nodes = in_boundary_nodes[in_boundary_nodes['_merge'] == 'left_only'][[start_node_column, end_node_column]]
            
                start_segment = in_boundary_nodes[in_boundary_nodes[start_node_column] == in_boundary_nodes[start_node_column].min()][[start_node_column, end_node_column]].to_numpy(dtype=int)

                # put first segment value in dataframe with code = 1 i.e. Path.MoveTo
                out_df = pd.DataFrame(data=np.append(start_segment, 1).reshape(1,3), columns=[start_node_column, end_node_column, 'code'])

                # store first_start_node
                first_start_node = out_df[start_node_column].to_numpy()[0]

                # store end_node of segment
                previous_end_node = out_df.iloc[-1][end_node_column]
            else:
                next_segment = in_boundary_nodes[in_boundary_nodes[start_node_column] == previous_end_node][[start_node_column, end_node_column]].to_numpy()
                current_end_node = next_segment[0][-1]
    
                if current_end_node == first_start_node:
                    out_df = out_df.append(pd.DataFrame(data=np.append(next_segment, 79).reshape(1,3), columns=[start_node_column, end_node_column, 'code']), ignore_index=True)
                    df_list.append(out_df)
    
                else:
                    out_df = out_df.append(pd.DataFrame(data=np.append(next_segment, 2).reshape(1,3), columns=[start_node_column, end_node_column, 'code']), ignore_index=True)
    
                previous_end_node = current_end_node
    
        return pd.concat(df_list)