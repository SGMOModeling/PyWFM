import os
import ctypes
import math
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches

from iwfmdll.misc import IWFMMiscellaneous

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
        ''' returns the current simulation date and time 
        
        Returns
        -------
        str
            current date and time in IWFM format MM/DD/YYYY_hh:mm

        Notes
        -----
        1. the intent of this method is to retrieve information about the
        current time step when using the IWFM DLL to run a simulation. 
        i.e. IWFMModel object is instantiated with is_for_inquiry=0
        
        2. if this method is called when the IWFMModel object is 
        instantiated with is_for_inquiry=1, it only returns the 
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
        ''' returns the number of timesteps in an IWFM simulation 
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
           
        if not hasattr(self, "n_time_steps"):
            self.n_time_steps = n_time_steps

        return self.n_time_steps.value

    def get_time_specs(self):
        ''' returns the IWFM simulation dates and time step

        Returns
        -------
        tuple (length=2)
            list: simulation dates
            str: simulation time step 
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
        ''' returns a list of the possible time intervals a selected
        time-series data can be retrieved at.

        Returns
        -------
        list of strings
            list of available output intervals for given data type
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
        ''' returns the number of nodes in an IWFM model

        Returns
        -------
        int
            number of nodes specified in the IWFM model
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
        ''' returns the x,y coordinates of the nodes in an IWFM model
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
        ''' returns an array of node ids in an IWFM model
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
        ''' returns the number of elements in an IWFM model
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
        ''' returns an array of element ids in an IWFM model
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
        ''' returns an array of node ids for an IWFM element.
        The node ids are provided in a counter-clockwise direction

        Parameters
        ----------
        element_id : int
            single element ID for IWFM model. must be one of the values returned by
            get_element_ids method

        Returns
        -------
        np.array
            array of node IDs for element

        Notes
        -----
        In IWFM, elements can be composed of either 3 or 4 nodes. If 
        the element has 3 nodes, the fourth is returned as a 0.
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetElementConfigData"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetElementConfigData'))
        
        # check that element_id is an integer
        if not isinstance(element_id, (int, np.int, np.int32, np.dtype('<i4'))):
            raise TypeError('element_id must be an integer')

        # check that element_id is a valid element_id
        element_ids = self.get_element_ids()
        if not np.any(element_ids == element_id):
            raise ValueError('element_id is not a valid element ID')

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # set input variables
        element_id = ctypes.c_int(element_id)
        max_nodes_per_element = ctypes.c_int(4)

        # initialize output variables
        nodes_in_element = (ctypes.c_int*max_nodes_per_element.value)()

        self.dll.IW_Model_GetElementConfigData(ctypes.byref(element_id),
                                               ctypes.byref(max_nodes_per_element),
                                               nodes_in_element,
                                               ctypes.byref(self.status))

        return np.array(nodes_in_element)

    def get_n_subregions(self):
        ''' returns the number of subregions in an IWFM model
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
        ''' returns an array of IDs for subregions identifiedin the an IWFM model 
        
        Returns
        -------
        np.array
            integer array of length returned by method 'get_n_subregions'
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
        ''' returns the name corresponding to the subregion_id in an IWFM model 
        
        Parameters
        ----------
        subregion_id : int
            subregion identification number used to return name
            
        Returns
        -------
        str
            name of the subregion
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
            raise ValueError('subregion_id provided is not a valid subregion id. value provided {}. Must be one of: {}'.format(subregion_id, ' '.join(subregion_ids)))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # convert subregion_id to ctypes
        subregion_id = ctypes.c_int(subregion_id)

        # initialize name length as 50 characters
        length_name = ctypes.c_int(50)

        # initialize output variables
        subregion_name = ctypes.create_string_buffer(length_name.value)
        
        self.dll.IW_Model_GetSubregionName(ctypes.byref(subregion_id),
                                           ctypes.byref(length_name),
                                           subregion_name,
                                           ctypes.byref(self.status))

        return subregion_name.value.decode('utf-8')

    def get_subregions_by_element(self):
        ''' returns an array identifying the IWFM Model elements contained within each subregion.

        Returns
        -------
        np.array
            integer array of length returned by method 'get_n_elements'
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

        return np.array(element_subregions)

    def get_n_stream_nodes(self):
        ''' returns the number of stream nodes in an IWFM model
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
        ''' returns an array of stream node ids from the IWFM model application
        
        Returns
        -------
        np.array
            integer array of length returned by method 'get_n_stream_nodes' 
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

        return np.array(stream_node_ids)

    def get_n_stream_nodes_upstream_of_stream_node(self, stream_node_id):
        ''' returns the number of stream nodes immediately upstream of
        the provided stream node id
        
        Parameters
        ----------
        stream_node_id : int
            stream node id used to determine number of stream nodes upstream
            
        Returns
        -------
        int
            number of stream nodes immediately upstream of given stream node
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmNUpstrmNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetStrmNUpstrmNodes'))

        # check that stream_node_id is an integer
        if not isinstance(stream_node_id, int):
            raise TypeError('stream_node_id must be an integer')

        # check that stream_node_id is a valid stream_node_id
        stream_node_ids = self.get_stream_node_ids()
        if not np.any(stream_node_ids == stream_node_id):
            raise ValueError('stream_node_id is not a valid Stream Node ID')

        # set input variables
        stream_node_id = ctypes.c_int(stream_node_id)
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        n_upstream_stream_nodes = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmNUpstrmNodes(ctypes.byref(stream_node_id),
                                              ctypes.byref(n_upstream_stream_nodes),
                                              ctypes.byref(self.status))

        return n_upstream_stream_nodes.value

    def get_stream_nodes_upstream_of_stream_node(self, stream_node_id):
        ''' returns an array of the stream node ids immediately upstream
        of the provided stream node id
        
        Parameters
        ----------
        stream_node_id : int
            stream node id used to determine number of stream nodes upstream 
            
        Returns
        -------
        np.ndarray
            integer array of stream node ids upstream of the provided stream node id
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

        # set input variables
        stream_node_id = ctypes.c_int(stream_node_id)
        n_upstream_stream_nodes = ctypes.c_int(self.get_n_stream_nodes_upstream_of_stream_node(stream_node_id))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        upstream_nodes = (ctypes.c_int*n_upstream_stream_nodes.value)()

        self.dll.IW_Model_GetStrmUpstrmNodes(ctypes.byref(stream_node_id),
                                             ctypes.byref(n_upstream_stream_nodes),
                                             upstream_nodes,
                                             ctypes.byref(self.status))

        return np.array(upstream_nodes)

    def get_stream_bottom_elevations(self):
        ''' returns the stream channel bottom elevation at each stream node
        
        Returns
        -------
        np.ndarray
            array of float with the stream channel elevation for each stream node
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmBottomElevs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetStrmBottomElevs'))

        # set input variables
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # reset_instance variable status to -1
        self.status = ctypes.c_int(0)

        # initialize output variables
        stream_bottom_elevations = (ctypes.c_double*n_stream_nodes.value)()

        self.dll.IW_Model_GetStrmBottomElevs(ctypes.byref(n_stream_nodes),
                                             stream_bottom_elevations,
                                             ctypes.byref(self.status))
        
        return np.array(stream_bottom_elevations)

    def get_n_rating_table_points(self, stream_node_id):
        '''returns the number of data points in the stream flow rating 
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

        # set input variables convert to ctypes, if not already
        stream_node_id = ctypes.c_int(stream_node_id)

        # reset instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        n_rating_table_points = ctypes.c_int(0)

        self.dll.IW_Model_GetNStrmRatingTablePoints(ctypes.byref(stream_node_id),
                                                    ctypes.byref(n_rating_table_points),
                                                    ctypes.byref(self.status))

        return n_rating_table_points.value


    def get_stream_rating_table(self, stream_node_id):
        ''' returns the stream rating table for a specified stream node 
        
        Parameters
        ----------
        stream_node_id : int
            stream node id used to return the rating table
        
        Returns
        -------
        tuple
            length 2 tuple of np.ndarrays representing stage and flow, respectively
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmRatingTable"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetStrmRatingTable'))

        # check that stream_node_id is an integer
        if not isinstance(stream_node_id, (int, np.int, np.int32, np.dtype('<i4'))):
            raise TypeError('stream_node_id must be an integer')

        # check that stream_node_id is a valid stream_node_id
        stream_node_ids = self.get_stream_node_ids()
        if not np.any(stream_node_ids == stream_node_id):
            raise ValueError('stream_node_id is not a valid Stream Node ID')

        # set input variables
        stream_node_id = ctypes.c_int(stream_node_id)
        n_rating_table_points =ctypes.c_int(self.get_n_rating_table_points(stream_node_id.value))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        stage = (ctypes.c_double*n_rating_table_points.value)()
        flow = (ctypes.c_double*n_rating_table_points.value)()

        self.dll.IW_Model_GetStrmRatingTable(ctypes.byref(stream_node_id), 
                                             ctypes.byref(n_rating_table_points),
                                             stage,
                                             flow,
                                             ctypes.byref(self.status))

        return np.array(stage), np.array(flow)

    def get_n_stream_inflows(self):
        ''' returns the number of stream boundary inflows specified by the 
        user as timeseries input data

        Returns
        -------
        int
            number of stream boundary inflows
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
        ''' returns the indices of the stream nodes that receive boundary 
        inflows specified by the user as timeseries input data 
        
        Returns
        -------
        np.ndarray
            integer array of stream inflow node indices
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

        return np.array(stream_inflow_nodes)

    def get_stream_inflow_ids(self):
        ''' returns the identification numbers for the stream boundary 
        inflows specified by the user as timeseries input data 
        
        Returns
        -------
        np.ndarray
            integer array of stream inflow indices
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

    def get_stream_inflows_at_some_locations(self, stream_inflow_locations, inflow_conversion_factor=1.0):
        ''' returns stream boundary inflows at a specified set of inflow
        locations listed by their indices for the current simulation timestep
        
        Parameters
        ----------
        stream_inflow_locations : list of int
            one or more stream inflow ids used to return flows

        inflow_conversion_factor : float, default=1.0
            conversion factor for stream boundary inflows from the 
            simulation units of volume to a desired unit of volume

        Returns
        -------
        np.ndarray
            array of inflows for the inflow locations at the current 
            simulation time step

        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return
        stream inflows at the current timestep during a simulation.
        '''
        #if self.is_for_inquiry != 0:
        #    raise RuntimeError("This function can only be used when the model object is instantiated with the is_for_inquiry flag set to 0")

        if not hasattr(self.dll, "IW_Model_GetStrmInflows_AtSomeInflows"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmInflows_AtSomeInflows"))

        # initialize input variables
        n_stream_inflow_locations = ctypes.c_int(len(stream_inflow_locations))
        stream_inflow_locations = (ctypes.c_int*n_stream_inflow_locations.value)(*stream_inflow_locations)
        inflow_conversion_factor = ctypes.c_double(inflow_conversion_factor)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        inflows = (ctypes.c_double*n_stream_inflow_locations.value)()
                
        self.dll.IW_Model_GetStrmInflows_AtSomeInflows(ctypes.byref(n_stream_inflow_locations),
                                                       stream_inflow_locations,
                                                       ctypes.byref(inflow_conversion_factor),
                                                       inflows,
                                                       ctypes.byref(self.status))

        return np.array(inflows)

    def get_stream_flow_at_location(self, stream_node_id, flow_conversion_factor=1.0):
        ''' returns stream flow at a stream node for the current time
        step in a simulation 

        Parameters
        ----------
        stream_node_id : int
            stream node index where flow is retrieved

        flow_conversion_factor : float
            conversion factor for stream flows from the 
            simulation units of volume to a desired unit of volume

        Returns
        -------
        float
            stream flow at specified stream node
        
        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return
        a stream flow at the current timestep during a simulation.
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmFlow"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmFlow"))
        
        # convert input variables to ctypes
        stream_node_id = ctypes.c_int(stream_node_id)
        flow_conversion_factor = ctypes.c_double(flow_conversion_factor)

        # initialize output variables
        stream_flow = ctypes.c_double(0)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmFlow(ctypes.byref(stream_node_id),
                                      ctypes.byref(flow_conversion_factor),
                                      ctypes.byref(stream_flow),
                                      ctypes.byref(self.status))

        return stream_flow.value

    def get_stream_flows(self, flow_conversion_factor=1.0):
        ''' returns stream flows at every stream node for the current timestep 
        
        Parameters
        ----------
        flow_conversion_factor : float
            conversion factor for stream flows from the 
            simulation units of volume to a desired unit of volume

        Returns
        -------
        np.ndarray
            flows for all stream nodes for the current simulation timestep

        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return
        stream flows at the current timestep during a simulation.
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
        ''' returns stream stages at every stream node for the current timestep
        
        Parameters
        ----------
        stage_conversion_factor : float
            conversion factor for stream stages from the 
            simulation units of length to a desired unit of length

        Returns
        -------
        np.ndarray
            stages for all stream nodes for the current simulation timestep

        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return
        stream stages at the current timestep during a simulation.
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
        ''' returns small watershed inflows at every stream node for the current timestep
        
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

        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return
        small watershed inflows at the current timestep during a simulation.

        stream nodes without a small watershed draining to it will be 0
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
        ''' returns small watershed inflows at every stream node for the current timestep
        
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

        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return
        inflows from rainfall-runoff at the current timestep during a simulation.

        stream nodes without rainfall-runoff draining to it will be 0
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
        ''' returns agricultural and urban return flows at every stream
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

        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return
        return flows at the current timestep during a simulation.

        stream nodes without return flows will be 0
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
        ''' returns tile drain flows into every stream
        node for the current timestep
        
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

        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return
        tile drain flows at the current timestep during a simulation.

        stream nodes without tile drain flows will be 0
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
        ''' returns riparian evapotranspiration from every stream
        node for the current timestep
        
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

        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return
        riparian evapotranspiration at the current timestep during a 
        simulation.

        stream nodes without riparian evapotranspiration will be 0
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
        ''' returns gain from groundwater for every stream
        node for the current timestep
        
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

        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return
        gain from groundwater at the current timestep during a 
        simulation.

        stream nodes with gain from groundwater will be +
        stream nodes with loss to groundwater will be -
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
        ''' returns gain from lakes for every stream
        node for the current timestep
        
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

        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return
        gain from groundwater at the current timestep during a 
        simulation.

        stream nodes without gain from lakes will be 0
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
        ''' returns net bypass inflows for every stream
        node for the current timestep
        
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

        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return
        net bypass inflow to streams at the current timestep during a 
        simulation.

        stream nodes without net bypass inflow will be 0
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

    def get_actual_stream_diversions_at_some_locations(self, diversion_indices, diversion_conversion_factor):
        ''' returns actual diversion amounts for a list of diversions
        during a model simulation
        
        Parameters
        ----------
        diversion_indices : list of int, np.ndarray
            one or more diversion indices where actual diversions are
            returned. This is based on order not on the id used in the
            input file

        diversion_conversion_factor: float
            conversion factor for actual diversions from the simulation 
            unit of volume to a desired unit of volume
        
        Returns
        -------
        np.ndarray
            actual diversions for the diversion indices provided
        
        Notes
        -----
        This method is designed for use when is_for_inquiry=0 to return
        actual diversions amounts for selected diversion locations at 
        the current timestep during a simulation.

        Actual diversion amounts can be less than the required diversion 
        amount if stream goes dry at the stream node where the diversion 
        occurs
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmActualDiversions_AtSomeDiversions"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetStrmActualDiversions_AtSomeDiversions"))

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

    def get_stream_diversion_locations(self, diversion_locations):
        ''' returns the stream node indices corresponding to diversion locations

        Parameters
        ----------
        diversion_locations : list, tuple, np.ndarray
            integer array of diversion indices
        
        Returns
        -------
        np.ndarray
            integer array of stream node indices
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmDiversionsExportNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format("IW_Model_GetStrmDiversionsExportNodes"))

        # set input variables
        if isinstance(diversion_locations, (np.ndarray, tuple, list)):
            n_diversions = ctypes.c_int(len(diversion_locations))
            diversion_list = (ctypes.c_int*n_diversions.value)(*diversion_locations)
        
        elif isinstance(diversion_locations, str):
            if diversion_locations.lower() == 'all':
                n_diversions = ctypes.c_int(self.get_n_diversions())
                diversion_list = (ctypes.c_int*n_diversions.value)(*np.arange(1,n_diversions.value + 1))
            else:
                raise ValueError('diversion_locations must be a list, tuple, or np.ndarray or use "all"')
        else:
            raise TypeError('diversion_locations provided must be a list, tuple, or np.ndarray or use "all"')

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # initialize output variables
        diversion_stream_nodes = (ctypes.c_int*n_diversions.value)()

        self.dll.IW_Model_GetStrmDiversionsExportNodes(ctypes.byref(n_diversions),
                                                       diversion_list,
                                                       diversion_stream_nodes,
                                                       ctypes.byref(self.status))

        return np.array(diversion_stream_nodes)

    def get_n_stream_reaches(self):
        ''' returns the number of stream reaches in an IWFM model
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
        
        if not hasattr(self, "n_stream_reaches"):
            self.n_stream_reaches = n_stream_reaches
            
        return self.n_stream_reaches.value

    def get_stream_reach_ids(self):
        ''' returns the user-specified identification numbers for the
        stream reaches in an IWFM model 
        
        Returns
        -------
        stream reach_ids : np.ndarray of ints
            integer array containing stream reach ids
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

    def get_n_nodes_in_stream_reach(self, reach_index):
        ''' returns the number of stream nodes in a stream reach
        
        Parameters
        ----------
        reach_index : int
            stream reach index to obtain number of stream nodes. This 
            is not necessarily the same as the reach id 
            
        Returns
        -------
        int
            number of stream nodes specified in the stream reach    
        '''
        if not hasattr(self.dll, "IW_Model_GetReachNNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachNNodes"))

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

    def get_stream_reach_groundwater_nodes(self, reach_index):
        ''' returns the groundwater node indices corresponding to stream
        nodes in a specified reach 

        Parameters
        ----------
        reach_index : int
            stream reach index to obtain the corresponding groundwater nodes. This 
            is not necessarily the same as the reach id

        Returns
        -------
        np.ndarray
            integer array of groundwater node indices corresponding to
            stream reach
        '''
        if not hasattr(self.dll, "IW_Model_GetReachGWNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachGWNodes"))

        # convert reach index to ctypes
        reach_index = ctypes.c_int(reach_index)

        # get number of nodes in stream reach
        n_nodes_in_reach = ctypes.c_int(self.get_n_nodes_in_stream_reach(reach_index.value))

        # initialize output variables
        reach_groundwater_nodes = (ctypes.c_int*n_nodes_in_reach.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetReachGWNodes(ctypes.byref(reach_index),
                                          ctypes.byref(n_nodes_in_reach),
                                          reach_groundwater_nodes,
                                          ctypes.byref(self.status))

        return np.array(reach_groundwater_nodes)

    def get_stream_reach_stream_nodes(self, reach_index):
        ''' returns the stream node indices corresponding to stream
        nodes in a specified reach 

        Parameters
        ----------
        reach_index : int
            stream reach index to obtain the corresponding stream nodes. This 
            is not necessarily the same as the reach id

        Returns
        -------
        np.ndarray
            integer array of stream node indices corresponding to
            stream reach
        '''
        if not hasattr(self.dll, "IW_Model_GetReachStrmNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachStrmNodes"))

        # convert reach index to ctypes
        reach_index = ctypes.c_int(reach_index)

        # get number of nodes in stream reach
        n_nodes_in_reach = ctypes.c_int(self.get_n_nodes_in_stream_reach(reach_index.value))

        # initialize output variables
        reach_stream_nodes = (ctypes.c_int*n_nodes_in_reach.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetReachStrmNodes(ctypes.byref(reach_index),
                                            ctypes.byref(n_nodes_in_reach),
                                            reach_stream_nodes,
                                            ctypes.byref(self.status))

        return np.array(reach_stream_nodes)

    def get_stream_reaches_for_stream_nodes(self, stream_node_indices):
        ''' returns the stream reach indices that correspond to a list of stream nodes

        Parameters
        ---------
        stream_node_indices : list, np.ndarray
            list or array of stream node indices where the stream reach
            indices will be returned

        Returns
        -------
        np.ndarray
            array of stream reaches corresponding to stream node indices
        '''
        if not hasattr(self.dll, "IW_Model_GetReaches_ForStrmNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReaches_ForStrmNodes"))

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

        return np.array(stream_reaches)

    def get_upstream_nodes_in_stream_reaches(self):
        ''' returns the indices for the upstream stream node in each
        stream reach

        Returns
        -------
        np.ndarray
            array of stream node indices corresponding to the most 
            upstream stream node in each stream reach
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

        return np.array(upstream_stream_nodes)

    def get_n_reaches_upstream_of_reach(self, reach_index):
        ''' returns the number of stream reaches immediately upstream 
        of the specified reach

        Parameters
        ----------
        reach_index : int
            stream reach index to obtain the corresponding stream nodes. This 
            is not necessarily the same as the reach id

        Returns
        -------
        int
            number of stream reaches immediately upstream of specified
            stream reach.

        Notes
        -----
        if no stream reaches upstream, returns 0
        if reach downstream of confluence of tributaries, returns number 
        of tributaries
        otherwise, returns 1
        '''
        if not hasattr(self.dll, "IW_Model_GetReachNUpstrmReaches"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachNUpstrmReaches"))

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

    def get_reaches_upstream_of_reach(self, reach_index):
        ''' returns the indices of the reaches that are immediately 
        upstream of the specified reach

        Parameters
        ----------
        reach_index : int
            stream reach index to obtain the corresponding stream nodes. This 
            is not necessarily the same as the reach id

        Returns
        -------
        np.ndarray
            array of reach indices immediately upstream of the specified reach
        '''
        if not hasattr(self.dll, "IW_Model_GetReachUpstrmReaches"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format("IW_Model_GetReachUpstrmReaches"))

        # get the number of reaches upstream of the specified reach
        n_upstream_reaches = ctypes.c_int(self.get_n_reaches_upstream_of_reach(reach_index))

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

        return np.array(upstream_reaches)

    def get_downstream_node_in_stream_reaches(self):
        ''' returns the indices for the downstream stream node in each 
        stream reach

        Returns
        -------
        np.ndarray
            array of stream node indices for the downstream stream node
            in each stream reach
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
        
        return np.array(downstream_stream_nodes)

    def get_reach_outflow_destination(self):
        ''' This procedure returns the destination index that each stream
        reach flows into. To find out the type of destination (i.e. lake, 
        another stream node or outside the model domain) that the reaches 
        flow into, it is necessary to call IW_Model_GetReachOutflowDestType 
        procedure.

        Returns
        -------
        np.ndarray
            array of destination indices corresponding to the destination 
            of flows exiting each stream reach
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
        ''' returns the outflow destination types that each stream reach
        flows into.

        Returns
        -------
        np.ndarray
            array of destination types for each reach in the IWFM model
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
        ''' returns the number of surface water diversions in an IWFM model
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
        
        if not hasattr(self, "n_diversions"):
            self.n_diversions = n_diversions
            
        return self.n_diversions.value

    def get_diversion_ids(self):
        ''' returns the surface water diversion identification numbers
        specified in an IWFM model
        
        Returns
        -------
        np.ndarray
            integer array of diversion ids
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
        ''' returns the number of lakes in an IWFM model

        Returns
        -------
        int
            number of lakes in the IWFM model
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNLakes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNLakes'))

        # check if instance variable n_lakes already exists
        if hasattr(self, "n_lakes"):
            return self.n_lakes
            
        # initialize n_stream_reaches variable
        n_lakes = ctypes.c_int(0)
            
        # set instance variable status to 0
        self.status = ctypes.c_int(0)
        
        self.dll.IW_Model_GetNLakes(ctypes.byref(n_lakes),
                                    ctypes.byref(self.status))
        
        if not hasattr(self, "n_lakes"):
            self.n_lakes = n_lakes.value
            
        return n_lakes.value

    def get_lake_ids(self):
        ''' returns the lake identification numbers assigned by the user

        Returns
        -------
        np.ndarray
            array of lake identification numbers for each lake in the 
            model 
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
        ''' returns the number of finite element grid cells that make
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
        
        # convert lake id to ctypes
        lake_id = ctypes.c_int(lake_id)
        
        # initialize output variables
        n_elements_in_lake = ctypes.c_int(0)

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetNElementsInLake(ctypes.byref(lake_id),
                                             ctypes.byref(n_elements_in_lake),
                                             ctypes.byref(self.status))

        return n_elements_in_lake.value

    def get_elements_in_lake(self, lake_id):
        ''' returns the element ids in the lakes
        
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
        
        # convert lake id to ctypes
        lake_id = ctypes.c_int(lake_id)
        
        # get number of elements in lake
        n_elements_in_lake = ctypes.c_int(self.get_n_elements_in_lake(lake_id.value))

        # initialize output variables
        elements_in_lake = (ctypes.c_int*n_elements_in_lake.value)()

        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        self.dll.IW_Model_GetElementsInLake(ctypes.byref(lake_id),
                                            ctypes.byref(n_elements_in_lake),
                                            elements_in_lake,
                                            ctypes.byref(self.status))

        return np.array(elements_in_lake)

    def get_n_tile_drains(self):
        ''' returns the number of tile drain nodes in an IWFM model

        Returns
        -------
        int
            number of tile drains simulated in the IWFM model 
            application
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNTileDrainNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNTileDrainNodes'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
            
        # initialize n_stream_reaches variable
        n_tile_drains = ctypes.c_int(0)
            
        self.dll.IW_Model_GetNTileDrainNodes(ctypes.byref(n_tile_drains),
                                             ctypes.byref(self.status))
        
        if not hasattr(self, "n_tile_drains"):
            self.n_tile_drains = n_tile_drains.value
            
        return n_tile_drains.value

    def get_tile_drain_ids(self):
        ''' returns the user-specified identification numbers for tile
        drains simulated in an IWFM model

        Returns
        -------
        np.ndarray
            array of all tile drain identification number specified in
            an IWFM model
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
        ''' returns the node ids where tile drains are specified
        
        Returns
        -------
        np.ndarray
            array of node ids where tiles drains are specified
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

        return np.array(tile_drain_nodes)

    def get_n_layers(self):
        ''' returns the number of layers in an IWFM model

        Returns
        -------
        int
            number of layers specified in an IWFM model
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNLayers"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNLayers'))

        # set instance variable status to 0
        self.status = ctypes.c_int(0)
            
        # initialize n_layers variable
        n_layers = ctypes.c_int(0)
            
        self.dll.IW_Model_GetNLayers(ctypes.byref(n_layers),
                                     ctypes.byref(self.status))
        
        if not hasattr(self, "n_layers"):
            self.n_layers = n_layers.value
            
        return n_layers.value

    def get_ground_surface_elevation(self):
        ''' returns the ground surface elevation for each node specified 
        in the IWFM model

        Returns
        -------
        np.ndarray
            array of ground surface elevation at every finite element 
            node in an IWFM model
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetGSElev"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetGSElev'))
        
        # set instance variable status to 0
        self.status = ctypes.c_int(0)

        # get number of model nodes
        n_nodes = ctypes.c_int(self.get_n_nodes())

        # initialize output variables
        gselev = (ctypes.c_double*n_nodes.value)()
        
        self.dll.IW_Model_GetGSElev(ctypes.byref(n_nodes),
                                    gselev,
                                    ctypes.byref(self.status))
        
        return np.array(gselev)

    def get_aquifer_top_elevation(self):
        ''' returns the aquifer top elevations for each finite element 
        node and each layer

        Returns
        -------
        np.ndarray
            array of aquifer top elevations 
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
        ''' returns the aquifer top elevations for each finite element 
        node and each layer

        Returns
        -------
        np.ndarray
            array of aquifer top elevations 
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

    def get_stratigraphy_atXYcoordinate(self, x, y, fact, output_options=1):
        ''' returns the stratigraphy at a given X,Y coordinate and 
        conversion factor.

        Parameters
        ----------
        x : int, float
            x-coordinate for spatial location

        y : int, float
            y-coordinate for spatial location

        fact : int, float
            conversion factor for x,y coordinates to model length units
            
            e.g. if model units in feet and x,y coordinates are provided in 
            meters, then FACT=3.2808

        output_options : int, string, default=1
            selects how output is returned by the function
            Options
            -------
            None
            1 or 'combined'
            2 or 'gse'
            3 or 'tops'
            4 or 'bottoms'

        Returns
        -------
        if output_options == 1 or 'combined',
        np.array
            array contains the ground surface elevation and the bottoms of all layers
        
        if output_options == 2 or 'gse',
        float
            ground surface elevation at x,y coordinates
        
        if output_options == 3 or 'tops':
        np.array
            array containing the top elevations of each model layer

        if output_options == 4 or 'bottoms':
        np.array
            array containing the bottom elevations of each model layer
        
        if output_options is None or some other integer or string not defined above, 
        tuple : length 3
            ground surface elevation at x,y coordinates
            numpy array of top elevation of each layer
            numpy array of bottom elevation of each layer

        Notes
        -----
        ground surface elevation, elevations of the tops of each layer,
        and the elevations of the bottoms of each layer       
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
            
        # convert input variables to ctype equivalent
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
        if output_options is None:
            output = (gselev.value, np.array(top_elevs), np.array(bottom_elevs))
        elif output_options == 1 or output_options == 'combined':
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
        ''' returns the aquifer horizontal hydraulic conductivity for 
        each finite element node and each layer

        Returns
        -------
        np.ndarray
            array of aquifer horizontal hydraulic conductivity 
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
        ''' returns the aquifer vertical hydraulic conductivity for each finite element 
        node and each layer

        Returns
        -------
        np.ndarray
            array of aquifer vertical hydraulic conductivity 
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
        ''' returns the aquitard vertical hydraulic conductivity for 
        each finite element node and each layer

        Returns
        -------
        np.ndarray
            array of aquitard vertical hydraulic conductivity
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
        ''' returns the aquifer specific yield for each finite element 
        node and each layer

        Returns
        -------
        np.ndarray
            array of aquifer specific yield
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
        ''' returns the aquifer specific storage for each finite element 
        node and each layer

        Returns
        -------
        np.ndarray
            array of aquifer specific storage 
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
        ''' returns all aquifer parameters at each model node and layer 
        
        Returns
        -------
        tuple
            np.ndarray of aquifer horizontal hydraulic conductivity for each node and layer
            np.ndarray of aquifer vertical hydraulic conductivity for each node and layer
            np.ndarray of aquitard vertical hydraulic conductivity for each node and layer
            np.ndarray of aquifer specific yield for each node and layer
            np.ndarray of aquifer specific storage for each node and layer
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
        ''' returns the number of agricultural crops simulated in an 
        IWFM model

        Returns
        -------
        int
            number of agricultural crops (both non-ponded and ponded)
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

    def _get_supply_purpose(self, supply_type_id, supply_indices):
        ''' private method returning the flags for the initial assignment of water supplies
        (diversions, well pumping, element pumping) designating if they serve
        agricultural, urban, or both

        Parameters
        ----------
        supply_type_id : int
            supply type identification number used by IWFM for surface water
            diversions, well pumping, or element pumping

        supply_indices : list of int or np.ndarray
            indices of supplies for which flags are being retrieved. This is
            one or more identification numbers for the supply type chosen
            e.g. supply_type_id for diversions supply indices would be one or 
            more diversion ids.

        Returns
        -------
        np.ndarray
            array of flags for each supply index provided

        Notes
        -----
        flag equal to 10 for agricultural water demand
        flag equal to 01 for urban water demands
        flag equal to 11 for both ag and urban

        automatic supply adjustment in IWFM allows the supply purpose 
        to change dynamically, so this only returns the user-specified
        initial value.
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetSupplyPurpose"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetSupplyPurpose'))
        
        # convert supply_type_id to ctypes
        supply_type_id = ctypes.c_int(supply_type_id)
        
        # check that supply_indices are provided as a list or np.ndarray
        if not isinstance(supply_indices, (list, np.ndarray)):
            raise TypeError('supply_indices must be a list or np.ndarray')

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

    def get_diversion_purpose(self, diversion_indices):
        ''' returns the flags for the initial purpose of the water 
        supplies as ag, urban, or both

        Parameters
        ----------
        diversion_indices : list of int or np.ndarray
            One or more diversion identification numbers used to return
            the supply purpose.

        Returns
        -------
        np.ndarray
            array of flags for each supply index provided

        Notes
        -----
        flag equal to 10 for agricultural water demand
        flag equal to 01 for urban water demands
        flag equal to 11 for both ag and urban

        automatic supply adjustment in IWFM allows the supply purpose 
        to change dynamically, so this only returns the user-specified
        initial value. 
        '''
        supply_type_id = self.get_supply_type_id_diversion()

        return self._get_supply_purpose(supply_type_id, diversion_indices)

    def get_well_pumping_purpose(self, well_indices):
        ''' returns the flags for the initial purpose of the water 
        supplies as ag, urban, or both

        Parameters
        ----------
        well_indices : list of int or np.ndarray
            One or more well identification numbers used to return
            the supply purpose.

        Returns
        -------
        np.ndarray
            array of flags for each supply index provided

        Notes
        -----
        flag equal to 10 for agricultural water demand
        flag equal to 01 for urban water demands
        flag equal to 11 for both ag and urban

        automatic supply adjustment in IWFM allows the supply purpose 
        to change dynamically, so this only returns the user-specified
        initial value.
        '''
        supply_type_id = self.get_supply_type_id_well()

        return self._get_supply_purpose(supply_type_id, well_indices)

    def _get_supply_requirement_ag(self, location_type_id, locations_list, 
                                   conversion_factor):
        ''' returns the agricultural water supply requirement at a 
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

    def get_supply_requirement_ag_elements(self, elements_list, conversion_factor=1.0):
        ''' returns the agricultural supply requirement for one or more model elements

        Parameters
        ----------
        elements_list : list or np.ndarray
            one or more element identification numbers used to return 
            the ag supply requirement

        conversion_factor : float, default=1.0
            factor to convert ag supply requirement from model units to
            desired output units

        Returns
        -------
        np.ndarray
            array of ag supply requirement for elements specified
        '''
        location_type_id = self.get_location_type_id_element()

        return self._get_supply_requirement_ag(location_type_id, elements_list, conversion_factor)

    def get_supply_requirement_ag_subregions(self, subregions_list, conversion_factor=1.0):
        ''' returns the agricultural supply requirement for one or more model subregions

        Parameters
        ----------
        subregions_list : list or np.ndarray
            one or more subregion identification numbers used to return 
            the ag supply requirement

        conversion_factor : float, default=1.0
            factor to convert ag supply requirement from model units to
            desired output units

        Returns
        -------
        np.ndarray
            array of ag supply requirement for subregions specified
        '''
        location_type_id = self.get_location_type_id_subregion()

        return self._get_supply_requirement_ag(location_type_id, subregions_list, conversion_factor)

    def _get_supply_requirement_urban(self, location_type_id, locations_list, conversion_factor):
        ''' returns the urban water supply requirement at a 
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

    def get_supply_requirement_urban_elements(self, elements_list, conversion_factor=1.0):
        ''' returns the urban supply requirement for one or more model elements

        Parameters
        ----------
        elements_list : list or np.ndarray
            one or more element identification numbers used to return 
            the urban supply requirement

        conversion_factor : float, default=1.0
            factor to convert ag supply requirement from model units to
            desired output units

        Returns
        -------
        np.ndarray
            array of ag supply requirement for elements specified
        '''
        location_type_id = self.get_location_type_id_element()

        return self._get_supply_requirement_urban(location_type_id, 
                                                  elements_list, 
                                                  conversion_factor)

    def get_supply_requirement_urban_subregions(self, subregions_list, conversion_factor=1.0):
        ''' returns the urban supply requirement for one or more model subregions

        Parameters
        ----------
        subregions_list : list or np.ndarray
            one or more subregion identification numbers used to return 
            the urban supply requirement

        conversion_factor : float, default=1.0
            factor to convert ag supply requirement from model units to
            desired output units

        Returns
        -------
        np.ndarray
            array of ag supply requirement for subregions specified
        '''
        location_type_id = self.get_location_type_id_subregion()

        return self._get_supply_requirement_urban(location_type_id, 
                                                  subregions_list, 
                                                  conversion_factor)

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

    def get_ag_diversion_supply_shortage_at_origin(self, diversions_list, conversion_factor=1.0):
        ''' returns the supply shortage for agricultural diversions at the destination of those 
        supplies plus any conveyance losses
        
        Parameters
        ----------
        diversions_list : list or np.ndarray
            indices of diversions where ag supply shortages are returned

        conversion_factor : float, default=1.0
            factor to convert agricultural supply shortage from model 
            units to the desired output units

        Returns
        -------
        np.ndarray
            array of agricultural supply shortages for each diversion location
        '''
        supply_type_id = self.get_supply_type_id_diversion()

        return self._get_supply_shortage_at_origin_ag(supply_type_id, 
                                                      diversions_list, 
                                                      conversion_factor)

    def get_ag_well_supply_shortage_at_origin(self, wells_list, conversion_factor=1.0):
        ''' returns the supply shortage for agricultural wells at the destination of those 
        supplies plus any conveyance losses
        
        Parameters
        ----------
        wells_list : list or np.ndarray
            indices of wells where ag supply shortages are returned

        conversion_factor : float, default=1.0
            factor to convert agricultural supply shortage from model 
            units to the desired output units

        Returns
        -------
        np.ndarray
            array of agricultural supply shortages for each well location
        '''
        supply_type_id = self.get_supply_type_id_well()

        return self._get_supply_shortage_at_origin_ag(supply_type_id, 
                                                      wells_list, 
                                                      conversion_factor)

    def get_ag_elempump_supply_shortage_at_origin(self, elements_list, conversion_factor=1.0):
        ''' returns the supply shortage for agricultural element pumping 
        at the destination of those supplies plus any conveyance losses
        
        Parameters
        ----------
        elements_list : list or np.ndarray
            indices of element pumping locations where ag supply shortages are returned

        conversion_factor : float, default=1.0
            factor to convert agricultural supply shortage from model 
            units to the desired output units

        Returns
        -------
        np.ndarray
            array of agricultural supply shortages for each element pumping location
        '''
        supply_type_id = self.get_supply_type_id_elempump()

        return self._get_supply_shortage_at_origin_ag(supply_type_id, 
                                                      elements_list, 
                                                      conversion_factor)

    def _get_supply_shortage_at_origin_urban(self, supply_type_id, supply_location_list, supply_conversion_factor):
        ''' returns the supply shortage for agriculture at the destination of those 
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

    def get_urban_diversion_supply_shortage_at_origin(self, diversions_list, conversion_factor=1.0):
        ''' returns the supply shortage for urban diversions at the destination of those 
        supplies plus any conveyance losses
        
        Parameters
        ----------
        diversions_list : list or np.ndarray
            indices of diversions where urban supply shortages are returned

        conversion_factor : float, default=1.0
            factor to convert urban supply shortage from model 
            units to the desired output units

        Returns
        -------
        np.ndarray
            array of urban supply shortages for each diversion location
        '''
        supply_type_id = self.get_supply_type_id_diversion()

        return self._get_supply_shortage_at_origin_urban(supply_type_id, 
                                                         diversions_list, 
                                                         conversion_factor)

    def get_urban_well_supply_shortage_at_origin(self, wells_list, conversion_factor=1.0):
        ''' returns the supply shortage for urban wells at the destination of those 
        supplies plus any conveyance losses
        
        Parameters
        ----------
        wells_list : list or np.ndarray
            indices of wells where urban supply shortages are returned

        conversion_factor : float, default=1.0
            factor to convert urban supply shortage from model 
            units to the desired output units

        Returns
        -------
        np.ndarray
            array of urban supply shortages for each well location
        '''
        supply_type_id = self.get_supply_type_id_well()

        return self._get_supply_shortage_at_origin_urban(supply_type_id, 
                                                         wells_list, 
                                                         conversion_factor)

    def get_urban_elempump_supply_shortage_at_origin(self, elements_list, conversion_factor=1.0):
        ''' returns the supply shortage for urban element pumping 
        at the destination of those supplies plus any conveyance losses
        
        Parameters
        ----------
        elements_list : list or np.ndarray
            indices of element pumping locations where urban supply shortages are returned

        conversion_factor : float, default=1.0
            factor to convert urban supply shortage from model 
            units to the desired output units

        Returns
        -------
        np.ndarray
            array of urban supply shortages for each element pumping location
        '''
        supply_type_id = self.get_supply_type_id_elempump()

        return self._get_supply_shortage_at_origin_urban(supply_type_id, 
                                                         elements_list, 
                                                         conversion_factor)

    def _get_names(self, location_type_id):
        ''' returns the available names for a given feature_type

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

        # get location type id
        location_type_id = ctypes.c_int(location_type_id)

        # get number of location for specified location type
        if location_type_id.value == 8:
            num_names = ctypes.c_int(self.get_n_nodes())

        elif location_type_id.value == 2:
            num_names = ctypes.c_int(self.get_n_elements())

        elif location_type_id.value == 4:
            num_names = ctypes.c_int(self.get_n_subregions())

        elif location_type_id.value == 7:
            # need to determine if API call exists for this
            raise NotImplementedError

        elif location_type_id.value == 3:
            num_names = ctypes.c_int(self.get_n_lakes())

        elif location_type_id.value == 1:
            num_names = ctypes.c_int(self.get_n_stream_nodes())

        elif location_type_id.value == 11:
            num_names = ctypes.c_int(self.get_n_stream_reaches())

        elif location_type_id.value == 13:
            num_names = ctypes.c_int(self.get_n_tile_drains())

        elif location_type_id.value == 14:
            #self.get_n_small_watersheds()
            raise NotImplementedError

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
        ''' returns the subregions names specified
        in an IWFM model
        
        Returns
        -------
        list
            list of names for each subregion in the model 
        '''
        location_type_id = self.get_location_type_id_subregion()

        return self._get_names(location_type_id)

    def get_stream_reach_names(self):
        ''' returns the stream reach names specified in an IWFM model
        
        Returns
        -------
        list
            list of names for each stream reach in the model
        '''
        location_type_id = self.get_location_type_id_streamreach()

        return self._get_names(location_type_id)

    def get_groundwater_observation_names(self):
        ''' returns the groundwater head observation location names
        specified in an IWFM model

        Returns
        -------
        list
            list of names for each groundwater head observation location
        '''
        location_type_id = self.get_location_type_id_gwheadobs()

        return self._get_names(location_type_id)

    def get_stream_observation_names(self):
        ''' returns the stream flow observation location names specified
        in an IWFM model
        
        Returns
        -------
        list
            list of names for each stream observation location
        '''
        location_type_id = self.get_location_type_id_streamhydobs()

        return self._get_names(location_type_id)

    def get_subsidence_observation_names(self):
        ''' returns the subsidence observation location names specified
        in an IWFM model

        Returns
        -------
        list
            list of names for each subsidence observation locations
        '''
        location_type_id = self.get_location_type_id_subsidenceobs()

        return self._get_names(location_type_id)

    def get_n_hydrograph_types(self):
        ''' returns the number of different hydrograph types being
        printed by the IWFM model
        
        Returns
        -------
        int
            number of hydrograph types produced by the model
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
        ''' returns a list of different hydrograph types being printed
        by the IWFM model 
        
        Returns
        -------
        dict
            keys are different hydrograph types printed by the IWFM model
            values are corresponding hydrograph type ids
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
        ''' returns the number of groundwater hydrographs specified in
        an IWFM model

        Returns
        -------
        int
            number of groundwater hydrographs
        '''
        location_type_id = self.get_location_type_id_gwheadobs()

        return self._get_n_hydrographs(location_type_id)

    def get_n_subsidence_hydrographs(self):
        ''' returns the number of subsidence hydrographs specified in 
        an IWFM model

        Returns
        -------
        int
            number of subsidence hydrographs
        '''
        location_type_id = self.get_location_type_id_subsidenceobs()

        return self._get_n_hydrographs(location_type_id)

    def get_n_stream_hydrographs(self):
        ''' returns the number of stream flow hydrographs specified in
        an IWFM model

        Returns
        -------
        int
            number of stream hydrographs
        '''
        location_type_id = self.get_location_type_id_streamhydobs()

        return self._get_n_hydrographs(location_type_id)

    def get_n_tile_drain_hydrographs(self):
        ''' returns the number of tile drain hydrographs specified in 
        an IWFM model

        Returns
        -------
        int
            number of tile drain hydrographs
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
        ''' returns the ids for the groundwater hydrographs specified
        in an IWFM model

        Returns
        -------
        np.ndarray
            integer array of ids for groundwater hydrographs
        '''
        # get the location type id for groundwater head observations
        location_type_id = self.get_location_type_id_gwheadobs()

        return self._get_hydrograph_ids(location_type_id)

    def get_subsidence_hydrograph_ids(self):
        ''' returns the ids for the subsidence hydrographs specified
        in an IWFM model
        
        Returns
        -------
        np.ndarray
            integer array of ids for subsidence hydrographs
        '''
        # get the location type id for groundwater head observations
        location_type_id = self.get_location_type_id_subsidenceobs()

        return self._get_hydrograph_ids(location_type_id)

    def get_stream_hydrograph_ids(self):
        ''' returns the ids for the stream hydrographs specified
        in an IWFM model
        
        Returns
        -------
        np.ndarray
            integer array of ids for stream hydrographs
        '''
        # get the location type id for stream flow observations
        location_type_id = self.get_location_type_id_streamhydobs()

        return self._get_hydrograph_ids(location_type_id)

    def get_tile_drain_hydrograph_ids(self):
        ''' returns the ids for the tile drain hydrographs specified
        in an IWFM model
        
        Returns
        -------
        np.ndarray
            integer array of ids for tile drain hydrographs
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
        ''' returns the x,y-coordinates for the groundwater hydrographs
        specified in an IWFM model

        Returns
        -------
        tuple
            np.ndarray of x-coordinates
            np.ndarray of y-coordinates
        '''
        location_type_id = self.get_location_type_id_gwheadobs()

        return self._get_hydrograph_coordinates(location_type_id)

    def get_subsidence_observation_coordinates(self):
        ''' returns the x,y-coordinates for the subsidence observation
        locations specified in an IWFM model

        Returns
        -------
        tuple
            np.ndarray of x-coordinates
            np.ndarray of y-coordinates
        '''
        location_type_id = self.get_location_type_id_subsidenceobs()

        return self._get_hydrograph_coordinates(location_type_id)

    def get_stream_observation_coordinates(self):
        ''' returns the x,y-coordinates for the stream flow observation
        locations specified in an IWFM model

        Returns
        -------
        tuple
            np.ndarray of x-coordinates
            np.ndarray of y-coordinates
        '''
        location_type_id = self.get_location_type_id_streamhydobs()

        return self._get_hydrograph_coordinates(location_type_id)

    def get_tile_drain_observation_coordinates(self):
        ''' returns the x,y-coordinates for the tile drain observations
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
                raise ValueError('end_date was not found in the Budget file. use IWFMModel.get_time_specs() method to check.')

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
        ''' returns the simulated groundwater hydrograph for the 
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
        ''' returns the simulated groundwater hydrograph for the 
        provided groundwater hydrograph id

        Parameters
        ----------
        subsidence_location_id : int
            id for subsidence hydrograph location being retrieved
            
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
        hydrograph_type = self.get_location_type_id_subsidenceobs()
        layer_number = 1

        return self._get_hydrograph(hydrograph_type, subsidence_location_id, 
                                    layer_number, begin_date, end_date, 
                                    length_conversion_factor, volume_conversion_factor)

    def get_stream_hydrograph(self, stream_location_id, begin_date=None,
                              end_date=None, length_conversion_factor=1.0, 
                              volume_conversion_factor=1.0):
        ''' returns the simulated groundwater hydrograph for the 
        provided groundwater hydrograph id

        Parameters
        ----------
        stream_location_id : int
            id for subsidence hydrograph location being retrieved
            
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
        hydrograph_type = self.get_location_type_id_streamhydobs()
        layer_number = 1

        return self._get_hydrograph(hydrograph_type, stream_location_id, 
                                    layer_number, begin_date, end_date, 
                                    length_conversion_factor, volume_conversion_factor)

    def get_gwheads_foralayer(self, layer_number, begin_date=None, end_date=None, length_conversion_factor=1.0):
        ''' returns the simulated groundwater heads for a single user-specified model layer for
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

        Notes
        -----
        the interval between the begin_date and the end_date is determined from the model time interval
        using get_time_specs()

        Examples
        --------
        >>> model = IWFMModel(dll, preprocessor_file, simulation_file)

        >>>dates, heads = model.get_gwheadsall_foralayer(1, '09/30/1980_24:00', '09/30/2000_24:00')
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
        ''' returns the groundwater heads at all nodes in every aquifer 
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
        ''' returns the groundwater heads at all nodes in every aquifer 
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
        ''' returns subregional depth to groundwater values that are 
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
        ''' returns average depth to groundwater for user-defined zones

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
        ''' returns the number of locations for a specified location
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
        ''' returns the number of small watersheds specified in an IWFM
        model
        
        Returns
        -------
        int
            number of small watersheds
        '''
        location_type_id = self.get_location_type_id_smallwatershed()

        return self.get_n_locations(ctypes.byref(location_type_id))

    def get_location_ids(self, location_type_id):
        ''' returns the location identification numbers used by the 
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
        ''' returns the small watershed identification numbers specified
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
        ''' overwrites time series data for the current time step
        
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

        Notes
        -----
        This method is intended to be used when is_for_inquiry=0 during
        a model simulation 
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
        ''' returns model information for the groundwater hydrographs,
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
        ''' returns node id, x-, and y-coordinates for each node in an IWFM model
        '''
        # get array of node ids
        node_ids = self.get_node_ids()
        
        # get arrays of x- and y- coordinates for each node id
        x, y = self.get_node_coordinates()
        
        # create DataFrame object to manage node info
        node_info = pd.DataFrame({'NodeID': node_ids, 'X': x, 'Y': y})

        return node_info

    def get_element_info(self):
        ''' returns element configuration information for all 
        elements in an IWFM model
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
        ''' returns nodes that make up the boundary of an IWFM model

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
        ''' returns element configuration information including x-y 
        coordinates for nodes
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
        dts, heads = self.get_gwheadsall_foralayer(layer_number, begin_date, end_date)

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