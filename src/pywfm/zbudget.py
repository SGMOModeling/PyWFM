import ctypes
from typing import Type
import numpy as np
import pandas as pd

from pywfm.misc import IWFMMiscellaneous

class IWFMZBudget(IWFMMiscellaneous):
    ''' IWFM ZBudget Class for interacting with the IWFM DLL

    Parameters
    ----------
    dll_path : str
        file path and name of the IWFM DLL to access IWFM procedures

    zbudget_file_name : str
        file path and name of the budget file

    Returns
    -------
    IWFMZBudget Object
        instance of the IWFMZBudget class and access to the IWFM Budget 
        fortran procedures.
    '''
    def __init__(self, dll_path, zbudget_file_name):
        if not isinstance(dll_path, str):
            raise TypeError('dll path provided: {} is not a string'.format(dll_path))
        
        self.dll_path = dll_path
        self.zbudget_file_name = zbudget_file_name

        self.dll = ctypes.windll.LoadLibrary(self.dll_path)

        # check to see if the open file procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_OpenFile'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_OpenFile'))

        # set input variables name and name length
        zbudget_file = ctypes.create_string_buffer(self.zbudget_file_name.encode('utf-8'))
        length_file_name = ctypes.c_int(ctypes.sizeof(zbudget_file))
        
        # initialize output variable status
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_OpenFile(zbudget_file,
                                    ctypes.byref(length_file_name),
                                    ctypes.byref(status))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_budget_file()

    def close_zbudget_file(self):
        ''' closes an open budget file for an IWFM model application '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_CloseFile'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_CloseFile'))
        
        # initialize output variable status
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_CloseFile(ctypes.byref(status))

    def generate_zone_list_from_file(self, zone_definition_file):
        ''' generates a list of zones and their neighboring zones based
        on data provided in a text file. This file must be in the same 
        format as the Zone Definition File used by the Z-Budget post-
        processor. 
        Parameters
        ----------
        zone_definition_file : str
            file name for the zone definition file used to generate the list of zones
            
        Returns
        -------
        None
            generates the list of zones and adjacent zones
        '''
        # check to see if the open file procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_GenerateZoneList_FromFile'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_GenerateZoneList_FromFile'))

        # set input variables name and name length
        zone_file = ctypes.create_string_buffer(zone_definition_file.encode('utf-8'))
        length_file_name = ctypes.c_int(ctypes.sizeof(zone_file))
        
        # initialize output variable status
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GenerateZoneList_FromFile(zone_file,
                                                      ctypes.byref(length_file_name),
                                                      ctypes.byref(status))

    def _generate_zone_list(self, zone_extent_id, elements, layers, zones, zone_names):
        ''' private method that generates a list of zones and their neighboring zones based
        on data provided directly by the client software
        
        Parameters
        ----------
        zone_extent_id : int
            valid IWFM zone extent identification number. Options can
            be obtained using the get_zone_extent_ids method

        elements : list, np.ndarray
            list of element identification numbers used to identify 
            zone definitions

        layers : list, np.ndarray
            list of layer numbers used to identify zone definitions. 
            if using the zone extent id for horizontal, this is not used

        zones : list, np.ndarray
            list of identification numbers used to identify which zone
            each element and layer are specified in.

        zone_names : list
            list of zone names. there can be fewer names than zones defined.

        Returns
        -------
        None
            generates the zone definitions
        '''
        # check to see if the open file procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_GenerateZoneList'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_GenerateZoneList'))

        # convert zone_extent_id to ctypes
        zone_extent_id = ctypes.c_int(zone_extent_id)

        # check that inputs are array-like
        if not isinstance(elements, (np.ndarray, list)):
            raise TypeError('elements must be an array or list')

        if not isinstance(layers, (np.ndarray, list)):
            raise TypeError('layers must be an array or list')

        if not isinstance(zones, (np.ndarray, list)):
            raise TypeError('zones must be an array or list')


        # check elements, layers, zones arrays are 1-D and same length
        if isinstance(elements, list):
            elements = np.array(elements)

        if isinstance(layers, list):
            layers = np.array(layers)

        if isinstance(zones, list):
            zones = np.array(zones)

        if (elements.shape == layers.shape) & (elements.shape == zones.shape) & (len(elements.shape) == 1):
            n_elements = ctypes.c_int(elements.shape[0])
            elements = (ctypes.c_int*n_elements.value)(*elements)
            layers = (ctypes.c_int*n_elements.value)(*layers)
            zones = (ctypes.c_int*n_elements.value)(*zones)

        else:
            raise ValueError('elements, layers, and zones are 1-D '
                             'arrays and must be the same length.')
                            
        # convert list of zone names to string with array of delimiter locations
        n_zones_with_names = ctypes.c_int(len(zone_names))

        zones_with_names = (ctypes.c_int*n_zones_with_names.value)(*[val+1 for val in range(n_zones_with_names.value)])

        # initialize zone_names_string, delimiter_position_array, and length_zone_names
        zone_names_string = ''
        delimiter_position_array = []
        length_zone_names = 0

        for name in zone_names:
            # added 1 since fortran arrays are 1-based
            delimiter_position_array.append(length_zone_names + 1)
            for c in name:
                length_zone_names += 1
            zone_names_string += name

        # convert zone_names_string, delimiter_position_array, and 
        # length_zone_names to ctypes
        zone_names_string = ctypes.create_string_buffer(zone_names_string.encode('utf-8'))
        delimiter_position_array = (ctypes.c_int*n_zones_with_names.value)(*delimiter_position_array)
        length_zone_names = ctypes.c_int(length_zone_names)

        # initialize output variables
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GenerateZoneList(ctypes.byref(zone_extent_id),
                                             ctypes.byref(n_elements),
                                             elements,
                                             layers,
                                             zones,
                                             ctypes.byref(n_zones_with_names),
                                             zones_with_names,
                                             ctypes.byref(length_zone_names),
                                             zone_names_string,
                                             delimiter_position_array,
                                             ctypes.byref(status))

    def get_n_zones(self):
        ''' returns the number of zones specified in the zbudget

        Returns
        -------
        int
            number of zones
        '''
        # check to see if the open file procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_GetNZones'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_GetNZones'))

        # initialize output variables
        n_zones = ctypes.c_int(0)

        # initialize output variable status
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetNZones(ctypes.byref(n_zones),
                                      ctypes.byref(status))

        return n_zones.value

    def get_zone_list(self):
        ''' returns the list of zone numbers

        Returns
        -------
        np.ndarray
            array of zone numbers   
        '''
        # check to see if the open file procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_GetZoneList'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_GetZoneList'))

        # get number of zones
        n_zones = ctypes.c_int(self.get_n_zones())

        # initialize output variables
        zone_list = (ctypes.c_int*n_zones.value)()

        # initialize output variable status
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetZoneList(ctypes.byref(n_zones),
                                        zone_list,
                                        ctypes.byref(status))

        return np.array(zone_list)

    def get_n_time_steps(self):
        ''' returns the number of time steps where zbudget data is 
        available

        Returns
        -------
        int
            number of time steps
        '''
        # check to see if the open file procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_GetNTimeSteps'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_GetNTimeSteps'))

        # initialize output variables
        n_time_steps = ctypes.c_int(0)

        # initialize output variable status
        status = ctypes.c_int(0)
        
        self.dll.IW_ZBudget_GetNTimeSteps(ctypes.byref(n_time_steps),
                                          ctypes.byref(status))

        return n_time_steps.value
    
    def get_time_specs(self):
        ''' returns a list of all the time stamps and the time interval for the zbudget 
        
        Returns
        -------
        length-2 tuple
            time stamps (list), time interval (string)
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_GetTimeSpecs'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_GetTimeSpecs'))

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
        status = ctypes.c_int(0)

        # IW_ZBudget_GetTimeSpecs(cDataDatesAndTimes,iLenDates,cInterval,iLenInterval,NData,iLocArray,iStat)
        self.dll.IW_ZBudget_GetTimeSpecs(raw_dates_string,
                                         ctypes.byref(length_date_string),
                                         time_interval,
                                         ctypes.byref(length_time_interval),
                                         ctypes.byref(n_time_steps),
                                         delimiter_position_array,
                                         ctypes.byref(status))

        dates_list = self._string_to_list_by_array(raw_dates_string, delimiter_position_array, n_time_steps)

        interval = time_interval.value.decode('utf-8')

        return dates_list, interval

    def _get_column_headers_general(self, area_unit='SQ FT', volume_unit='CU FT'):
        ''' private method returning the Z-Budget column headers (i.e. 
        titles). For flow processes that simulate flow exchange between 
        neighboring zones (e.g. groundwater process) the inflow and 
        outflow columns are lumped into two columns (e.g. “Inflows from 
        Adjacent Zones” and “Outflows to Adjacent Zones”) instead of 
        identifying inflows from and outflows to individual neighboring 
        zones. These column headers apply to any zone regardless of the 
        number of neighboring zones.

        Parameters
        ----------
        area_unit : str, default='SQ FT'
            unit of area appearing in the Zbudget column headers

        volume_unit : str, default='CU FT'
            unit of volume appearing in the ZBudget column headers

        Returns
        -------
        list
            list of column headers
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_GetColumnHeaders_General'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_GetColumnHeaders_General'))

        # set the maximum number of columns
        max_n_column_headers = ctypes.c_int(200)

        # get string length for area_unit and volume_unit
        unit_length = ctypes.c_int(max(len(area_unit), len(volume_unit)))

        # set total length of column headers
        length_column_headers = ctypes.c_int(max_n_column_headers.value*30)

        # convert area_unit and volume_unit to ctypes
        area_unit = ctypes.create_string_buffer(area_unit.encode('utf-8'))
        volume_unit = ctypes.create_string_buffer(volume_unit.encode('utf-8'))

        # initialize output variables
        raw_column_header_string = ctypes.create_string_buffer(length_column_headers.value)
        n_columns = ctypes.c_int(0)
        delimiter_position_array = (ctypes.c_int*max_n_column_headers.value)()
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetColumnHeaders_General(ctypes.byref(max_n_column_headers),
                                                     area_unit,
                                                     volume_unit,
                                                     ctypes.byref(unit_length),
                                                     ctypes.byref(length_column_headers),
                                                     raw_column_header_string,
                                                     ctypes.byref(n_columns),
                                                     delimiter_position_array,
                                                     ctypes.byref(status))

        return self._string_to_list_by_array(raw_column_header_string, 
                                             delimiter_position_array, 
                                             n_columns)

    def get_column_headers_for_a_zone(self, zone_id, area_unit='SQ FT', 
                                      volume_unit='CU FT', column_list='all',
                                      include_time=True):
        ''' This procedure retrieves the Z-Budget column headers (i.e. 
        titles) for a specified zone for selected data columns. For flow 
        processes that simulate flow exchange between neighboring zones 
        (e.g. groundwater process), the column headers for inflows from 
        and outflows to neighboring zones are listed separately for each 
        neighboring zone. These columns are referred to as “diversified 
        columns” since the inflows from and outflows to each neighboring 
        zone are treated as separate columns

        Parameters
        ----------
        zone_id : int
            zone identification number used to return the column headers

        column_list : int, list, np.ndarray, or 'all', default='all'
            list of header column indices. this is based on the results 
            from the get_column_headers_general method

        area_unit : str, default='SQ FT'
            unit of area appearing in the Zbudget column headers

        volume_unit : str, default='CU FT'
            unit of volume appearing in the ZBudget column headers

        include_time : boolean, default=True
            flag to determine if columns headers include the time column

        Returns
        -------
        tuple (length=2)
            index 0 - list of column headers
            index 1 - np.ndarray of column indices 
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_GetColumnHeaders_ForAZone'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_GetColumnHeaders_ForAZone'))

        # convert zone_id to ctypes
        zone_id = ctypes.c_int(zone_id)

        # get general column headers
        general_columns = self._get_column_headers_general(area_unit, volume_unit)

        # get number of general columns
        n_general_columns = len(general_columns)

        # get column indices for general_columns
        general_column_indices = np.arange(1, n_general_columns + 1)

        # validate column_list
        if column_list == 'all':
            column_list = general_column_indices
        
        elif isinstance(column_list, (int, np.ndarray, list)):
            if isinstance(column_list, list):
                column_list = np.array(column_list)
            
            elif isinstance(column_list, int):
                column_list = np.array([column_list])

            # check values in column list are in general_column_indices
            if not np.all(np.isin(column_list, general_column_indices)):
                raise ValueError('provided indices in column_list are invalid')

        else:
            raise TypeError("column_list must be an int, list, np.ndarray, or 'all'")

        # convert column_list to ctypes
        if include_time:
            n_column_list = ctypes.c_int(len(column_list))
            column_list = (ctypes.c_int*n_column_list.value)(*column_list)
        else:
            n_column_list = ctypes.c_int(len(column_list) - 1)
            column_list = (ctypes.c_int*n_column_list.value)(*column_list[column_list != 1])
        
        # set the maximum number of columns
        max_n_column_headers = ctypes.c_int(200)

        # get string length for area_unit and volume_unit
        unit_length = ctypes.c_int(max(len(area_unit), len(volume_unit)))

        # set total length of column headers
        length_column_headers = ctypes.c_int(max_n_column_headers.value*30)

        # convert area_unit and volume_unit to ctypes
        area_unit = ctypes.create_string_buffer(area_unit.encode('utf-8'))
        volume_unit = ctypes.create_string_buffer(volume_unit.encode('utf-8'))

        # initialize output variables
        raw_column_header_string = ctypes.create_string_buffer(length_column_headers.value)
        n_columns = ctypes.c_int(0)
        delimiter_position_array = (ctypes.c_int*max_n_column_headers.value)()
        diversified_columns_list= (ctypes.c_int*max_n_column_headers.value)()
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetColumnHeaders_ForAZone(ctypes.byref(zone_id),
                                                      ctypes.byref(n_column_list),
                                                      column_list,
                                                      ctypes.byref(max_n_column_headers),
                                                      area_unit,
                                                      volume_unit,
                                                      ctypes.byref(unit_length),
                                                      ctypes.byref(length_column_headers),
                                                      raw_column_header_string,
                                                      ctypes.byref(n_columns),
                                                      delimiter_position_array,
                                                      diversified_columns_list,
                                                      ctypes.byref(status))

        column_headers =  self._string_to_list_by_array(raw_column_header_string, 
                                                        delimiter_position_array, 
                                                        n_columns)

        return column_headers, np.array(diversified_columns_list)

    def get_zone_names(self):
        ''' returns the zone names specified by the user in the zone
        definitions
        
        Returns
        -------
        list
            list of names for each zone defined
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_GetZoneNames'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_GetZoneNames'))

        # get number of zones
        n_zones = ctypes.c_int(self.get_n_zones())

        # set size of string used to retrieve the names
        length_zone_names_string = ctypes.c_int(n_zones.value*30)

        # initialize output variables
        raw_zone_names = ctypes.create_string_buffer(length_zone_names_string.value)
        delimiter_location_array = (ctypes.c_int*n_zones.value)()
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetZoneNames(ctypes.byref(n_zones),
                                         ctypes.byref(length_zone_names_string),
                                         raw_zone_names,
                                         delimiter_location_array,
                                         ctypes.byref(status))

        return self._string_to_list_by_array(raw_zone_names, 
                                             delimiter_location_array, 
                                             n_zones)

    def get_n_title_lines(self):
        ''' returns the number of title lines in a Zbudget 
        
        Returns
        -------
        int
            number of title lines
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_GetNTitleLines'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_GetNTitleLines'))

        # initialize output variables
        n_title_lines = ctypes.c_int(0)
        status = ctypes.c_int(0)

        # IW_Budget_GetNTitleLines(NTitles,iStat)
        self.dll.IW_ZBudget_GetNTitleLines(ctypes.byref(n_title_lines),
                                          ctypes.byref(status))

        return n_title_lines.value

    def get_title_lines(self, zone_id, area_conversion_factor, area_unit,
                        volume_unit):
        ''' returns the title lines for the Z-Budget data for a zone to
        be displayed in the files (text, spreadsheet, etc.) where the 
        Z-Budget data is being imported into. 
        
        Parameters
        ----------
        zone_id : int
            zone identification number used to retrieve the title lines
            
        area_conversion_factor : int, float
            factor used to convert area units between the default model
            unit and the desired output unit 
            e.g. ft^2 --> Acre = 2.29568E-05 
            
        area_unit : str
            desired output unit for area
                      
        volume_unit : str
            desired output unit for volume
            
        Returns
        -------
        list
            title lines for zone
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_GetTitleLines'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_GetTitleLines'))

        # get number of title lines
        n_title_lines = ctypes.c_int(self.get_n_title_lines())

        # convert zone_id to ctypes
        zone_id = ctypes.c_int(zone_id)

        # convert area conversion factor and units to ctypes
        area_conversion_factor = ctypes.c_double(area_conversion_factor)
        area_unit = ctypes.create_string_buffer(area_unit.encode('utf-8'))

        # convert volume units to ctypes
        volume_unit = ctypes.create_string_buffer(volume_unit.encode('utf-8'))

        # get character length of units
        length_unit_string = ctypes.c_int(max(ctypes.sizeof(area_unit), 
                                              ctypes.sizeof(volume_unit)))

        # set length of title string
        length_title_string = ctypes.c_int(n_title_lines.value*200)

        # initialize output variables
        raw_title_string = ctypes.create_string_buffer(length_title_string.value)
        delimiter_position_array = (ctypes.c_int*n_title_lines.value)()
        status = ctypes.c_int(0)
        
        self.dll.IW_ZBudget_GetTitleLines(ctypes.byref(n_title_lines),
                                          ctypes.byref(zone_id),
                                          ctypes.byref(area_conversion_factor),
                                          area_unit,
                                          volume_unit,
                                          ctypes.byref(length_unit_string),
                                          raw_title_string,
                                          ctypes.byref(length_title_string),
                                          delimiter_position_array,
                                          ctypes.byref(status))

        return self._string_to_list_by_array(raw_title_string, 
                                             delimiter_position_array, 
                                             n_title_lines)

    def get_values_for_some_zones_for_an_interval(self, zone_ids='all', 
                                                  column_ids='all', 
                                                  current_date=None, 
                                                  output_interval=None, 
                                                  area_conversion_factor=1.0, 
                                                  volume_conversion_factor=1.0):
        ''' returns specified zone flow values for a specified list of 
        zones for a given time interval.

        Parameters
        ----------
        zone_ids : list, np.ndarray, int
            one or more zone identification numbers to retrieve zbudget
            data

        column_ids : int, list, or 'all', default='all'
            one or more data column indices to retrieve zbudget data

        current_date : str
            valid IWFM date used to return zbudget data

        output_interval : str
            valid IWFM output time interval for returning zbudget data.
            This must be greater than or equal to the simulation time 
            step

        area_conversion_factor : float or int, default=1.0
            factor to convert area units from the default model units
            to the desired output units

        volume_conversion_factor : float or int, default=1.0
            factor to convert volume units from the default model units
            to the desired output units

        Returns
        -------
        np.ndarray
            array of ZBudget output for user-specified columns and specified zones

        Note
        ----
        Return value includes Time as the first column whether the user provided it or not
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_GetValues_ForSomeZones_ForAnInterval'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_GetValues_ForSomeZones_ForAnInterval'))

        # check that zone is valid
        zones = self.get_zone_list()

        if zone_ids == 'all':
            zone_ids = zones

        elif isinstance(zone_ids, (int, list, np.ndarray)):
            if isinstance(zone_ids, list):
                zone_ids = np.array(zone_ids)
            
            elif isinstance(zone_ids, int):
                zone_ids = np.array([zone_ids])
        
        else:
            raise TypeError('zone_ids must be an int, list or np.ndarray')

        if not np.all(np.isin(zone_ids, zones)):
            raise ValueError('zone_ids were not found in zone definitions provided')

        # convert zone_ids to ctypes
        n_zones = ctypes.c_int(len(zone_ids))
        zone_ids = (ctypes.c_int*n_zones.value)(*zone_ids)

        # get all possible column ids for each zone and place in zone_header_array
        zone_header_array = []
        n_columns_max = 0
        for zone_id in zone_ids:
            _, column_header_ids = self.get_column_headers_for_a_zone(zone_id, include_time=True)
            n_columns = len(column_header_ids[column_header_ids > 0])
            
            if n_columns > n_columns_max:
                n_columns_max = n_columns
            
            zone_header_array.append(column_header_ids)

        zone_header_array = np.array(zone_header_array)[:,:n_columns_max]

        # handle different options for providing column_ids
        if column_ids == 'all':
            max_n_columns = ctypes.c_int(n_columns_max)
            column_ids= zone_header_array

        elif isinstance(column_ids, (int, list)):
            
            if isinstance(column_ids, int):
                # add the 'Time' column if user did not include it
                if column_ids != 1:
                    column_ids = np.array([1, column_ids])
                else:
                    column_ids = np.array([column_ids])

            elif isinstance(column_ids, list):
                
                # first sort each row
                if all([isinstance(val, int) for val in column_ids]):
                    if len(column_ids) > 1:
                        column_ids = sorted(column_ids)

                    # add the 'Time' column if user did not include it
                    if 1 not in column_ids:
                        column_ids = [1] + column_ids

                    max_row_length = len(column_ids)

                elif all([isinstance(val, list) for val in column_ids]):
                    # first sort each row
                    column_ids = [sorted(val) for val in column_ids]

                    # if column id 1 i.e. Time is not included add it as the first column
                    column_ids = [[1] + val if 1 not in val else val for val in column_ids]
                
                    # get the number of columns in each zone
                    max_row_list = [len(val) for val in column_ids]

                    # get the maximum number of columns in any of the zones
                    max_row_length = max(max_row_list)

                    # if list does not have same number of elements in each 
                    # row, then need to pad the end with zeros before 
                    # converting to a numpy array
                    if len(max_row_list) > 1:
                        for i, row in enumerate(column_ids):
                            len_row = len(row)
                            while len_row < max_row_length:
                                row.append(0)
                                len_row = len(row)
                
                column_ids = np.array(column_ids)

            # valid user inputs have been converted to a np.ndarray so validation is performed using numpy
            # check: number of rows in column_ids must match number of zones
            if (column_ids.ndim == 2) and (column_ids.shape[0] != n_zones.value):
                raise ValueError('Each number of rows in column_ids '
                                 'must match number of zones\nThe number '
                                 'of zones provided is {}.\nThe number '
                                 'of zones implied by column_ids is {}'.format(n_zones.value, column_ids.shape[0]))

            elif (column_ids.ndim == 1) and (n_zones.value != 1):
                raise ValueError('Each number of rows in column_ids '
                                 'must match number of zones\nThe number '
                                 'of zones provided is {}.\nThe number '
                                 'of zones implied by column_ids is {}'.format(n_zones.value, column_ids.ndim))
            
            if column_ids.ndim == 1:
                if not np.all(np.isin(column_ids, zone_header_array[zone_header_array > 0])):
                    raise ValueError('column_ids for zone {} are invalid'.format(np.array(zone_ids)))

                max_n_columns = ctypes.c_int(column_ids.shape[0])

            else:
                # check row by row if the column_ids are valid for a particular zone
                # this will only catch the first error it finds
                for i, row in enumerate(column_ids):
                    if not np.all(np.isin(row, zone_header_array[i][zone_header_array[i] > 0])):
                        raise ValueError('column_ids for zone {} are invalid'.format(np.array(zone_ids)[i]))

                max_n_columns = ctypes.c_int(column_ids.shape[-1])

        else:
            raise TypeError("column_ids must be 'all', an integer or list")
        
        # populate ctypes array containing column ids for each zone
        if n_zones.value == 1:
            column_id_array = (ctypes.c_int*max_n_columns.value)(*column_ids)
        else:
            column_id_array = ((ctypes.c_int*max_n_columns.value)*n_zones.value)()
            for i, row in enumerate(column_ids):
                column_id_array[i][:] = row

        
        # handle current date
        # get time specs
        dates_list, sim_output_interval = self.get_time_specs()
        
        if current_date is None:
            current_date = dates_list[0]
        else:
            self._validate_iwfm_date(current_date)

            if current_date not in dates_list:
                raise ValueError('current_date was not found in the ZBudget '
                                 'file. use get_time_specs() method to check.')

        # convert current_date to ctypes
        current_date = ctypes.create_string_buffer(current_date.encode('utf-8'))
        length_date_string = ctypes.c_int(ctypes.sizeof(current_date))

        # handle output interval
        if output_interval is None:
            output_interval = sim_output_interval
                
        # check output interval is greater than or equal to simulation
        if not self._is_time_interval_greater_or_equal(output_interval, sim_output_interval):
            raise ValueError('output_interval must be greater than or '
                             'equal to the simulation time step')
        
        # convert output_interval to ctypes
        output_interval = ctypes.create_string_buffer(output_interval.encode('utf-8'))
        length_output_interval = ctypes.c_int(ctypes.sizeof(output_interval))

        # convert unit conversion factors to ctypes
        area_conversion_factor = ctypes.c_double(area_conversion_factor)
        volume_conversion_factor = ctypes.c_double(volume_conversion_factor)

        # initialize output variables
        zbudget_values = ((ctypes.c_double*max_n_columns.value)*n_zones.value)()
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetValues_ForSomeZones_ForAnInterval(ctypes.byref(n_zones),
                                                                 zone_ids,
                                                                 ctypes.byref(max_n_columns),
                                                                 column_id_array,
                                                                 current_date,
                                                                 ctypes.byref(length_date_string),
                                                                 output_interval,
                                                                 ctypes.byref(length_output_interval),
                                                                 ctypes.byref(area_conversion_factor),
                                                                 ctypes.byref(volume_conversion_factor),
                                                                 zbudget_values,
                                                                 ctypes.byref(status))

        values = np.array(zbudget_values)

        #dates = np.array('1899-12-30', dtype='datetime64') + values[:,0].astype('timedelta64')
        #zbudget = values[:,1:]
        
        #return dates, zbudget
        return values

    def get_values_for_a_zone(self, zone_id, column_ids='all', begin_date=None, 
                              end_date=None, output_interval=None, 
                              area_conversion_factor=1.0, 
                              volume_conversion_factor=1.0):
        ''' returns specified Z-Budget data columns for a specified zone for a time period.

        Parameters
        ----------
        zone_id : int
            zone identification number used to return zbudget results

        column_ids : int, list, np.ndarray, or str='all', default='all'
            one or more column identification numbers for returning zbudget results

        begin_date : str
            first date where zbudget results are returned

        end_date : str
            last date where zbudget results are returned

        output_interval : str
            output interval greater than or equal to the model simulation time step

        area_conversion_factor : float or int, default=1.0
            factor to convert area units from the default model units
            to the desired output units

        volume_conversion_factor : float or int, default=1.0
            factor to convert volume units from the default model units
            to the desired output units

        Returns
        -------
        pd.DataFrame
            DataFrame of ZBudget output for user-specified columns for a zone

        Note
        ----
        Return value includes Time as the first column whether the user provided it or not
        '''
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, 'IW_ZBudget_GetValues_ForAZone'):
            raise AttributeError('IWFM DLL does not have "{}" procedure. '
                                 'Check for an updated version'.format('IW_ZBudget_GetValues_ForAZone'))

        # check zone_id is an integer
        if not isinstance(zone_id, int):
            raise TypeError('zone_id must be an integer')

        # get possible zones numbers
        zones = self.get_zone_list()

        # check that zone_id is a valid zone ID
        if zone_id not in zones:
            raise ValueError('zone_id was not found in zone definitions provided')

        # get all column headers and column IDs
        column_headers, column_header_ids = self.get_column_headers_for_a_zone(zone_id, include_time=True)

        if column_ids == 'all':
            column_ids = column_header_ids[column_header_ids > 0]

        if isinstance(column_ids, int):
            column_ids = np.array([column_ids])
        
        if isinstance(column_ids, list):
            column_ids = np.array(column_ids)
                
        # valid column_ids should now all be np.ndarray, so validate column_ids
        if not isinstance(column_ids, np.ndarray):
            raise TypeError('column_ids must be an int, list, np.ndarray or str="all"')
            
        # check that all column_ids are in the list of possible 
        # column header ids for the given zone
        if not np.all(np.isin(column_ids, column_header_ids)):
            raise ValueError('one or more column_ids provided are not valid')

        # if column_id 1 i.e. Time is not included, add it.
        if 1 not in column_ids:
            column_ids = np.concatenate((np.array([1]), column_ids))

        # get list of column names from column_ids
        column_headers = np.array(column_headers)
        columns = column_headers[column_ids - 1]

        # convert zone_id to ctypes
        zone_id = ctypes.c_int(zone_id)

        # convert column_ids to ctypes
        n_column_ids = ctypes.c_int(len(column_ids))
        column_ids = (ctypes.c_int*n_column_ids.value)(*column_ids)

        # handle start and end dates
        # get time specs
        dates_list, sim_output_interval = self.get_time_specs()
        
        if begin_date is None:
            begin_date = dates_list[0]
        else:
            self._validate_iwfm_date(begin_date)

            if begin_date not in dates_list:
                raise ValueError('begin_date was not found in the ZBudget '
                                 'file. use get_time_specs() method to check.')
        
        if end_date is None:
            end_date = dates_list[-1]
        else:
            self._validate_iwfm_date(end_date)

            if end_date not in dates_list:
                raise ValueError('end_date was not found in the ZBudget '
                                 'file. use get_time_specs() method to check.')

        if self.is_date_greater(begin_date, end_date):
            raise ValueError('end_date must occur after begin_date')

        if output_interval is None:
            output_interval = sim_output_interval
        
        # get number of timestep intervals
        n_timestep_intervals = ctypes.c_int(self.get_n_intervals(begin_date, end_date, 
                                                                 output_interval, includes_end_date=True))

        # convert beginning and end dates to ctypes
        begin_date = ctypes.create_string_buffer(begin_date.encode('utf-8'))
        end_date = ctypes.create_string_buffer(end_date.encode('utf-8'))

        length_date_string = ctypes.c_int(ctypes.sizeof(begin_date))

        # check output interval is greater than or equal to simulation
        if not self._is_time_interval_greater_or_equal(output_interval, sim_output_interval):
            raise ValueError('output_interval must be greater than or '
                             'equal to the simulation time step')
        
        # convert output_interval to ctypes
        output_interval = ctypes.create_string_buffer(output_interval.encode('utf-8'))
        length_output_interval = ctypes.c_int(ctypes.sizeof(output_interval))

        # convert unit conversion factors to ctypes
        area_conversion_factor = ctypes.c_double(area_conversion_factor)
        volume_conversion_factor = ctypes.c_double(volume_conversion_factor)

        # initialize output variables
        zbudget_values = ((ctypes.c_double*n_column_ids.value)*n_timestep_intervals.value)()
        n_times_out = ctypes.c_int(0)
        status = ctypes.c_int(0)

        
        self.dll.IW_ZBudget_GetValues_ForAZone(ctypes.byref(zone_id),
                                               ctypes.byref(n_column_ids),
                                               column_ids,
                                               begin_date,
                                               end_date,
                                               ctypes.byref(length_date_string),
                                               output_interval,
                                               ctypes.byref(length_output_interval),
                                               ctypes.byref(area_conversion_factor),
                                               ctypes.byref(volume_conversion_factor),
                                               ctypes.byref(n_timestep_intervals),
                                               zbudget_values,
                                               ctypes.byref(n_times_out),
                                               ctypes.byref(status))

        values = np.array(zbudget_values)

        zbudget = pd.DataFrame(data=values, columns=columns)
        zbudget['Time'] = zbudget['Time'].astype('timedelta64[D]') + np.array('1899-12-30', dtype='datetime64')
        
        return zbudget