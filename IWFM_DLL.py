import os
import datetime
import ctypes
import math
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches

class IWFM_Model:
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
        is_for_inquiry=1: when an instance of the IWFM_Model class is 
        created for the first time, the entire model object will be 
        available for returning data. A binary file will be generated 
        for quicker loading, if this binary file exists when subsequent 
        instances of the IWFM_Model object are created, not all functions
        will be available.

    Returns
    -------
    IWFM_Model Object
        instance of the IWFM_Model class and access to the IWFM Model Object 
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
            
        self.status = ctypes.c_int(-1)
            
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

    def __exit__(self):
        self.kill()
      
    def delete_inquiry_data_file(self):
        
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_DeleteInquiryDataFile"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_DeleteInquiryDataFile'))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)
        
        self.dll.IW_Model_DeleteInquiryDataFile(ctypes.byref(self.length_simulation_file_name),
                                                self.simulation_file_name,
                                                ctypes.byref(self.status))
            
    def kill(self):
        ''' terminates model object, closes files associated with model,
        and clears memory
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_Kill"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_Kill'))
        
        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)
        
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
        i.e. IWFM_Model object is instantiated with is_for_inquiry=0
        
        2. if this method is called when the IWFM_Model object is 
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

        # set instance variable status to -1
        self.status = ctypes.c_int(-1)

        self.dll.IW_Model_GetCurrentDateAndTime(ctypes.byref(length_date_string),
                                                current_date_string,
                                                ctypes.byref(self.status))

        return current_date_string.value.decode('utf-8')

    def get_n_time_steps(self):
        ''' returns the number of timesteps in an IWFM simulation 
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNTimeSteps"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNTimeSteps'))
        
        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # initialize n_nodes variable
        n_time_steps = ctypes.c_int(0)

        self.dll.IW_Model_GetNTimeSteps(ctypes.byref(n_time_steps),
                                    ctypes.byref(self.status))
           
        if not hasattr(self, "n_time_steps"):
            self.n_time_steps = n_time_steps

        return self.n_time_steps.value

    def get_time_specs(self):
        ''' returns the IWFM simulation dates and time step
        if the version of the DLL is prior or including IWFM 2015.0.1045,
        the simulation dates will only include the start and end date.
        
        For newer versions, simulation dates will include all dates in 
        the simulation. 
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetTimeSpecs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetTimeSpecs'))
            
        # get version of the DLL to determine functionality of GetTimeSpecs procedure
        dll_version = self.get_version()['IWFM Core']

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)
        
        if dll_version in ['2015.0.706', '2015.0.828', '2015.0.961', '2015.0.1045']:
            # set string length properties
            n_data = ctypes.c_int(2)
            length_dates = ctypes.c_int(32)
            length_ts_interval = ctypes.c_int(8)
            
        else:
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

        dates_list = IWFM_Model._string_to_list_by_array(raw_dates_string, 
                                                        delimiter_position_array, n_data)

        sim_time_step = simulation_time_step.value.decode('utf-8')

        return dates_list, sim_time_step

    def get_output_interval(self, feature_type, data_type_index):
        ''' returns a list of the possible time intervals a selected
        time-series data can be retrieved at.

        Parameters
        ----------
        feature_type : str
            valid feature type to obtain a location_type_id for feature

        data_type_index : int
            array index, i.e. 0-based (standard python) for data type 
            returned for feature_type by running get_data_list method

        Returns
        -------
        list of strings
            list of available output intervals for given data type
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetOutputIntervals"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetOutputIntervals'))

        # check that provided feature_type is valid
        IWFM_Model._validate_feature_type(feature_type)

        # get number of data for provided feature_type
        self.get_n_data_list(feature_type)

        # get data types for provided feature_type
        data_list = self.get_data_list(feature_type)

        # get sub data types for provided feature_type and data_type_index
        sub_data_list = self.get_sub_data_list(feature_type, data_type_index)

        if not sub_data_list:
            output_data_list = data_list
        else:
            output_data_list = sub_data_list

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # convert data_type_index to fortran-type (1-based)
        selected_data_index = ctypes.c_int(data_type_index + 1)

        # set length of output intervals character array to 160 or larger
        length_output_intervals = ctypes.c_int(160)

        # set maximum number of time intervals to 20 or larger
        max_num_time_intervals = ctypes.c_int(20)

        # initialize output variables
        output_intervals = ctypes.create_string_buffer(length_output_intervals.value)
        actual_num_time_intervals = ctypes.c_int(0)
        delimiter_position_array = (ctypes.c_int*max_num_time_intervals.value)()
            
        self.dll.IW_Model_GetOutputIntervals(ctypes.byref(selected_data_index), 
                                             output_intervals, 
                                             ctypes.byref(length_output_intervals),
                                             delimiter_position_array,
                                             ctypes.byref(max_num_time_intervals),
                                             ctypes.byref(actual_num_time_intervals),
                                             ctypes.byref(self.status))

        return output_data_list, IWFM_Model._string_to_list_by_array(output_intervals, delimiter_position_array, actual_num_time_intervals)
  
    def get_n_nodes(self):
        ''' returns the number of nodes in an IWFM model
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNNodes'))
        
        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

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

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

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

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

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

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

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
            
        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

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

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

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

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)
            
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

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # get number of model subregions
        n_subregions = ctypes.c_int(self.get_n_subregions())

        # initialize output variables
        subregion_ids = (ctypes.c_int*n_subregions.value)()
                
        self.dll.IW_Model_GetSubregionIDs(ctypes.byref(n_subregions),
                                                       subregion_ids,
                                                       self.status)

        return np.array(subregion_ids)

    def get_subregion_name(self, subregion_id):
        ''' returns the name corresponding to the subregion_id in an IWFM model '''

        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetSubregionName"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetSubregionName'))

        # check that subregion_id is an integer
        if not isinstance(subregion_id, (int, np.int, np.int32, np.dtype('<i4'))):
            raise TypeError('subregion_id must be an integer')

        # check that subregion_id is valid
        subregion_ids = self.get_subregion_ids()
        if subregion_id not in subregion_ids:
            raise ValueError('subregion_id provided is not a valid subregion id. value provided {}. Must be one of: {}'.format(subregion_id, ' '.join(subregion_ids)))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

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

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

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

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)
            
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

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # get number of stream nodes
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # initialize output variables
        stream_node_ids = (ctypes.c_int*n_stream_nodes.value)()

        self.dll.IW_Model_GetStrmNodeIDs(ctypes.byref(n_stream_nodes),
                                         stream_node_ids,
                                         ctypes.byref(self.status))

        return np.array(stream_node_ids)

    def get_n_stream_nodes_upstream_of_stream_node(self, stream_node_id):
        ''' returns the number of stream nodes upstream of the provided stream node id
        
        Parameters
        ----------
        stream_node_id : int
            stream node id used to determine number of stream nodes upstream
            
        Returns
        -------
        int
            number of stream nodes upstream of given stream node
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmNUpstrmNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetStrmNUpstreamNodes'))

        # check that stream_node_id is an integer
        if not isinstance(stream_node_id, (int, np.int, np.int32, np.dtype('<i4'))):
            raise TypeError('stream_node_id must be an integer')

        # check that stream_node_id is a valid stream_node_id
        stream_node_ids = self.get_stream_node_ids()
        if not np.any(stream_node_ids == stream_node_id):
            raise ValueError('stream_node_id is not a valid Stream Node ID')

        # set input variables
        stream_node_id = ctypes.c_int(stream_node_id)
        
        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # initialize output variables
        n_upstream_stream_nodes = ctypes.c_int(0)

        self.dll.IW_Model_GetStrmNUpstreamNodes(ctypes.byref(stream_node_id),
                                                ctypes.byref(n_upstream_stream_nodes),
                                                ctypes.byref(self.status))

        return n_upstream_stream_nodes.value

    def get_stream_nodes_upstream_of_stream_node(self, stream_node_id):
        ''' returns an array of the stream node ids upstream of the provided stream node id
        
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
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetStrmUpstrmNodes'))

        # check that stream_node_id is an integer
        if not isinstance(stream_node_id, (int, np.int, np.int32, np.dtype('<i4'))):
            raise TypeError('stream_node_id must be an integer')

        # check that stream_node_id is a valid stream_node_id
        stream_node_ids = self.get_stream_node_ids()
        if not np.any(stream_node_ids == stream_node_id):
            raise ValueError('stream_node_id is not a valid Stream Node ID')

        # set input variables
        stream_node_id = ctypes.c_int(stream_node_id)
        n_upstream_stream_nodes = ctypes.c_int(self.get_n_stream_nodes_upstream_of_stream_node(stream_node_id))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

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
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetStrmBottomElevs'))

        # set input variables
        n_stream_nodes = ctypes.c_int(self.get_n_stream_nodes())

        # reset_instance variable status to -1
        self.status = ctypes.c_int(-1)

        # initialize output variables
        stream_bottom_elevations = (ctypes.c_double*n_stream_nodes.value)()

        self.dll.IW_Model_GetStrmBottomElevs(ctypes.byref(n_stream_nodes),
                                             stream_bottom_elevations,
                                             ctypes.byref(self.status))
        
        return np.array(stream_bottom_elevations)

    def get_n_rating_table_points(self, stream_node_id):
        '''returns the number of data points in the stream flow rating table for a stream node

        Parameters
        ----------
        stream_node_id : int
            stream node id used to determine number of data points in the rating table

        Returns
        -------
        int
            number of data points in the stream flow rating table
        '''
        if not hasattr(self.dll, "IW_Model_GetNRatingTablePoints"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNRatingTablePoints'))

        # check that stream_node_id is an integer
        if not isinstance(stream_node_id, (int, np.int, np.int32, np.dtype('<i4'))):
            raise TypeError('stream_node_id must be an integer')

        # check that stream_node_id is a valid stream_node_id
        stream_node_ids = self.get_stream_node_ids()
        if not np.any(stream_node_ids == stream_node_id):
            raise ValueError('stream_node_id is not a valid Stream Node ID')

        # set input variables
        stream_node_id = ctypes.c_int(stream_node_id)

        # reset_instance variable status to -1
        self.status = ctypes.c_int(-1)

        # initialize output variables
        n_rating_table_points = ctypes.c_int(0)

        self.dll.IW_Model_GetNRatingTablePoints(ctypes.byref(stream_node_id),
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
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetStrmRatingTable'))

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

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

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
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format("IW_Model_GetStrmNInflows"))
        
        # set instance variable status to -1
        self.status = ctypes.c_int(-1)
        
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
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format("IW_Model_GetStrmInflowNodes"))
        
        # get number of stream inflow nodes
        n_stream_inflows = ctypes.c_int(self.get_n_stream_inflows())

        # set instance variable status to -1
        self.status = ctypes.c_int(-1)

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
            integer array of stream inflow node indices
        '''
        if not hasattr(self.dll, "IW_Model_GetStrmInflowIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format("IW_Model_GetStrmInflowIDs"))
        
        # get number of stream inflow nodes
        n_stream_inflows = ctypes.c_int(self.get_n_stream_inflows())

        # set instance variable status to -1
        self.status = ctypes.c_int(-1)

        # initialize output variables
        stream_inflow_ids = (ctypes.c_int*n_stream_inflows.value)()

        self.dll.IW_Model_GetStrmInflowIDs(ctypes.byref(n_stream_inflows),
                                             stream_inflow_ids,
                                             ctypes.byref(self.status))

        return np.array(stream_inflow_ids)

    def get_stream_inflows_at_some_locations(self, stream_inflow_locations):
        ''' returns user-specified stream boundary inflows at a specified
        set of inflows listed by their indices
        
        Parameters
        ----------
        stream_inflow_locations : int

        Returns
        -------

        Notes
        -----
        This method is designed to return stream inflows at the current
        timestep during a simulation.
        '''
        if self.is_for_inquiry != 0:
            raise RuntimeError("This function can only be used when the model object is instantiated with the is_for_inquiry flag set to 0")

        if not hasattr(self.dll, "IW_Model_GetStrmInflows_AtSomeInflows"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format("IW_Model_GetStrmInflows_AtSomeInflows"))

        # initialize output variables
        
        
        #self.dll.IW_Model_GetStrmInflows_AtSomeInflows()

    def get_stream_flow_at_location(self, stream_node_id, flow_conversion_factor):
        # is_for_inquiry=0
        pass

    def get_stream_flows(self):
        # is_for_inquiry=0
        pass

    def get_stream_stages(self):
        # is_for_inquiry=0
        pass

    def get_stream_tributary_inflows(self, inflow_conversion_factor):
        # is_for_inquiry=0
        pass

    def get_stream_rainfall_runoff(self, runoff_conversion_factor):
        # is_for_inquiry=0
        pass

    def get_stream_return_flows(self, return_flow_conversion_factor):
        # is_for_inquiry=0
        pass

    def get_stream_tile_drains(self, tile_drain_flow_conversion_factor):
        # is_for_inquiry=0
        pass

    def get_stream_riparian_evapotranspiration(self, evapotranspiration_conversion_factor):
        # is_for_inquiry=0
        pass

    def get_stream_gain_from_groundwater(self, stream_gain_conversion_factor):
        # is_for_inquiry=0
        pass

    def get_stream_gain_from_lakes(self, lake_inflow_conversion_factor):
        # is_for_inquiry=0
        pass

    def get_net_bypass_inflows(self, bypass_inflow_conversion_factor):
        # is_for_inquiry=0
        pass

    def get_actual_stream_diversions_at_some_locations(self, diversion_id, diversion_conversion_factor):
        # is_for_inquiry=0
        pass

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
                n_diversions = self.get_n_diversions()
                diversion_list = (ctypes.c_int*n_diversions.value)(*np.arange(1,n_diversions + 1))
            else:
                raise ValueError('diversion_locations must be a list, tuple, or np.ndarray or use "all"')
        else:
            raise TypeError('diversion_locations provided must be a list, tuple, or np.ndarray or use "all"')

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

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

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)
            
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
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format("IW_Model_GetReachIDs"))

        # set input variables
        n_stream_reaches = ctypes.c_int(self.get_n_stream_reaches())
        
        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # initialize output variables
        stream_reach_ids = (ctypes.c_int*n_stream_reaches.value)()

        self.dll.IW_Model_GetReachIDs(ctypes.byref(n_stream_reaches),
                                      stream_reach_ids,
                                      ctypes.byref(self.status))

        return np.array(stream_reach_ids)

    def get_n_nodes_in_stream_reach(self, reach_id):
        pass

    def get_stream_reach_groundwater_nodes(self, reach_id):
        pass

    def get_stream_reach_stream_nodes(self, reach_id):
        pass

    def get_stream_reaches_for_stream_nodes(self, stream_node_indices):
        pass

    def get_upstream_node_in_stream_reach(self):
        pass

    def get_n_reaches_upstream_of_reach(self, reach_id):
        pass

    def get_reaches_upstream_of_reach(self, reach_id):
        pass

    def get_downstream_node_in_stream_reach(self, reach_id):
        pass

    def get_reach_outflow_destination(self):
        pass

    def get_reach_outflow_destination_types(self):
        pass

    def get_n_diversions(self):
        ''' returns the number of surface water diversions in an IWFM model
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNDiversions"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_Model_GetNDiversions'))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)
            
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
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format("IW_Model_GetDiversionIDs"))

        # set input variables
        n_diversions = ctypes.c_int(self.get_n_diversions)
        
        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # initialize output variables
        diversion_ids = (ctypes.c_int*n_diversions.value)()

        self.dll.IW_Model_GetDiversionIDs(ctypes.byref(n_diversions),
                                          diversion_ids,
                                          ctypes.byref(self.status))

        return np.array(diversion_ids)

    def get_n_lakes(self):
        ''' returns the number of lakes in an IWFM model
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNLakes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNLakes'))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)
            
        # initialize n_stream_reaches variable
        n_lakes = ctypes.c_int(0)
            
        self.dll.IW_Model_GetNLakes(ctypes.byref(n_lakes),
                                    ctypes.byref(self.status))
        
        if not hasattr(self, "n_lakes"):
            self.n_lakes = n_lakes
            
        return self.n_lakes.value

    def get_lake_ids(self):
        pass

    def get_n_elements_in_lake(self, lake_id):
        pass

    def get_elements_in_lake(self, lake_id):
        pass

    def get_n_tile_drains(self):
        ''' returns the number of tile drain nodes in an IWFM model
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNTileDrainNodes"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNTileDrainNodes'))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)
            
        # initialize n_stream_reaches variable
        n_tile_drains = ctypes.c_int(0)
            
        self.dll.IW_Model_GetNTileDrainNodes(ctypes.byref(n_tile_drains),
                                             ctypes.byref(self.status))
        
        if not hasattr(self, "n_tile_drains"):
            self.n_tile_drains = n_tile_drains
            
        return self.n_tile_drains.value

    def get_tile_drain_ids(self):
        pass

    def get_tile_drain_nodes(self):
        pass

    def get_n_layers(self):
        ''' returns the number of layers in an IWFM model
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNLayers"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNLayers'))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)
            
        # initialize n_layers variable
        n_layers = ctypes.c_int(0)
            
        self.dll.IW_Model_GetNLayers(ctypes.byref(n_layers),
                                     ctypes.byref(self.status))
        
        if not hasattr(self, "n_layers"):
            self.n_layers = n_layers
            
        return self.n_layers.value

    def get_ground_surface_elevation(self):
        ''' returns the ground surface elevation for each node specified 
        in the IWFM model
        '''
        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # get number of model nodes
        num_nodes = ctypes.c_int(self.get_n_nodes())

        # initialize output variables
        gselev = (ctypes.c_double*num_nodes.value)()
        
        self.dll.IW_Model_GetGSElev(ctypes.byref(num_nodes),
                                    gselev,
                                    ctypes.byref(self.status))
        
        return np.array(gselev)

    def get_aquifer_top_elevation(self):
        pass

    def get_aquifer_bottom_elevation(self):
        pass

    def get_stratigraphy_atXYcoordinate(self, x, y, fact, output_options=1):
        ''' returns the ground surface elevation, elevations of the tops of each layer,
        and the elevations of the bottoms of each layer at a given X,Y coordinate and 
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
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetStratigraphy_AtXYCoordinate"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetStratigraphy_AtXYCoordinate'))

        if not isinstance(x, (int, float)):
            raise TypeError('X-coordinate must be an int or float')

        if not isinstance(y, (int, float)):
            raise TypeError('Y-coordinate must be an int or float')

        if not isinstance(fact, (int, float)):
            raise TypeError('conversion factor must be an int or float')

        if not isinstance(output_options, (int, str)):
            raise TypeError('output_options must be an integer or string')
        
        # reset instance variable status to -1 
        self.status = ctypes.c_int(-1)
            
        # convert input variables to ctype equivalent
        x = ctypes.c_double(x * fact)
        y = ctypes.c_double(y * fact)
            
        # initialize output variables
        gselev = ctypes.c_double(0.0)
        top_elevs = (ctypes.c_double*self.get_n_layers())()
        bottom_elevs = (ctypes.c_double*self.get_n_layers())()
        
    
        self.dll.IW_Model_GetStratigraphy_AtXYCoordinate(ctypes.byref(self.n_layers), 
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
        pass

    def get_aquifer_vertical_k(self):
        pass

    def get_aquitard_vertical_k(self):
        pass

    def get_aquifer_specific_yield(self):
        pass

    def get_aquifer_specific_storage(self):
        pass

    def get_aquifer_parameters(self):
        '''  '''
        pass

    def get_n_ag_crops(self):
        pass

    def get_supply_purpose(self, supply_type):
        pass

    def get_supply_requirement_ag(self, location_type, locations):
        pass

    def get_supply_requirement_urban(self, location_type, locations):
        pass

    def get_supply_shortage_at_origin_ag(self, supply_type, supply_list, supply_conversion_factor):
        pass

    def get_supply_shortage_at_origin_urban(self, supply_type, supply_list, supply_conversion_factor):
        pass

    def get_names(self, feature_type):
        ''' returns the available names for a given feature_type

         Parameters
        ----------
        feature_type : str
            valid feature type to obtain a location_type_id for feature

        Returns
        -------
        list of strings
            list containing names for the provided feature_type. Returns
            empty list if no names are available for given feature_type.
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNames"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNames'))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # get location type id
        location_type_id = self.get_location_type_id(feature_type)

        # get number of location for specified feature_type
        if feature_type.lower() == 'node':
            self.get_n_nodes()

        elif feature_type.lower() == 'element':
            self.get_n_elements()

        elif feature_type.lower() == 'subregion':
            self.get_n_subregions()

        elif feature_type.lower() == 'zone':
            # need to determine if API call exists for this
            raise NotImplementedError

        elif feature_type.lower() == 'lake':
            self.get_n_lakes()

        elif feature_type.lower() == 'stream_node':
            self.get_n_stream_nodes()

        elif feature_type.lower() == 'stream_reach':
            self.get_n_stream_reaches()

        elif feature_type.lower() == 'tile_drain':
            num_names = self.get_n_tile_drains()

        elif feature_type.lower() == 'small_watershed':
            #self.get_n_small_watersheds()
            raise NotImplementedError

        elif feature_type.lower() == 'gw_head_obs':
            num_names = ctypes.c_int(self.get_n_hydrographs(feature_type))

        elif feature_type.lower() == 'stream_hydrograph_obs':
            num_names = ctypes.c_int(self.get_n_hydrographs(feature_type))

        elif feature_type.lower() == 'subsidence_obs':
            num_names = ctypes.c_int(self.get_n_hydrographs(feature_type))

        # initialize output variables
        delimiter_position_array = (ctypes.c_int*num_names.value)()
        names_string_length = ctypes.c_int(30 * num_names.value)
        raw_names_string = ctypes.create_string_buffer(names_string_length.value)

        self.dll.IW_Model_GetNames(ctypes.byref(location_type_id),
                                   ctypes.byref(num_names), 
                                   delimiter_position_array,
                                   ctypes.byref(names_string_length),
                                   raw_names_string,
                                   ctypes.byref(self.status))

        return IWFM_Model._string_to_list_by_array(raw_names_string, delimiter_position_array, num_names)

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
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNHydrographTypes'))

        # initialize output variables
        n_hydrograph_types = ctypes.c_int(0)

        # set instance variable status to -1
        self.status = ctypes.c_int(-1)

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

        # set instance variable status to -1
        self.status = ctypes.c_int(-1)

        self.dll.IW_Model_GetHydrographTypeList(ctypes.byref(n_hydrograph_types),
                                                delimiter_position_array,
                                                ctypes.byref(length_hydrograph_type_list),
                                                raw_hydrograph_type_string,
                                                hydrograph_location_type_list,
                                                ctypes.byref(self.status))

        hydrograph_type_list = IWFM_Model._string_to_list_by_array(raw_hydrograph_type_string, delimiter_position_array, n_hydrograph_types)

        return dict(zip(hydrograph_type_list, np.array(hydrograph_location_type_list)))

    def get_n_hydrographs(self, feature_type):
        ''' returns the number of hydrographs for a given IWFM feature type
        
        Parameters
        ----------
        feature_type : str (case-insensitive)
            Valid feature types include:
                'tile_drain'
                'gw_head_obs'
                'stream_hydrograph_obs'
                'subsidence_obs'

            Other feature types will raise a ValueError

        Returns
        -------
        int
            number of hydrographs for the provided feature type

        Examples
        --------
        >>> num_hydrographs = IWFM_Model.get_n_hydrographs('gw_head_obs')
        >>> print(num_hydrographs)    
        43
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNHydrographs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNHydrographs'))

        if not isinstance(feature_type, str):
            raise TypeError('feature_type must be a string.')

        _valid_feature_types = ['tile_drain', 
                                'gw_head_obs', 
                                'stream_hydrograph_obs', 
                                'subsidence_obs']

        if feature_type.lower() not in _valid_feature_types:
            raise ValueError("invalid feature_type: {}. Must be:\n\t-{}".format(feature_type, '\n\t-'.join(_valid_feature_types)))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # initialize output variables
        n_hydrographs = ctypes.c_int(0)

        # get location type id for valid location types
        location_type_id = self.get_location_type_id(feature_type)

        self.dll.IW_Model_GetNHydrographs(ctypes.byref(location_type_id), 
                                          ctypes.byref(n_hydrographs), 
                                          ctypes.byref(self.status))

        return n_hydrographs.value

    def get_hydrograph_ids(self, feature_type):
        ''' returns the ids of the hydrographs for a provided feature_type

        Parameters
        ----------
        feature_type : str
            valid feature type to obtain a location_type_id for feature
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetHydrographIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetHydrographIDs'))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # get location type id. validation of feature_type internal to this function
        location_type_id = self.get_location_type_id(feature_type)

        # get number of hydrographs
        num_hydrographs = ctypes.c_int(self.get_n_hydrographs(feature_type))

        # initialize output variables
        hydrograph_ids = (ctypes.c_int*num_hydrographs.value)()

        self.dll.IW_Model_GetHydrographIDs(ctypes.byref(location_type_id),
                                           ctypes.byref(num_hydrographs),
                                           hydrograph_ids,
                                           ctypes.byref(self.status))
        
        return np.array(hydrograph_ids)

    def get_hydrograph_coordinates(self, feature_type):
        ''' returns the hydrograph coordinates for a provided feature type

        Parameters
        ----------
        feature_type : str
            valid feature type to obtain a location_type_id for feature

        Returns
        -------
        tuple : length 2
            index 0: np.array of x-coordinates of hydrographs
            index 1: np.array of y-coordinates of hydrographs 
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetHydrographCoordinates"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetHydrographCoordinates'))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # get location type id. validation of feature_type performed in this function
        location_type_id = self.get_location_type_id(feature_type)

        # get number of hydrographs
        num_hydrographs = ctypes.c_int(self.get_n_hydrographs(feature_type))

        # initialize output variables
        x = (ctypes.c_double*num_hydrographs.value)()
        y = (ctypes.c_double*num_hydrographs.value)() 

        self.dll.IW_Model_GetHydrographCoordinates(ctypes.byref(location_type_id), 
                                                   ctypes.byref(num_hydrographs), 
                                                   x, 
                                                   y, 
                                                   ctypes.byref(self.status))

        return np.array(x), np.array(y)

    def _get_hydrograph(self, hydrograph_type, hydrograph_id, layer_number=1, 
                        begin_date=None, end_date=None, length_conversion_factor=1.0, 
                        volume_conversion_factor=2.29568E-8):
        ''' returns a simulated hydrograph for a selected hydrograph type and hydrograph index 
        
        Parameters
        ----------
        hydrograph_type : int
            one of the available hydrograph types for the model retrieved using
            get_hydrograph_type_list method
            
        hydrograph_id : int
            id for hydrograph being retrieved
            
        layer_number : int, default=1
            layer number for returning hydrograph. only used for groundwater hydrograph
            at node and layer
            
        begin_date : str, default=None
            IWFM-style date for the beginning date of the simulated groundwater heads

        end_date : str, default=None
            IWFM-style date for the end date of the simulated groundwater heads

        length_conversion_factor : float, int, default=1.0
            hydrographs with units of length are multiplied by this
            value to convert simulation units to desired output units
            
        volume_conversion_factor : float, int, default=2.29568E-8
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
            IWFM_Model._validate_iwfm_date(begin_date)

            if begin_date not in dates_list:
                raise ValueError('begin_date was not recognized as a model time step. use IWFM_Model.get_time_specs() method to check.')
        
        if end_date is None:
            end_date = dates_list[-1]
        else:
            IWFM_Model._validate_iwfm_date(end_date)

            if end_date not in dates_list:
                raise ValueError('end_date was not found in the Budget file. use IWFM_Model.get_time_specs() method to check.')

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

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

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
        >>> model = IWFM_Model(dll, preprocessor_file, simulation_file)

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
            IWFM_Model._validate_iwfm_date(begin_date)

            if begin_date not in dates_list:
                raise ValueError('begin_date was not recognized as a model time step. use IWFM_Model.get_time_specs() method to check.')
        
        if end_date is None:
            end_date = dates_list[-1]
        else:
            IWFM_Model._validate_iwfm_date(end_date)

            if end_date not in dates_list:
                raise ValueError('end_date was not found in the Budget file. use IWFM_Model.get_time_specs() method to check.')

        if self.is_date_greater(begin_date, end_date):
            raise ValueError('end_date must occur after begin_date')
                
        # check that length conversion factor is a number
        if not isinstance(length_conversion_factor, (int, float)):
            raise TypeError('length_conversion_factor must be a number. value {} provides is of type {}'.format(length_conversion_factor, type(length_conversion_factor)))
        
        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

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

    def get_gwheads_all(self, end_of_timestep=True):
        # is_for_inquiry=0
        pass

    def get_subsidence_all(self, length_conversion_factor):
        # is_for_inquiry=0
        pass

    def get_subregion_ag_pumping_average_depth_to_water(self):
        # is_for_inquiry=0
        pass

    def get_zone_ag_pumping_average_depth_to_water(self):
        # is_for_inquiry=0
        pass

    def get_n_locations(self, location_type_id):
        pass

    def get_location_ids(self, location_type_id):
        pass

    def set_preprocessor_path(self, preprocessor_path):
        pass

    def set_simulation_path(self, simulation_path):
        pass

    def set_supply_adjustment_max_iterations(self, max_iterations):
        pass

    def set_supply_adjustment_tolerance(self, tolerance):
        pass

    def simulate_for_one_timestep(self):
        pass

    def simulate_for_an_interval(self):
        pass

    def simulate_all(self):
        pass

    def advance_time(self):
        pass

    def read_timeseries_data(self):
        pass

    def read_timeseries_data_overwrite(self):
        pass

    def print_results(self):
        pass

    def advance_state(self):
        pass

    def is_stream_upstream_node(self, stream_node_1, stream_node_2):
        pass

    def is_end_of_simulations(self):
        pass

    def is_model_instantiated(self):
        pass

    def turn_supply_adjustment_on_off(self, diversion_adjustment_flag, pumping_adjustment_flag):
        pass

    def restore_pumping_to_read_values(self):
        pass

    def is_date_greater(self, first_date, comparison_date):
        ''' returns True if first_date is greater than comparison_date

        Parameters
        ----------
        first_date : str
            IWFM format date MM/DD/YYYY_HH:MM

        comparison_date : str
            IWFM format date MM/DD/YYYY_HH:MM

        Returns
        -------
        boolean
            True if first_date is greater (in the future) when compared to the comparison_date
            False if first_date is less (in the past) when compared to the comparison_date 
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_IsTimeGreaterThan"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_IsTimeGreaterThan'))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)
           
        # convert begin and end dates to ctypes character arrays 
        first_date = ctypes.create_string_buffer(first_date.encode('utf-8'))
        comparison_date = ctypes.create_string_buffer(comparison_date.encode('utf-8'))

        # set length of IWFM date
        length_dates = ctypes.c_int(ctypes.sizeof(first_date))

        # initialize output variables
        compare_result = ctypes.c_int(0)
            
        self.dll.IW_IsTimeGreaterThan(ctypes.byref(length_dates),
                                      first_date,
                                      comparison_date,
                                      ctypes.byref(compare_result),
                                      ctypes.byref(self.status))

        if compare_result.value == -1:
            is_greater = False 
        elif compare_result.value == 1:
            is_greater = True

        return is_greater
    
    def get_n_intervals(self, begin_date, end_date, time_interval, includes_end_date=True):
        ''' returns the number of time intervals between a provided start date and end date

        Parameters
        ----------
        begin_date : str
            IWFM format date MM/DD/YYYY_HH:MM
        
        end_date : str
            IWFM format date MM/DD/YYYY_HH:MM

        time_interval : str
            valid IWFM time interval

        includes_end_date : boolean, default=True
            True adds 1 to the number of intervals to include the 
            end_date
            False is the number of intervals between the two dates 
            without including the end_date

        Returns
        -------
        int
            number of time intervals between begin and end date
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_GetNIntervals"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_GetNIntervals'))
        
        # check that begin_date is valid
        IWFM_Model._validate_iwfm_date(begin_date)
        
        # check that end_date is valid
        IWFM_Model._validate_iwfm_date(end_date)
        
        # check that time_interval is a valid IWFM time_interval
        IWFM_Model._validate_time_interval(time_interval)
        
        # check that begin_date is not greater than end_date
        if self.is_date_greater(begin_date, end_date):
            raise ValueError("begin_date must occur before end_date")
        
        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # convert IWFM dates to ctypes character arrays
        begin_date = ctypes.create_string_buffer(begin_date.encode('utf-8'))
        end_date = ctypes.create_string_buffer(end_date.encode('utf-8'))
        time_interval = ctypes.create_string_buffer(time_interval.encode('utf-8'))

        # set length of IWFM datetime string
        length_iwfm_date = ctypes.c_int(ctypes.sizeof(begin_date))

        # set length of IWFM time_interval string
        length_time_interval = ctypes.c_int(ctypes.sizeof(time_interval))

        # initialize output variables
        n_intervals = ctypes.c_int(0)

        self.dll.IW_GetNIntervals(begin_date,
                                  end_date,
                                  ctypes.byref(length_iwfm_date),
                                  time_interval,
                                  ctypes.byref(length_time_interval),
                                  ctypes.byref(n_intervals),
                                  ctypes.byref(self.status))
            
        if includes_end_date:
            return n_intervals.value + 1

        return n_intervals.value
       
    def _get_location_type_ids(self):
        ''' private method to generate dictionary of location type ids 
        for an IWFM model. Uses the IWFM DLL IW_GetLocationTypeIDs 
        function.

        Notes
        -----
        dictionary has a fixed set of keys:
        node,
        element, 
        subregion, 
        zone,
        lake, 
        stream_node, 
        stream_reach,
        tile_drain, 
        small_watershed,
        gw_head_obs,
        stream_hydrograph_obs,
        subsidence_obs
        
        dictionary values are ctypes data types and can be converted 
        to their python equivalent using the .value method

        e.g. 
        >>>location_type_ids['gw_head_obs']
          ctypes.c_long(9)
        >>>gw_head_obs.value
          9
        '''        
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_GetLocationTypeIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_GetLocationTypeIDs'))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)
            
        # initialize output variables
        location_type_id_node = ctypes.c_int(0)
        location_type_id_element = ctypes.c_int(0)
        location_type_id_subregion = ctypes.c_int(0)
        location_type_id_zone = ctypes.c_int(0)
        location_type_id_lake = ctypes.c_int(0)
        location_type_id_stream_node = ctypes.c_int(0)
        location_type_id_stream_reach = ctypes.c_int(0)
        location_type_id_tile_drain = ctypes.c_int(0)
        location_type_id_small_watershed = ctypes.c_int(0)
        location_type_id_gw_head_obs = ctypes.c_int(0)
        location_type_id_stream_hyd_obs = ctypes.c_int(0)
        location_type_id_subsidence_obs = ctypes.c_int(0)
           
        self.dll.IW_GetLocationTypeIDs(ctypes.byref(location_type_id_node),
                                       ctypes.byref(location_type_id_element),
                                       ctypes.byref(location_type_id_subregion),
                                       ctypes.byref(location_type_id_zone),
                                       ctypes.byref(location_type_id_lake),
                                       ctypes.byref(location_type_id_stream_node),
                                       ctypes.byref(location_type_id_stream_reach),
                                       ctypes.byref(location_type_id_tile_drain),
                                       ctypes.byref(location_type_id_small_watershed),
                                       ctypes.byref(location_type_id_gw_head_obs),
                                       ctypes.byref(location_type_id_stream_hyd_obs),
                                       ctypes.byref(location_type_id_subsidence_obs),
                                       ctypes.byref(self.status))
            
        self.location_type_ids = dict(
            node=location_type_id_node,
            element=location_type_id_element,
            subregion=location_type_id_subregion,
            zone=location_type_id_zone,
            lake=location_type_id_lake,
            stream_node=location_type_id_stream_node,
            stream_reach=location_type_id_stream_reach,
            tile_drain=location_type_id_tile_drain,
            small_watershed=location_type_id_small_watershed,
            gw_head_obs=location_type_id_gw_head_obs,
            stream_hydrograph_obs=location_type_id_stream_hyd_obs,
            subsidence_obs=location_type_id_subsidence_obs
            )
            
    def get_location_type_id(self, feature_type):
        ''' public function to return location type id from a valid IWFM feature type

        Parameters
        ----------
        feature_type : str
            must be one of the following strings (not case-sensitive):
                'node',
                'element', 
                'subregion', 
                'zone',
                'lake', 
                'stream_node', 
                'stream_reach',
                'tile_drain', 
                'small_watershed',
                'gw_head_obs',
                'stream_hydrograph_obs',
                'subsidence_obs'

        Returns
        -------
        ctypes.long
            id value of IWFM feature type
        '''
        IWFM_Model._validate_feature_type(feature_type)
        
        if not hasattr(self, 'location_type_ids'):
            self._get_location_type_ids()
        
        return self.location_type_ids[feature_type.lower()]

    def _get_data_unit_type_ids(self):
        ''' private method to generate dictionary of data unit type ids 
        for an IWFM model. Uses the IWFM DLL IW_GetDataUnitTypeIDs 
        function.

        Notes
        -----
        dictionary has a fixed set of keys:
        length,
        area, 
        volume 
        
        dictionary values are ctypes data types and can be converted 
        to their python equivalent using the .value method

        e.g. 
        >>>data_unit_type_ids['length']
          ctypes.c_long(0)
        >>>length_unit_id = data_unit_type_ids['length']
        >>>length_unit_id.value
          0
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_GetDataUnitTypeIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_GetDataUnitTypeIDs'))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)
            
        # initialize output variables
        data_unit_type_id_length = ctypes.c_int(0)
        data_unit_type_id_area = ctypes.c_int(0)
        data_unit_type_id_volume = ctypes.c_int(0)

        self.dll.IW_GetDataUnitTypeIDs(ctypes.byref(data_unit_type_id_length),
                                       ctypes.byref(data_unit_type_id_area),
                                       ctypes.byref(data_unit_type_id_volume),
                                       ctypes.byref(self.status))

        self.data_unit_type_ids = dict(
            length=data_unit_type_id_length,
            area=data_unit_type_id_area,
            volume=data_unit_type_id_volume
            )

    def get_data_unit_id(self, data_unit_type):
        ''' public function to return location type id from a valid IWFM feature type

        Parameters
        ----------
        feature_type : str
            must be one of the following strings (not case-sensitive):
                'length',
                'area', 
                'volume'

        Returns
        -------
        ctypes.long
            id value of IWFM data unit type
        '''
        _valid_unit_types = ['length', 
                             'area', 
                             'volume'
                            ]
        
        if data_unit_type.lower() not in _valid_unit_types:
            raise ValueError('feature_type must be one of the following types:\n' + 
                             ', '.join(_valid_unit_types))
        
        if not hasattr(self, 'data_unit_type_ids'):
            self._get_data_unit_type_ids()
        
        return self.data_unit_type_ids[data_unit_type.lower()]

    def _get_zone_extent_ids(self):
        ''' private method to generate dictionary of data unit type ids 
        for an IWFM model. Uses the IWFM DLL IW_GetDataUnitTypeIDs 
        function.

        Notes
        -----
        dictionary has a fixed set of keys:
        horizontal,
        vertical 
        
        dictionary values are ctypes data types and can be converted 
        to their python equivalent using the .value method

        e.g. 
        >>>zone_extent_ids['horizontal']
          ctypes.c_long(0)
        >>>length_unit_id = zone_extent_ids['horizontal']
        >>>length_unit_id.value
          0
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_GetZoneExtentIDs"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_GetZoneExtentIDs'))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # initialize output variables
        zone_extent_id_horizontal = ctypes.c_int(0)
        zone_extent_id_vertical = ctypes.c_int(0)

        self.dll.IW_GetZoneExtentIDs(ctypes.byref(zone_extent_id_horizontal),
                                     ctypes.byref(zone_extent_id_vertical),
                                     ctypes.byref(self.status))

        self.zone_extent_ids = dict(
            horizontal=zone_extent_id_horizontal,
            vertical=zone_extent_id_vertical
            )

    def get_zone_extent_id(self, zone_type):
        ''' public function to return zone extent id from a valid IWFM zone type

        Parameters
        ----------
        feature_type : str
            must be one of the following strings (not case-sensitive):
                'horizontal',
                'vertical'

        Returns
        -------
        ctypes.long
            id value of IWFM zone extent type
        '''
        # check that provided zone type is valid
        IWFM_Model._validate_zone_type(zone_type)
        
        if not hasattr(self, 'zone_extent_ids'):
            self._get_zone_extent_ids()
        
        return self.zone_extent_ids[zone_type.lower()]

    def get_n_data_list(self, feature_type):
        ''' returns the number of data types available for a given feature_type

        Parameters
        ----------
        feature_type : str
            valid feature type to obtain a location_type_id for feature

        Returns
        -------
        ctypes.c_long
            number of data types available
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetNDataList_AtLocationType"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetNDataList_AtLocationType'))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # get location type id
        location_type_id = self.get_location_type_id(feature_type)

        # initialize output variables
        n_data = ctypes.c_int(0)

        self.dll.IW_Model_GetNDataList_AtLocationType(ctypes.byref(location_type_id),
                                                      ctypes.byref(n_data),
                                                      ctypes.byref(self.status))

        return n_data

    def get_data_list(self, feature_type):
        ''' returns a list of data types for a given feature type

        Parameters
        ----------
        feature_type : str
            valid feature type to obtain a location_type_id for feature

        Returns
        -------
        list of strings
            list of data types available for feature
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetDataList_AtLocationType"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetDataList_AtLocationType'))
        
        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # get location type id
        location_type_id = self.get_location_type_id(feature_type)

        # set maximum number of data types to 20
        max_num_data_types = ctypes.c_int(20)
        #max_num_data_types = self.get_n_data_list(feature_type)

        # set maximum length for output data string to 3000 characters
        max_length_output_data_string = ctypes.c_int(3000)

        # initialize output variables
        n_data = ctypes.c_int(0)
        delimiter_position_array = (ctypes.c_int*max_num_data_types.value)()
        raw_data_string = ctypes.create_string_buffer(max_length_output_data_string.value)

        self.dll.IW_Model_GetDataList_AtLocationType(ctypes.byref(location_type_id),
                                                     ctypes.byref(n_data),
                                                     ctypes.byref(max_num_data_types),
                                                     delimiter_position_array,
                                                     ctypes.byref(max_length_output_data_string),
                                                     raw_data_string,
                                                     ctypes.byref(self.status))

        return IWFM_Model._string_to_list_by_array(raw_data_string, delimiter_position_array, n_data)

    def get_sub_data_list(self, feature_type, data_type_index):
        ''' returns a list of sub data types for a given feature type and data type

        Parameters
        ----------
        feature_type : str
            valid feature type to obtain a location_type_id for feature
        
        data_type_index : int
            array index, i.e. 0-based (standard python) for data type 
            returned for feature_type by running get_data_list method

        Returns
        -------
        list of strings
            list of available sub data types for given feature and data type
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetSubDataList_ForLocationAndDataType"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetSubDataList_ForLocationAndDataType'))

        # check that provided feature_type is valid
        IWFM_Model._validate_feature_type(feature_type)

        # check that provided data_type_index is int
        if not isinstance(data_type_index, int):
            raise TypeError('data_type_index must be an integer.')
        
        # check that provided data_type_index is valid
        n_data_types = self.get_n_data_list(feature_type)
        if data_type_index >= n_data_types.value:
            raise IndexError("data_type_index is out of range")

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # get location type id
        location_type_id = self.get_location_type_id(feature_type)

        # convert data_type_index to fortran-type (1-based)
        selected_data_index = ctypes.c_int(data_type_index + 1)

        # set max number of sub data types to 100
        max_sub_data_types = ctypes.c_int(100)

        # set max length of sub data types string to 3000
        max_length_output_sub_data_string = ctypes.c_int(3000)

        # initialize output variables
        n_data = ctypes.c_int(0)
        delimiter_position_array = (ctypes.c_int*max_sub_data_types.value)()
        raw_sub_data_string = ctypes.create_string_buffer(max_length_output_sub_data_string.value)

        self.dll.IW_Model_GetSubDataList_ForLocationAndDataType(ctypes.byref(location_type_id), 
                                                                ctypes.byref(selected_data_index),
                                                                ctypes.byref(n_data),
                                                                ctypes.byref(max_sub_data_types),
                                                                delimiter_position_array, 
                                                                ctypes.byref(max_length_output_sub_data_string),
                                                                raw_sub_data_string,
                                                                ctypes.byref(self.status))

        return IWFM_Model._string_to_list_by_array(raw_sub_data_string, delimiter_position_array, n_data)

    def get_model_data(self, feature_type, feature_id, data_type_index,
                       data_sub_type_index, begin_date, end_date, output_interval,
                       zone_type='horizontal',
                       length_zone_array='default',
                       elements_array=[],
                       layers_array=[],
                       zones_array=[], 
                       length_conversion_factor=1.0, 
                       area_conversion_factor=0.0000229568, 
                       volume_conversion_factor=0.0000000229568):
        ''' retrieves time-series simulation data at a selected location with a specified
        beginning and ending date and time interval.

        Parameters
        ----------
        feature_type : str
            valid feature type to obtain a location_type_id for feature

        feature_id : int
            valid id for given provided feature_type
            e.g. feature_type = 'subregion'
                 feature_id = subregion_id

        data_type_index : int
            array index, i.e. 0-based (standard python) for data type 
            returned for feature_type by running get_data_list method

        data_sub_type_index : int
            array index, i.e. 0-based (standard python) for data sub type
            returned for feature_type by running get_sub_data_list method.
            set equal to -1 if no data sub types exist

        begin_date : str
            IWFM format date for beginning of date range
            format: MM/DD/YYYY_HH:MM

        end_date : str
            IWFM format date for ending of date range
            format: MM/DD/YYYY_HH:MM

        output_interval : str
            IWFM format output interval e.g. '1MON'

        zone_type : str, default='horizontal'
            valid IWFM zone type. options: 'horizontal', 'vertical'

        length_zone_array : int, default = 'default'
            length of input arrays for elements, layers, and zones denoting 
            zone definitions. when feature_type is not equal to 'zone' this
            value is set to 0. when feature_type is equal to 'zone' and this
            value is 'default', length_zone_array is equal to the number of 
            elements.

        elements_array : list, tuple, np.ndarray
            array of length 'length_zone_array' containing element_ids for
            elements where zones are specified. this array is 0-length when
            feature_type is not equal to 'zone'. when length_zone_array is 
            equal to 'default', elements_array is an array of all element ids
            using the get_element_ids method

        layers_array : list, tuple, np.ndarray
            array of length 'length_zone_array' containing layer_ids for
            layers where zones are specified. this array is 0-length when
            'feature_type' is not equal to 'zone'. when 'zone_type' is equal
            to 'horizontal', this array is specified as all ones. Otherwise, 
            user needs to specify array.

        zones_array :  list, tuple, np.ndarray
            array of length 'length_zone_array' containing zone_ids where 
            zones are specified. this array is 0-length when feature_type 
            is not equal to 'zone'. Otherwise, user needs to specify array.

        length_conversion_factor : float, default = 1.0 (feet-->feet)
            unit conversion from model length units to desired output length units.

        area_conversion_factor : float, default = 2.29568E-05 (square_feet-->acres)
            unit conversion from model area units to desired output area units

        volume_conversion_factor : float, default = 2.29568E-08 (cubic_feet-->TAF)
            unit conversion from model volume units to desired output area units

        Returns
        -------
        length-2 tuple of np.ndarrays
            array of dates returned
            array of data returned

        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_Model_GetModelData_AtLocation"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Model_GetModeData_AtLocation'))
        
        # check that provided feature_type is valid
        IWFM_Model._validate_feature_type(feature_type)

        # check that provided feature_id is valid
        if not isinstance(feature_id, int):
            raise TypeError('feature_id must be an integer')

        # check that provided data_type_index is int
        if not isinstance(data_type_index, int):
            raise TypeError('data_type_index must be an integer.')
        
        # check that provided data_type_index is valid
        n_data_types = self.get_n_data_list(feature_type)
        if data_type_index >= n_data_types.value:
            raise IndexError("data_type_index is out of range")

        # check that data_sub_type_index is valid

        # check that begin_date is a valid iwfm date
        IWFM_Model._validate_iwfm_date(begin_date)

        # check that end_date is a valid iwfm date
        IWFM_Model._validate_iwfm_date(end_date)

        # check that output_interval is a valid iwfm output interval
        IWFM_Model._validate_time_interval(output_interval)

        # check zone type is valid
        IWFM_Model._validate_zone_type(zone_type)

        # check that elements_array, layers_array, and zones_array are a list, tuple, or np.ndarray
        if not isinstance(elements_array, (list, tuple, np.ndarray)):
            raise TypeError('elements_array must be a list, tuple, or np.ndarray')

        if not isinstance(layers_array, (list, tuple, np.ndarray)):
            raise TypeError('layers_array must be a list, tuple, or np.ndarray')

        if not isinstance(zones_array, (list, tuple, np.ndarray)):
            raise TypeError("zones_array must be a list, tuple, or np.ndarray")

        # check length, area, and volume conversion factors are floats

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # get location type id
        location_type_id = self.get_location_type_id(feature_type)

        # convert integer inputs to ctypes
        location_id = ctypes.c_int(feature_id)
        data_type_index = ctypes.c_int(data_type_index + 1)
        data_sub_type_index = ctypes.c_int(data_sub_type_index)

        # calculate size of output arrays. do this before converting to ctypes or will throw an error
        length_output_arrays = ctypes.c_int(self.get_n_intervals(begin_date, end_date, output_interval))

        # convert string inputs to ctypes character arrays
        begin_date = ctypes.create_string_buffer(begin_date.encode('utf-8'))
        end_date = ctypes.create_string_buffer(end_date.encode('utf-8'))
        output_interval = ctypes.create_string_buffer(output_interval.encode('utf-8'))

        # get lengths of dates and output interval
        length_dates = ctypes.c_int(ctypes.sizeof(begin_date))
        length_interval = ctypes.c_int(ctypes.sizeof(output_interval))

        # other input variables that need to be dealt with
        #iZExtent
        zone_extent_id = self.get_zone_extent_id(zone_type)
            
        #iDimZones - total number of model elements for which a zone is defined
        # only used if feature_type is zone, otherwise set to 0
        #iElems(iDimZones) - array of element ids for which a zone is specified
        # only used if feature_type is zone
        #iLayers(iDimZones) - array of model layers where the elements listed in iElems reside
        # only used if feature_type is zone. if IZExtent set to horizontal, set all values equal to 1
        #iZones(iDimZones) - array of zone numbers for the elements listed in the iElems array
        # only used if feature_type is zone
        if feature_type == 'zone':
            if length_zone_array == 'default':
                length_zone_array = self.get_n_elements()
                    
                elements_array = self.get_element_ids()
                    
                if zone_type == 'horizontal':
                    layers_array = (ctypes.c_int*length_zone_array.value)(*np.ones(length_zone_array.value))
                else:
                    if len(layers_array) != length_zone_array.value:
                        raise IndexError("layers_array must have length equal to {}".format(length_zone_array.value))
                    else:
                        # need to check that layer ids are valid
                        layers_array = (ctypes.c_int*length_zone_array.value)(*layers_array)

                if len(zones_array) != length_zone_array.value:
                    raise IndexError("zones_array must have length equal to {}".format(length_zone_array.value))
                else:
                    zones_array = (ctypes.c_int*length_zone_array.value)(*zones_array)
            else:
                length_zone_array = ctypes.c_int(length_zone_array)
                    
                if len(elements_array) != length_zone_array.value:
                    raise IndexError("elements_array must have length equal to {}".format(length_zone_array.value))
                else:
                    elements_array = (ctypes.c_int*length_zone_array.value)(*elements_array)
                    
                if zone_type == 'horizontal':
                    layers_array = (ctypes.c_int*length_zone_array.value)(*np.ones(length_zone_array.value))
                else:
                    if len(layers_array) != length_zone_array.value:
                        raise IndexError("layers_array must have length equal to {}".format(length_zone_array.value))
                    else:
                        # need to check that layer ids are valid
                        layers_array = (ctypes.c_int*length_zone_array.value)(*layers_array)

                if len(zones_array) != length_zone_array.value:
                    raise IndexError("zones_array must have length equal to {}".format(length_zone_array.value))
                else:
                    zones_array = (ctypes.c_int*length_zone_array.value)(*zones_array)
        else:
            # if feature_type is not 'zone' then arrays are 0-length
            length_zone_array = ctypes.c_int(0)
            elements_array = (ctypes.c_int*length_zone_array.value)()
            layers_array = (ctypes.c_int*length_zone_array.value)() 
            zones_array = (ctypes.c_int*length_zone_array.value)()

        #rFact_LT - conversion factor from model units to desired output units for length
        # default = 1.0 (feet-->feet)
        length_conversion_factor = ctypes.c_double(length_conversion_factor)

        #rFact_AR - conversion factor from model units to desired output units for area
        # default = 2.29568E-05 (square_feet-->acres)
        area_conversion_factor = ctypes.c_double(area_conversion_factor)
            
        #rFact_VL - conversion factor from model units to desired output units for volume
        # default - 2.29568E-08 (cubic_feet-->TAF)
        volume_conversion_factor = ctypes.c_double(volume_conversion_factor)
            
        # initialize output variables
        actual_length_output_arrays = ctypes.c_int(0)
        output_dates = (ctypes.c_double*length_output_arrays.value)()
        output_data = (ctypes.c_double*length_output_arrays.value)()
        output_data_unit_type = ctypes.c_int(0)


        self.dll.IW_Model_GetModelData_AtLocation(ctypes.byref(location_type_id),
                                                  ctypes.byref(location_id),
                                                  ctypes.byref(data_type_index),
                                                  ctypes.byref(data_sub_type_index),
                                                  ctypes.byref(zone_extent_id),
                                                  ctypes.byref(length_zone_array),
                                                  elements_array,
                                                  layers_array,
                                                  zones_array,
                                                  begin_date,
                                                  end_date,
                                                  ctypes.byref(length_dates),
                                                  output_interval,
                                                  ctypes.byref(length_interval),
                                                  ctypes.byref(length_conversion_factor),
                                                  ctypes.byref(area_conversion_factor),
                                                  ctypes.byref(volume_conversion_factor),
                                                  ctypes.byref(output_data_unit_type),
                                                  ctypes.byref(length_output_arrays),
                                                  ctypes.byref(actual_length_output_arrays),
                                                  output_dates,
                                                  output_data,
                                                  ctypes.byref(self.status))

        return np.array('1899-12-30', dtype='datetime64') + np.array(output_dates, dtype='timedelta64[D]'), np.array(output_data)
    
    def get_version(self):
        ''' returns the version of the IWFM DLL
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_GetVersion"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_GetVersion'))
        
        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # set version character array length to 500
        version_length = ctypes.c_int(600)

        # initialize output variables
        iwfm_version = ctypes.create_string_buffer(version_length.value)
        
        self.dll.IW_GetVersion(ctypes.byref(version_length),
                               iwfm_version,
                               ctypes.byref(self.status))

        iwfm_version_string = iwfm_version.value.decode('utf-8')

        iwfm_version_info = {val.split(':')[0]: val.split(':')[1].strip() for val in iwfm_version_string.split('\n')}

        return iwfm_version_info

    ### methods that wrap two or more DLL calls
    def get_hydrograph_info(self, feature_type):
        ''' returns model information for the hydrograph locations for the
        provided feature type, including hydrograph id, x- and y- coordinates, 
        name, and stratigraphy.

        Parameters
        ----------
        feature_type : str
            valid feature type to obtain a location_type_id for feature

        Returns
        -------
        pd.DataFrame
            columns: id, name, x, y, gse, bottom_layer1, bottom_layer2, ..., bottom_layern
        '''
        hydrograph_ids = self.get_hydrograph_ids(feature_type)
        hydrograph_x_coord, hydrograph_y_coord = self.get_hydrograph_coordinates(feature_type)
        hydrograph_names = self.get_names(feature_type)
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
            IWFM_Model._validate_iwfm_date(begin_date)

            if begin_date not in dates_list:
                raise ValueError('begin_date was not recognized as a model time step. use IWFM_Model.get_time_specs() method to check.')
        
        if end_date is None:
            end_date = dates_list[-1]
        else:
            IWFM_Model._validate_iwfm_date(end_date)

            if end_date not in dates_list:
                raise ValueError('end_date was not recognized as a model time step. use IWFM_Model.get_time_specs() method to check.')

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

    ### helper methods
    @staticmethod
    def _string_to_list_by_array(in_string, starting_position_array, length_output_list):
        ''' converts a string to a list of strings based on an
        array of the starting character position (index).

        Parameters
        ----------
        in_string : str or ctypes.Array (character array)
            input string that is converted to list of strings

        starting_position_array : np.array, list of ints, ctypes.Array
            array of starting character index for each value in list.

        length_output_list : int, ctypes.c_int, ctypes.c_long
            number of non-placeholder values in starting_position_array

        Returns
        -------
        list of strings
            input string (in_string) sliced into pieces based on array 
            of starting positions (starting_position_array)

        Notes
        -----
        length of starting_position_array will be the length of the output list
        '''
        # check that type of starting_position_array is a np.ndarray, list, tuple, or ctypes.Array
        if not isinstance(starting_position_array, (np.ndarray, list, tuple, ctypes.Array)):
            raise TypeError("starting_position_array must be a np.ndarray, list, tuple, ctypes.Array")

        # handle case where starting_position_array is a list, tuple, or ctypes.Array
        if isinstance(starting_position_array, (list, tuple, ctypes.Array)):
            
            # convert to a numpy array
            starting_position_array = np.array(starting_position_array)
            
        # check that all values are integers
        if starting_position_array.dtype not in (np.int, np.int32, np.dtype('<i4')):
            raise TypeError("All values in starting_position_array must be type: int.")

        # check that length_output_list is an integer
        if not isinstance(length_output_list, (int, ctypes.c_long, ctypes.c_int)):
            raise TypeError("length_output_list must be an int, ctypes.c_int, or ctypes.c_long.")

        # convert length_output_list to python integer
        if isinstance(length_output_list, (ctypes.c_long, ctypes.c_int)):
            length_output_list = length_output_list.value

        # check that in_string is a string
        if not isinstance(in_string, (str, ctypes.Array)):
            raise TypeError("in_string must be type string or ctypes.Array.\n" +
                            "Type given was {}".format(type(in_string)))

        # convert in_string to a python string if in_string is a ctypes character array
        if isinstance(in_string, ctypes.Array):
            in_string = in_string.value.decode('utf-8')

        # initialize empty list for values
        string_list = []
        
        # trim starting_position_array to length_output_list
        if length_output_list > 0:
            starting_position_array = starting_position_array[:length_output_list]

            # check if first value in array is 1
            if starting_position_array[0] == 1:
                # first python arrays are 0-indexed and the resulting delimiter_position_array
                # is 1-indexed (fortran-standard)
                position_array = starting_position_array - 1

            else:
                position_array = starting_position_array
            
            for i in range(len(position_array)):
                if position_array[i] != position_array[-1]:
                    string_list.append(in_string[position_array[i]:position_array[i+1]])
                else:
                    string_list.append(in_string[position_array[i]:])

        return string_list

    @staticmethod
    def _validate_iwfm_date(dt):
        ''' performs validation that a provided value is an IWFM-format date string based on
        string length and format MM/DD/YYYY_HH:MM

        Parameters
        ----------
        dt : str
            input value to check if IWFM-format date

        Returns
        -------
        None
            raises errors if validation checks do not pass
        '''
        if not isinstance(dt, str):
            raise TypeError('IWFM dates must be a string')
                    
        if len(dt) != 16:
            raise ValueError("IWFM dates must be 16 characters in length and of format MM/DD/YYYY_HH:MM")
                
        if '_' not in dt or dt.index('_') != 10:
            raise ValueError("IWFM dates must have an '_' separating the date and time")
                
        if ':' not in dt or dt.index(':') != 13:
            raise ValueError("IWFM dates must have an ':' separating the hours from minutes")
                
        if dt[2] != '/' or dt[5] != '/':
            raise ValueError("IWFM dates must use '/' as separators for the month, day, year in the date")
                
        try:
            datetime.datetime.strptime(dt, '%m/%d/%Y_%H:%M')
        except ValueError:
            try:
                datetime.datetime.strptime(dt.split('_')[0], '%m/%d/%Y')
            except ValueError:
                raise ValueError("Value provided: {} could not be converted to a date".format(dt))
            else:
                try:
                    hour = int(dt[11:13])
                    minute = int(dt[14:])
                except:
                    raise ValueError("hour or minute values are not numbers")
                else:
                    if hour < 0 or hour > 24:
                        raise ValueError("hour value is not between 00 and 24")
                            
                    if minute < 0 or minute > 59:
                        raise ValueError("minute value is not between 00 and 59")
                        
                    if hour == 24 and minute > 0:
                        raise ValueError("days cannot exceed 24:00 hours")

    @staticmethod
    def _validate_feature_type(feature_type):
        ''' performs validation that a provided feature_type is a valid IWFM feature type
        
        Parameters
        ----------
        feature_type : str
            value to be validated that it can be used to generate a location type id
            
        Returns
        -------
        None
            raises errors if validation checks do not pass
        '''
        # check input type is a string
        if not isinstance(feature_type, str):
            raise TypeError('feature_type must be a string. type entered is {}.'.format(type(feature_type)))
        
        # list of valid feature types
        _valid_feature_types = ['node',
                                'element',
                                'subregion', 
                                'zone',
                                'lake',
                                'stream_node',
                                'stream_reach',
                                'tile_drain',
                                'small_watershed',
                                'gw_head_obs',
                                'stream_hydrograph_obs',
                                'subsidence_obs']
        
        if feature_type.lower() not in _valid_feature_types:
            error_string = 'feature_type entered is not a valid IWFM feature type.\n' + \
                        'feature type must be:\n\t-{}'.format('\n\t-'.join(_valid_feature_types))
            raise ValueError(error_string)

    @staticmethod
    def _validate_time_interval(time_interval):
        ''' performs validation that a provided value is an IWFM-format time-interval string

        Parameters
        ----------
        time_interval : str (not case-sensitive)
            input value to check if IWFM-format time-interval

        Returns
        -------
        None
            raises errors if validation checks do not pass
        '''
        # check input type is a string
        if not isinstance(time_interval, str):
            raise TypeError('time_interval must be a string. type entered is {}.'.format(type(time_interval)))
            
        # list of valid time intervals
        _valid_time_intervals = ['1MIN',
                                '2MIN',
                                '3MIN',
                                '4MIN',
                                '5MIN',
                                '10MIN',
                                '15MIN',
                                '20MIN',
                                '30MIN',
                                '1HOUR',
                                '2HOUR',
                                '3HOUR',
                                '4HOUR',
                                '6HOUR',
                                '8HOUR',
                                '12HOUR',
                                '1DAY',
                                '1WEEK',
                                '1MON',
                                '1YEAR']
        
        if time_interval.upper() not in _valid_time_intervals:
            error_string = 'time_interval entered is not a valid IWFM time interval.\n' + \
                        'time_interval must be:\n\t-{}'.format('\n\t-'.join(_valid_time_intervals))
            raise ValueError(error_string)

    @staticmethod
    def _validate_zone_type(zone_type):
        '''checks to see if provided zone_type is a valid zone type to use
        for accessing the zone extent id
        
        Parameters
        ----------
        zone_type : str
            how zones are defined in an IWFM model. Can be either:
            horizontal or vertical.

        Returns
        -------
        None
            raises an error if the zone type is not valid
        '''
        if not isinstance(zone_type, str):
            raise TypeError('zone_type must be a string.')

        _valid_zone_types = ['horizontal', 
                             'vertical']
        
        if zone_type.lower() not in _valid_zone_types:
            raise ValueError('zone_type must be one of the following types:\n\t-' + 
                             '\n\t-'.join(_valid_zone_types))

    @staticmethod
    def _is_valid_feature_id(feature_id):
        pass

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


    def _has_data_list(self, feature_type):
        ''' checks to see if feature type has a data list associated with it

        Parameters
        ----------
        feature_type : str
            valid IWFM feature type

        Returns
        -------
        boolean
            True if there is a data list returned using feature_type
            False if empty list is returned
        '''
        # check that feature_type is valid
        IWFM_Model._validate_feature_type(feature_type)

        # retrieve data list
        data_list = self.get_data_list(feature_type)

        # check that list has values
        if not data_list:
            return False
        
        return True

    def _has_sub_data_list(self, feature_type, data_type_index):
        ''' checks to see if particular data type for an IWFM feature
        has a sub data list

        Parameters
        ----------
        feature_type : str
            valid IWFM feature type

        data_type_index : int
            index of a value in data list

        Returns
        -------
        boolean
            returns True if there is a sub data list returned
            returns False if there is an empty sub data list
        '''
        # check that feature_type is valid
        IWFM_Model._validate_feature_type(feature_type)

        # check that list has values
        if not self._has_data_list(feature_type):
            return False

        sub_data_list = self.get_sub_data_list(feature_type, data_type_index)

        if not sub_data_list:
            return False

        return True

class IWFM_Budget:
    ''' IWFM Budget Class for interacting with the IWFM DLL

    Parameters
    ----------
    dll_path : str
        file path and name of the IWFM DLL to access IWFM procedures

    budget_file_name : str
        file path and name of the budget file

    Returns
    -------
    IWFM_Budget Object
        instance of the IWFM_Budget class and access to the IWFM Budget 
        fortran procedures.
    '''
    def __init__(self, dll_path, budget_file_name):
        if not isinstance(dll_path, str):
            raise TypeError('dll path provided: {} is not a string'.format(dll_path))
        
        self.dll_path = dll_path
        self.budget_file_name = budget_file_name

        self.dll = ctypes.windll.LoadLibrary(self.dll_path)

        # check to see if the open file procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_Budget_OpenFile'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Budget_OpenFile'))

        # set input variables name and name length
        budget_file = ctypes.create_string_buffer(self.budget_file_name.encode('utf-8'))
        length_file_name = ctypes.c_int(ctypes.sizeof(budget_file))
        
        # initialize output variable status
        status = ctypes.c_int(-1)

        self.dll.IW_Budget_OpenFile(budget_file,
                                    ctypes.byref(length_file_name),
                                    ctypes.byref(status))

    def __enter__(self):
        return self

    def __exit__(self):
        self.close_budget_file()

    def close_budget_file(self):
        ''' closes an open budget file for an IWFM model application '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_Budget_CloseFile'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Budget_CloseFile'))
        
        # initialize output variable status
        status = ctypes.c_int(-1)

        self.dll.IW_Budget_CloseFile(ctypes.byref(status))

    def get_n_locations(self):
        ''' returns the number of locations where budget data is available
        e.g. if it is a stream reach budget, this is the number of stream reaches
             if it is a groundwater budget, this is the number of subregions 
             
        Returns
        -------
        int
            number of locations
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_Budget_GetNLocations'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Budget_GetNLocations'))
        
        # initialize output variables
        n_locations = ctypes.c_int(0)
        status = ctypes.c_int(-1)


        self.dll.IW_Budget_GetNLocations(ctypes.byref(n_locations),
                                         ctypes.byref(status))

        return n_locations.value

    def get_location_names(self):
        ''' retrieves the location names e.g. subregion names, lake names, etc.
        from the open budget file 
        
        Returns
        -------
        list
            list of names for the locations 
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_Budget_GetLocationNames'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Budget_GetLocationNames'))
        
        # get number of locations
        n_locations = ctypes.c_int(self.get_n_locations())

        # set length of location names string to 30 times the number of
        #  locations per IWFM DLL programmers guide
        location_names_length = ctypes.c_int(30 * n_locations.value)
        raw_names_string = ctypes.create_string_buffer(location_names_length.value)
        delimiter_position_array = (ctypes.c_int*location_names_length.value)()
        
        status = ctypes.c_int(-1)
        
        # IW_Budget_GetLocationNames(cLocNames,iLenLocNames,NLocations,iLocArray,iStat)
        self.dll.IW_Budget_GetLocationNames(raw_names_string,
                                            ctypes.byref(location_names_length),
                                            ctypes.byref(n_locations),
                                            delimiter_position_array,
                                            ctypes.byref(status))

        return IWFM_Budget._string_to_list_by_array(raw_names_string, delimiter_position_array, n_locations)

    def get_n_time_steps(self):
        ''' returns the number of time steps where budget data is available 
        
        Returns
        -------
        int
            number of time steps
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_Budget_GetNTimeSteps'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Budget_GetNTimeSteps'))

        n_time_steps = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        # IW_Budget_GetNTimeSteps(NTimeSteps,iStat)
        self.dll.IW_Budget_GetNTimeSteps(ctypes.byref(n_time_steps),
                                         ctypes.byref(status))

        return n_time_steps.value

    def get_time_specs(self):
        ''' returns a list of all the time stamps and the time interval for the budget 
        
        Returns
        -------
        length-2 tuple
            time stamps (list), time interval (string)
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_Budget_GetTimeSpecs'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Budget_GetTimeSpecs'))

        # get number of time steps
        n_time_steps = ctypes.c_int(self.get_n_time_steps())

        # set the length of the dates string to 16 times n_timesteps
        length_date_string = ctypes.c_int(16 * n_time_steps.value)

        # set the length of the time interval
        length_time_interval = ctypes.c_int(8)

        # initialize output variables
        raw_dates_string = ctypes.create_string_buffer(length_date_string.value)
        time_interval = ctypes.create_string_buffer(length_time_interval.value)
        delimiter_position_array = (ctypes.c_int*n_time_steps.value)()
        status = ctypes.c_int(-1)

        # IW_Budget_GetTimeSpecs(cDataDatesAndTimes,iLenDates,cInterval,iLenInterval,NData,iLocArray,iStat)
        self.dll.IW_Budget_GetTimeSpecs(raw_dates_string,
                                        ctypes.byref(length_date_string),
                                        time_interval,
                                        ctypes.byref(length_time_interval),
                                        ctypes.byref(n_time_steps),
                                        delimiter_position_array,
                                        ctypes.byref(status))

        dates_list = IWFM_Budget._string_to_list_by_array(raw_dates_string, delimiter_position_array, n_time_steps)

        interval = time_interval.value.decode('utf-8')

        return dates_list, interval 
    
    def get_n_title_lines(self):
        ''' returns the number of title lines for a water budget of a location 
        
        Returns
        -------
        int
            number of title lines
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_Budget_GetNTitleLines'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Budget_GetNTitleLines'))

        # initialize output variables
        n_title_lines = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        # IW_Budget_GetNTitleLines(NTitles,iStat)
        self.dll.IW_Budget_GetNTitleLines(ctypes.byref(n_title_lines),
                                          ctypes.byref(status))

        return n_title_lines.value

    def get_title_length(self):
        ''' retrieves the length of the title lines
        
        Returns
        -------
        int
            number of characters that make up the title lines
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_Budget_GetTitleLength'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Budget_GetTitleLength'))
        
        # initialize output variables
        title_length = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        # IW_Budget_GetTitleLength(iLen,iStat)
        self.dll.IW_Budget_GetTitleLength(ctypes.byref(title_length),
                                          ctypes.byref(status))

        return title_length.value

    def get_title_lines(self, location_id, area_conversion_factor=2.295684E-05, length_units='ft', 
                        area_units='Acres', volume_units='TAF', alternate_location_name=None):
        ''' returns the title lines for the budget data for a location to be displayed in the files 
        
        Parameters
        ----------
        location_id : int
            ID for location (1 to number of locations)
            
        area_conversion_factor : float, default=2.295684E-05 -> ft to acres
            factor to convert budget file area units to user desired output area units
            note: only the area shows up in the title lines

        length_units : str, default='ft'
            units of length used in the budget results

        area_units : str, default='Acres'
            units of area used in the budget results

        volume_units : str, default='TAF'
            units of volume used in the budget results

        alternate_location_name : str, default=None
            alternate name for location given by the location_id

        Returns
        -------
        list
            titles generated for the Budget
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_Budget_GetTitleLines'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Budget_GetTitleLines'))
        
        # get the number of title lines
        n_title_lines = ctypes.c_int(self.get_n_title_lines())
        
        # get number of locations
        n_locations = self.get_n_locations()

        # check that location_id is a number between 1 and n_locations
        if location_id not in [i+1 for i in range(n_locations)]:
            raise ValueError('location_id is not valid. Must be a value between 1 and {}.'.format(n_locations))

        # convert the location_id to ctypes
        location_id = ctypes.c_int(location_id)

        # set length of the units string to the maximum of the length, area, and volume units
        units_length = ctypes.c_int(max(len(length_units), len(area_units), len(volume_units)))
        
        # convert units to ctypes strings
        length_units = ctypes.create_string_buffer(length_units.encode('utf-8'))
        area_units = ctypes.create_string_buffer(area_units.encode('utf-8'))
        volume_units = ctypes.create_string_buffer(volume_units.encode('utf-8')) 

        # convert area conversion factor to ctypes
        area_conversion_factor = ctypes.c_double(area_conversion_factor)

        # get title length
        title_length = ctypes.c_int(self.get_title_length())

        # handle alternate location name
        if alternate_location_name is None:
            alternate_location_name = ctypes.create_string_buffer(''.encode('utf-8'))
        else:
            alternate_location_name = ctypes.create_string_buffer(alternate_location_name.encode('utf-8'))

        length_alternate_location_name = ctypes.c_int(ctypes.sizeof(alternate_location_name))

        # compute total length of all lines of the title
        length_titles = ctypes.c_int(title_length.value * n_title_lines.value)

        # initialize output variables
        raw_title_string = ctypes.create_string_buffer(length_titles.value)
        delimiter_position_array = (ctypes.c_int*n_title_lines.value)()
        status = ctypes.c_int(-1)


        # IW_Budget_GetTitleLines(NTitles,iLocation,FactArea,LengthUnit,AreaUnit,VolumeUnit,iLenUnit,
        #                         cAltLocName,iLenAltLocName,cTitles,iLenTitles,iLocArray,iStat)
        self.dll.IW_Budget_GetTitleLines(ctypes.byref(n_title_lines),
                                         ctypes.byref(location_id),
                                         ctypes.byref(area_conversion_factor),
                                         length_units,
                                         area_units,
                                         volume_units,
                                         ctypes.byref(units_length),
                                         alternate_location_name,
                                         ctypes.byref(length_alternate_location_name),
                                         raw_title_string,
                                         ctypes.byref(length_titles),
                                         delimiter_position_array,
                                         ctypes.byref(status))

        return IWFM_Budget._string_to_list_by_array(raw_title_string, delimiter_position_array, n_title_lines)

    def get_n_columns(self, location_id):
        ''' retrieves the number of budget data columns for a specified location
        
        Parameters
        ----------
        location_id : int
            location identification number e.g. subregion number, lake number, stream reach number
            where budget data is being retrieved
            
        Returns
        -------
        int
            number of budget data columns 
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_Budget_GetNColumns'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Budget_GetNColumns'))
        
        # get number of locations
        n_locations = self.get_n_locations()
        
        # check that location_id is a number between 1 and n_locations
        if location_id not in [i+1 for i in range(n_locations)]:
            raise ValueError('location_id is not valid. Must be a value between 1 and {}.'.format(n_locations))

        # convert location_id to ctypes
        location_id = ctypes.c_int(location_id)

        # initialize output variables
        n_columns = ctypes.c_int(0)
        status = ctypes.c_int(-1)
        
        # IW_Budget_GetNColumns(iLoc,NColumns,iStat)
        self.dll.IW_Budget_GetNColumns(ctypes.byref(location_id),
                                       ctypes.byref(n_columns),
                                       ctypes.byref(status))

        return n_columns.value


    def get_column_headers(self, location_id, length_unit='ft', area_unit='Acres', volume_unit='TAF'):
        # IW_Budget_GetColumnHeaders(iLoc,cColumnHeaders,iLenColumnHeaders,NColumns,LengthUnit,AreaUnit,VolumeUnit,
        #                            iLenUnit,iLocArray,iStat)
        if not hasattr(self.dll, 'IW_Budget_GetColumnHeaders'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Budget_GetColumnHeaders'))
        
        # get number of locations
        n_locations = self.get_n_locations()

        # check that location_id is a number between 1 and n_locations
        if location_id not in [i+1 for i in range(n_locations)]:
            raise ValueError('location_id is not valid. Must be a value between 1 and {}.'.format(n_locations))

        # get the number of columns
        n_columns = ctypes.c_int(self.get_n_columns(location_id))

        # convert location_id to ctypes
        location_id = ctypes.c_int(location_id)
        
        # set length of the column headers array to 30 times 
        length_column_headers = ctypes.c_int(30 * n_columns.value)

        # get max length of the units
        units_length = ctypes.c_int(max(len(length_unit), len(area_unit), len(volume_unit)))

        # convert units to ctypes
        length_unit = ctypes.create_string_buffer(length_unit.encode('utf-8'))
        area_unit = ctypes.create_string_buffer(area_unit.encode('utf-8'))
        volume_unit = ctypes.create_string_buffer(volume_unit.encode('utf-8'))

        # initialize output variables
        raw_column_headers = ctypes.create_string_buffer(length_column_headers.value)
        delimiter_position_array = (ctypes.c_int*n_columns.value)()
        status = ctypes.c_int(-1)

        # IW_Budget_GetColumnHeaders(iLoc,cColumnHeaders,iLenColumnHeaders,NColumns,LengthUnit,AreaUnit,VolumeUnit,
        #                            iLenUnit,iLocArray,iStat)
        self.dll.IW_Budget_GetColumnHeaders(ctypes.byref(location_id),
                                            raw_column_headers,
                                            ctypes.byref(length_column_headers),
                                            ctypes.byref(n_columns),
                                            length_unit,
                                            area_unit,
                                            volume_unit,
                                            ctypes.byref(units_length),
                                            delimiter_position_array,
                                            ctypes.byref(status))

        return IWFM_Budget._string_to_list_by_array(raw_column_headers, delimiter_position_array, n_columns)

    def get_values(self, location_id, columns='all', begin_date=None, 
                   end_date=None, length_conversion_factor=1.0, 
                   area_conversion_factor=2.295684E-05, 
                   volume_conversion_factor=2.295684E-08):
        ''' returns budget data for selected budget columns for a location and specified time interval  
        
        Parameters
        ----------
        location_id : int
            location identiication number for budget e.g. subregion id,
            stream reach id, etc.
            
        columns : str or list of str, default='all'
            column names to obtain budget data

        begin_date : str
            first date where budget data are returned

        end_date : str
            last date where budget data are returned

        length_conversion_factor : float, default=1.0 
            conversion factor to convert simulation units for length
            to another length
        
        area_conversion_factor : float, default=2.295684E-05 (ft^2 -> Acres)
            conversion factor to convert simulation units for area

        volume_conversion_factor : float, default=2.295684E-08 (ft^3 -> TAF)
            conversion factor to convert simulation units for volume

        Returns
        -------
        np.array
            2-D array of floats containing budget data

        Notes
        -----
        At this time, output is always returned using the default output 
        interval. In the future, it could be the output interval or
        more aggregated.
        '''
        if not hasattr(self.dll, 'IW_Budget_GetValues'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Budget_GetValues'))
        
        # get number of locations
        n_locations = self.get_n_locations()

        # check that location_id is a number between 1 and n_locations
        if location_id not in [i+1 for i in range(n_locations)]:
            raise ValueError('location_id is not valid. Must be a value between 1 and {}.'.format(n_locations))

        # convert location_id to ctypes
        location_id = ctypes.c_int(location_id)

        # handle list of columns
        if isinstance(columns, str) and columns == 'all':
            # get number of columns of data, reduce by 1 since get_n_columns includes time
            n_columns = ctypes.c_int(self.get_n_columns(location_id.value) - 1)
            #n_columns = ctypes.c_int(self.get_n_columns(location_id.value))
            columns = (ctypes.c_int*n_columns.value)(*[i+1 for i in range(n_columns.value)])
                   
        elif isinstance(columns, list):
            # get column headers
            column_headers = self.get_column_headers(location_id.value)
            
            # check that all column names provided exist if so create list of column numbers
            column_numbers = []
            for i, val in enumerate(columns):
                if val not in column_headers:
                    raise ValueError('columns provided must be one of the following:\n {}'.format(', '.join(column_headers)))
                else:
                    column_numbers.append(i+1) # i+1 is used for fortran array indexing
            
            # convert column numbers list to ctypes
            n_columns = ctypes.c_int(len(column_numbers))
            columns = (ctypes.c_int*n_columns.value)(*column_numbers)

        else:
            raise TypeError('columns must be a list or "all"')

        # handle start and end dates
        # get time specs
        dates_list, output_interval = self.get_time_specs()
        
        if begin_date is None:
            begin_date = dates_list[0]
        else:
            IWFM_Budget._validate_iwfm_date(begin_date)

            if begin_date not in dates_list:
                raise ValueError('begin_date was not found in the Budget file. use get_time_specs() method to check.')
        
        if end_date is None:
            end_date = dates_list[-1]
        else:
            IWFM_Budget._validate_iwfm_date(end_date)

            if end_date not in dates_list:
                raise ValueError('end_date was not found in the Budget file. use get_time_specs() method to check.')

        if self.is_date_greater(begin_date, end_date):
            raise ValueError('end_date must occur after begin_date')

        # get number of timestep intervals
        n_timestep_intervals = ctypes.c_int(self.get_n_intervals(begin_date, end_date, 
                                                                 output_interval, includes_end_date=True))

        # convert beginning and end dates to ctypes
        begin_date = ctypes.create_string_buffer(begin_date.encode('utf-8'))
        end_date = ctypes.create_string_buffer(end_date.encode('utf-8'))

        length_date = ctypes.c_int(ctypes.sizeof(begin_date))

        # convert output_interval to ctypes
        output_interval = ctypes.create_string_buffer(output_interval.encode('utf-8'))
        length_output_interval = ctypes.c_int(ctypes.sizeof(output_interval))

        # convert unit conversion factors to ctypes
        length_conversion_factor = ctypes.c_double(length_conversion_factor)
        area_conversion_factor = ctypes.c_double(area_conversion_factor)
        volume_conversion_factor = ctypes.c_double(volume_conversion_factor)

        # initialize output variables
        budget_values = ((ctypes.c_double*(n_columns.value + 1))*n_timestep_intervals.value)()
        n_output_intervals = ctypes.c_int(0)
        status = ctypes.c_int(-1)

        # IW_Budget_GetValues(iLoc,nReadCols,iReadCols,cDateAndTimeBegin,cDateAndTimeEnd,iLenDateAndTime,
        #                     cOutputInterval,iLenInterval,rFact_LT,rFact_AR,rFact_VL,nTimes_In,Values,nTimes_Out,iStat)
        self.dll.IW_Budget_GetValues(ctypes.byref(location_id),
                                     ctypes.byref(n_columns),
                                     columns,
                                     begin_date,
                                     end_date,
                                     ctypes.byref(length_date),
                                     output_interval,
                                     ctypes.byref(length_output_interval),
                                     ctypes.byref(length_conversion_factor),
                                     ctypes.byref(area_conversion_factor),
                                     ctypes.byref(volume_conversion_factor),
                                     ctypes.byref(n_timestep_intervals),
                                     budget_values,
                                     ctypes.byref(n_output_intervals),
                                     ctypes.byref(status))

        values = np.array(budget_values)

        dates = np.array('1899-12-30', dtype='datetime64') + values[:,0].astype('timedelta64')
        budget = values[:,1:]

        return dates, budget

    def get_values_for_a_column(self, location_id, column_name, begin_date=None, 
                                end_date=None, length_conversion_factor=1.0, 
                                area_conversion_factor=2.295684E-05, 
                                volume_conversion_factor=2.295684E-08):
        ''' returns the budget data for a single column and location for a specified
        beginning and ending dates.

        Parameters
        ----------
        location_id : int
            location_id where the budget data is returned

        column_name : str
            name of the budget column to return

        begin_date : str or None, default=None
            first date for budget values

        end_date : str or None, default=None
            last date for budget values

        length_conversion_factor : float, default=1.0
            unit conversion factor for length units used in the model 
            to some other length unit

        area_conversion_factor : float, default=2.295684E-05
            unit conversion factor for area units used in the model
            to some other area unit

        volume_conversion_factor : float, default=2.295684E-08
            unit conversion factor for volume units used in the model
            to some other volume unit

        Returns
        -------
        length 2-tuple of np.arrays
            representing dates and values
        '''
        if not hasattr(self.dll, 'IW_Budget_GetValues_ForAColumn'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_Budget_GetValues_ForAColumn'))
        
        # get number of locations
        n_locations = self.get_n_locations()

        # check that location_id is a number between 1 and n_locations
        if location_id not in [i+1 for i in range(n_locations)]:
            raise ValueError('location_id is not valid. Must be a value between 1 and {}.'.format(n_locations))

        # convert location_id to ctypes
        location_id = ctypes.c_int(location_id)

        # get column_headers
        column_headers = self.get_column_headers(location_id.value)

        # check that column name provided exists. if so, get column index.
        try:
            column_id = ctypes.c_int(column_headers.index(column_name) + 1)
        except ValueError:
            add_message = 'Must be one of the following:\n{}'.format(', '.join(column_headers))
            raise ValueError(add_message)
            
        # handle start and end dates
        # get time specs
        dates_list, output_interval = self.get_time_specs()
        
        if begin_date is None:
            begin_date = dates_list[0]
        else:
            IWFM_Budget._validate_iwfm_date(begin_date)

            if begin_date not in dates_list:
                raise ValueError('begin_date was not found in the Budget file. use get_time_specs() method to check.')
        
        if end_date is None:
            end_date = dates_list[-1]
        else:
            IWFM_Budget._validate_iwfm_date(end_date)

            if end_date not in dates_list:
                raise ValueError('end_date was not found in the Budget file. use get_time_specs() method to check.')

        if self.is_date_greater(begin_date, end_date):
            raise ValueError('end_date must occur after begin_date')

        # get number of timestep intervals
        n_timestep_intervals = ctypes.c_int(self.get_n_intervals(begin_date, end_date, 
                                                                 output_interval, includes_end_date=True))

        # convert beginning and end dates to ctypes
        begin_date = ctypes.create_string_buffer(begin_date.encode('utf-8'))
        end_date = ctypes.create_string_buffer(end_date.encode('utf-8'))

        length_date = ctypes.c_int(ctypes.sizeof(begin_date))

        # convert output_interval to ctypes
        output_interval = ctypes.create_string_buffer(output_interval.encode('utf-8'))
        length_output_interval = ctypes.c_int(ctypes.sizeof(output_interval))

        # convert unit conversion factors to ctypes
        length_conversion_factor = ctypes.c_double(length_conversion_factor)
        area_conversion_factor = ctypes.c_double(area_conversion_factor)
        volume_conversion_factor = ctypes.c_double(volume_conversion_factor)

        # initialize output variables
        n_output_intervals = ctypes.c_int(0)
        dates = (ctypes.c_double*n_timestep_intervals.value)()
        values = (ctypes.c_double*n_timestep_intervals.value)()
        status = ctypes.c_int(-1)

        # IW_Budget_GetValues_ForAColumn(iLoc,iCol,cOutputInterval,iLenInterval,cOutputBeginDateAndTime,cOutputEndDateAndTime,
        #                                iLenDateAndTime,rFact_LT,rFact_AR,rFact_VL,iDim_In,iDim_Out,Dates,Values,iStat)
        self.dll.IW_Budget_GetValues_ForAColumn(ctypes.byref(location_id),
                                                ctypes.byref(column_id),
                                                output_interval,
                                                ctypes.byref(length_output_interval),
                                                begin_date,
                                                end_date,
                                                ctypes.byref(length_date),
                                                ctypes.byref(length_conversion_factor),
                                                ctypes.byref(area_conversion_factor),
                                                ctypes.byref(volume_conversion_factor),
                                                ctypes.byref(n_timestep_intervals),
                                                ctypes.byref(n_output_intervals),
                                                dates,
                                                values,
                                                ctypes.byref(status))

        dates = np.array('1899-12-30', dtype='datetime64') + np.array(dates, dtype='timedelta64')
        values = np.array(values)

        return dates, values

    ### helper methods
    def is_date_greater(self, first_date, comparison_date):
        ''' returns True if first_date is greater than comparison_date

        Parameters
        ----------
        first_date : str
            IWFM format date MM/DD/YYYY_HH:MM

        comparison_date : str
            IWFM format date MM/DD/YYYY_HH:MM

        Returns
        -------
        boolean
            True if first_date is greater (in the future) when compared to the comparison_date
            False if first_date is less (in the past) when compared to the comparison_date 
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_IsTimeGreaterThan"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_IsTimeGreaterThan'))

        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)
           
        # convert begin and end dates to ctypes character arrays 
        first_date = ctypes.create_string_buffer(first_date.encode('utf-8'))
        comparison_date = ctypes.create_string_buffer(comparison_date.encode('utf-8'))

        # set length of IWFM date
        length_dates = ctypes.c_int(ctypes.sizeof(first_date))

        # initialize output variables
        compare_result = ctypes.c_int(0)
            
        self.dll.IW_IsTimeGreaterThan(ctypes.byref(length_dates),
                                      first_date,
                                      comparison_date,
                                      ctypes.byref(compare_result),
                                      ctypes.byref(self.status))

        if compare_result.value == -1:
            is_greater = False 
        elif compare_result.value == 1:
            is_greater = True

        return is_greater

    def get_n_intervals(self, begin_date, end_date, time_interval, includes_end_date=True):
        ''' returns the number of time intervals between a provided start date and end date

        Parameters
        ----------
        begin_date : str
            IWFM format date MM/DD/YYYY_HH:MM
        
        end_date : str
            IWFM format date MM/DD/YYYY_HH:MM

        time_interval : str
            valid IWFM time interval

        includes_end_date : boolean, default=True
            True adds 1 to the number of intervals to include the 
            end_date
            False is the number of intervals between the two dates 
            without including the end_date

        Returns
        -------
        int
            number of time intervals between begin and end date
        '''
        # check to see if IWFM procedure is available in user version of IWFM DLL
        if not hasattr(self.dll, "IW_GetNIntervals"):
            raise AttributeError('IWFM DLL does not have "{}" procedure. Check for an updated version'.format('IW_GetNIntervals'))
        
        # check that begin_date is valid
        IWFM_Model._validate_iwfm_date(begin_date)
        
        # check that end_date is valid
        IWFM_Model._validate_iwfm_date(end_date)
        
        # check that time_interval is a valid IWFM time_interval
        IWFM_Model._validate_time_interval(time_interval)
        
        # check that begin_date is not greater than end_date
        if self.is_date_greater(begin_date, end_date):
            raise ValueError("begin_date must occur before end_date")
        
        # reset instance variable status to -1
        self.status = ctypes.c_int(-1)

        # convert IWFM dates to ctypes character arrays
        begin_date = ctypes.create_string_buffer(begin_date.encode('utf-8'))
        end_date = ctypes.create_string_buffer(end_date.encode('utf-8'))
        time_interval = ctypes.create_string_buffer(time_interval.encode('utf-8'))

        # set length of IWFM datetime string
        length_iwfm_date = ctypes.c_int(ctypes.sizeof(begin_date))

        # set length of IWFM time_interval string
        length_time_interval = ctypes.c_int(ctypes.sizeof(time_interval))

        # initialize output variables
        n_intervals = ctypes.c_int(0)

        self.dll.IW_GetNIntervals(begin_date,
                                  end_date,
                                  ctypes.byref(length_iwfm_date),
                                  time_interval,
                                  ctypes.byref(length_time_interval),
                                  ctypes.byref(n_intervals),
                                  ctypes.byref(self.status))
            
        if includes_end_date:
            return n_intervals.value + 1

        return n_intervals.value

    @staticmethod
    def _validate_iwfm_date(dt):
        ''' performs validation that a provided value is an IWFM-format date string based on
        string length and format MM/DD/YYYY_HH:MM

        Parameters
        ----------
        dt : str
            input value to check if IWFM-format date

        Returns
        -------
        None
            raises errors if validation checks do not pass
        '''
        if not isinstance(dt, str):
            raise TypeError('IWFM dates must be a string')
                    
        if len(dt) != 16:
            raise ValueError("IWFM dates must be 16 characters in length and of format MM/DD/YYYY_HH:MM")
                
        if '_' not in dt or dt.index('_') != 10:
            raise ValueError("IWFM dates must have an '_' separating the date and time")
                
        if ':' not in dt or dt.index(':') != 13:
            raise ValueError("IWFM dates must have an ':' separating the hours from minutes")
                
        if dt[2] != '/' or dt[5] != '/':
            raise ValueError("IWFM dates must use '/' as separators for the month, day, year in the date")
                
        try:
            datetime.datetime.strptime(dt, '%m/%d/%Y_%H:%M')
        except ValueError:
            try:
                datetime.datetime.strptime(dt.split('_')[0], '%m/%d/%Y')
            except ValueError:
                raise ValueError("Value provided: {} could not be converted to a date".format(dt))
            else:
                try:
                    hour = int(dt[11:13])
                    minute = int(dt[14:])
                except:
                    raise ValueError("hour or minute values are not numbers")
                else:
                    if hour < 0 or hour > 24:
                        raise ValueError("hour value is not between 00 and 24")
                            
                    if minute < 0 or minute > 59:
                        raise ValueError("minute value is not between 00 and 59")
                        
                    if hour == 24 and minute > 0:
                        raise ValueError("days cannot exceed 24:00 hours")

    @staticmethod
    def _string_to_list_by_array(in_string, starting_position_array, length_output_list):
        ''' converts a string to a list of strings based on an
        array of the starting character position (index).

        Parameters
        ----------
        in_string : str or ctypes.Array (character array)
            input string that is converted to list of strings

        starting_position_array : np.array, list of ints, ctypes.Array
            array of starting character index for each value in list.

        length_output_list : int, ctypes.c_int, ctypes.c_long
            number of non-placeholder values in starting_position_array

        Returns
        -------
        list of strings
            input string (in_string) sliced into pieces based on array 
            of starting positions (starting_position_array)

        Notes
        -----
        length of starting_position_array will be the length of the output list
        '''
        # check that type of starting_position_array is a np.ndarray, list, tuple, or ctypes.Array
        if not isinstance(starting_position_array, (np.ndarray, list, tuple, ctypes.Array)):
            raise TypeError("starting_position_array must be a np.ndarray, list, tuple, ctypes.Array")

        # handle case where starting_position_array is a list, tuple, or ctypes.Array
        if isinstance(starting_position_array, (list, tuple, ctypes.Array)):
            
            # convert to a numpy array
            starting_position_array = np.array(starting_position_array)
            
        # check that all values are integers
        if starting_position_array.dtype not in (np.int, np.int32, np.dtype('<i4')):
            raise TypeError("All values in starting_position_array must be type: int.")

        # check that length_output_list is an integer
        if not isinstance(length_output_list, (int, ctypes.c_long, ctypes.c_int)):
            raise TypeError("length_output_list must be an int, ctypes.c_int, or ctypes.c_long.")

        # convert length_output_list to python integer
        if isinstance(length_output_list, (ctypes.c_long, ctypes.c_int)):
            length_output_list = length_output_list.value

        # check that in_string is a string
        if not isinstance(in_string, (str, ctypes.Array)):
            raise TypeError("in_string must be type string or ctypes.Array.\n" +
                            "Type given was {}".format(type(in_string)))

        # convert in_string to a python string if in_string is a ctypes character array
        if isinstance(in_string, ctypes.Array):
            in_string = in_string.value.decode('utf-8')

        # initialize empty list for values
        string_list = []
        
        # trim starting_position_array to length_output_list
        if length_output_list > 0:
            starting_position_array = starting_position_array[:length_output_list]

            # check if first value in array is 1
            if starting_position_array[0] == 1:
                # first python arrays are 0-indexed and the resulting delimiter_position_array
                # is 1-indexed (fortran-standard)
                position_array = starting_position_array - 1

            else:
                position_array = starting_position_array
            
            for i in range(len(position_array)):
                if position_array[i] != position_array[-1]:
                    string_list.append(in_string[position_array[i]:position_array[i+1]])
                else:
                    string_list.append(in_string[position_array[i]:])

        return string_list