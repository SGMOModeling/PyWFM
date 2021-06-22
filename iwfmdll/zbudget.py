import ctypes
import numpy as np

from iwfmdll.misc import IWFM_Miscellaneous

class IWFM_ZBudget(IWFM_Miscellaneous):
    ''' IWFM ZBudget Class for interacting with the IWFM DLL

    Parameters
    ----------
    dll_path : str
        file path and name of the IWFM DLL to access IWFM procedures

    zbudget_file_name : str
        file path and name of the budget file

    Returns
    -------
    IWFM_ZBudget Object
        instance of the IWFM_ZBudget class and access to the IWFM Budget 
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
            file name for the zone definition file used to generate the
            list of zones
            
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
        ''' returns a list of all the time stamps and the time interval for the budget 
        
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

    def _get_column_headers_general(self, area_unit, volume_unit):
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
        area_unit : str
            unit of area appearing in the Zbudget column headers

        volume_unit : str
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

    def get_column_headers_for_a_zone(self, zone_id, area_unit, volume_unit, column_list='all'):
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

        area_unit : str
            unit of area appearing in the Zbudget column headers

        volume_unit : str
            unit of volume appearing in the ZBudget column headers

        column_list : int, list, np.ndarray, or 'all'
            list of header column indices. this is based on the results 
            from the get_column_headers_general method

        Returns
        -------
        list
            list of column headers
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

        if (isinstance(column_list, str)) and (column_list == 'all'):
            n_column_list = ctypes.c_int(n_general_columns)
            column_list = (ctypes.c_int*n_column_list.value)(*general_column_indices)
        elif isinstance(column_list, (int, np.ndarray, list)):
            if isinstance(column_list, list):
                column_list = np.array(column_list)
            elif isinstance(column_list, int):
                column_list = np.array([column_list])

            # check values in column list are in general_column_indices
            if not np.all(np.isin(column_list, general_column_indices)):
                raise ValueError('provided indices in column_list are invalid')

            n_column_list = ctypes.c_int(len(column_list))
            column_list = (ctypes.c_int*n_column_list.value)(*column_list)
        
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

        return self._string_to_list_by_array(raw_column_header_string, 
                                             delimiter_position_array, 
                                             n_columns)

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

    