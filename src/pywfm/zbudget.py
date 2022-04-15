import os
import ctypes
import numpy as np
import pandas as pd

from pywfm import DLL_PATH, DLL

from pywfm.misc import IWFMMiscellaneous


class IWFMZBudget(IWFMMiscellaneous):
    """
    IWFM ZBudget Class for interacting with the IWFM API.

    Parameters
    ----------
    zbudget_file_name : str
        File path and name of the budget file

    Returns
    -------
    IWFMZBudget Object
        Instance of the IWFMZBudget class and access to the IWFM Budget
        fortran procedures.
    """

    def __init__(self, zbudget_file_name):

        if not isinstance(zbudget_file_name, str):
            raise TypeError("zbudget_file_name must be a string")

        if not os.path.exists(zbudget_file_name):
            raise FileNotFoundError("{} was not found".format(zbudget_file_name))

        self.zbudget_file_name = zbudget_file_name

        self.dll = ctypes.windll.LoadLibrary(os.path.join(DLL_PATH, DLL))

        # check to see if the open file procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_OpenFile"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_ZBudget_OpenFile")
            )

        # set input variables name and name length
        zbudget_file = ctypes.create_string_buffer(
            self.zbudget_file_name.encode("utf-8")
        )
        length_file_name = ctypes.c_int(ctypes.sizeof(zbudget_file))

        # initialize output variable status
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_OpenFile(
            zbudget_file, ctypes.byref(length_file_name), ctypes.byref(status)
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_budget_file()

    def close_zbudget_file(self):
        """
        Close an open budget file for an IWFM model application.
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_CloseFile"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_ZBudget_CloseFile")
            )

        # initialize output variable status
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_CloseFile(ctypes.byref(status))

    def generate_zone_list_from_file(self, zone_definition_file):
        """
        Generate a list of zones and their neighboring zones based
        on data provided in a text file.

        This file must be in the same format as the Zone Definition
        File used by the Z-Budget post-processor.

        Parameters
        ----------
        zone_definition_file : str
            File name for the zone definition file used to generate the
            list of zones.

        Returns
        -------
        None
            Generates the list of zones and adjacent zones.

        Note
        ----
        See IWFM Sample Model ZBudget folder for format examples.
        """
        # check to see if the open file procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_GenerateZoneList_FromFile"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format(
                    "IW_ZBudget_GenerateZoneList_FromFile"
                )
            )

        # set input variables name and name length
        zone_file = ctypes.create_string_buffer(zone_definition_file.encode("utf-8"))
        length_file_name = ctypes.c_int(ctypes.sizeof(zone_file))

        # initialize output variable status
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GenerateZoneList_FromFile(
            zone_file, ctypes.byref(length_file_name), ctypes.byref(status)
        )

    def _generate_zone_list(self, zone_extent_id, elements, layers, zones, zone_names):
        """
        Private method that generates a list of zones and their neighboring
        zones based on data provided directly by the client software.

        Parameters
        ----------
        zone_extent_id : int
            Valid IWFM zone extent identification number. Options can
            be obtained using the get_zone_extent_ids method.

        elements : list, np.ndarray
            List of element identification numbers used to identify
            zone definitions.

        layers : list, np.ndarray
            List of layer numbers used to identify zone definitions.
            if using the zone extent id for horizontal, this is not used.

        zones : list, np.ndarray
            List of identification numbers used to identify which zone
            each element and layer are specified in.

        zone_names : list
            List of zone names. there can be fewer names than zones defined.

        Returns
        -------
        None
            Generates the zone definitions.
        """
        # check to see if the open file procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_GenerateZoneList"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_ZBudget_GenerateZoneList")
            )

        # convert zone_extent_id to ctypes
        zone_extent_id = ctypes.c_int(zone_extent_id)

        # check that inputs are array-like
        if not isinstance(elements, (np.ndarray, list)):
            raise TypeError("elements must be an array or list")

        if not isinstance(layers, (np.ndarray, list)):
            raise TypeError("layers must be an array or list")

        if not isinstance(zones, (np.ndarray, list)):
            raise TypeError("zones must be an array or list")

        # check elements, layers, zones arrays are 1-D and same length
        if isinstance(elements, list):
            elements = np.array(elements)

        if isinstance(layers, list):
            layers = np.array(layers)

        if isinstance(zones, list):
            zones = np.array(zones)

        if (
            (elements.shape == layers.shape)
            & (elements.shape == zones.shape)
            & (len(elements.shape) == 1)
        ):
            n_elements = ctypes.c_int(elements.shape[0])
            elements = (ctypes.c_int * n_elements.value)(*elements)
            layers = (ctypes.c_int * n_elements.value)(*layers)
            zones = (ctypes.c_int * n_elements.value)(*zones)

        else:
            raise ValueError(
                "elements, layers, and zones are 1-D "
                "arrays and must be the same length."
            )

        # convert list of zone names to string with array of delimiter locations
        n_zones_with_names = ctypes.c_int(len(zone_names))

        zones_with_names = (ctypes.c_int * n_zones_with_names.value)(
            *[val + 1 for val in range(n_zones_with_names.value)]
        )

        # initialize zone_names_string, delimiter_position_array, and length_zone_names
        zone_names_string = ""
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
        zone_names_string = ctypes.create_string_buffer(
            zone_names_string.encode("utf-8")
        )
        delimiter_position_array = (ctypes.c_int * n_zones_with_names.value)(
            *delimiter_position_array
        )
        length_zone_names = ctypes.c_int(length_zone_names)

        # initialize output variables
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GenerateZoneList(
            ctypes.byref(zone_extent_id),
            ctypes.byref(n_elements),
            elements,
            layers,
            zones,
            ctypes.byref(n_zones_with_names),
            zones_with_names,
            ctypes.byref(length_zone_names),
            zone_names_string,
            delimiter_position_array,
            ctypes.byref(status),
        )

    def get_n_zones(self):
        """
        Return the number of zones specified in the zbudget.

        Returns
        -------
        int
            Number of zones.

        See Also
        --------
        IWFMZBudget.get_zone_list : Return the list of zone numbers.
        IWFMZBudget.get_zone_names : Return the zone names specified
            by the user in the zone definitions.

        Example
        -------
        >>> from pywfm import IWFMZBudget
        >>> zbud_file = '../Results/GW_ZBud.hdf'
        >>> zone_defs = '../ZBudget/ZoneDef_SRs.dat'
        >>> gw_zbud = IWFMZBudget(zbud_file)
        >>> gw_zbud.generate_zone_list_from_file(zone_defs)
        >>> gw_zbud.get_n_zones()
        2
        >>> gw_zbud.close_zbudget_file()
        """
        # check to see if the open file procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_GetNZones"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_ZBudget_GetNZones")
            )

        # initialize output variables
        n_zones = ctypes.c_int(0)

        # initialize output variable status
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetNZones(ctypes.byref(n_zones), ctypes.byref(status))

        return n_zones.value

    def get_zone_list(self):
        """
        Return the list of zone numbers.

        Returns
        -------
        np.ndarray
            Array of zone numbers.

        See Also
        --------
        IWFMZBudget.get_n_zones : Return the number of zones specified
            in the zbudget.
        IWFMZBudget.get_zone_names : Return the zone names specified by
            the user in the zone definitions.

        Example
        -------
        >>> from pywfm import IWFMZBudget
        >>> zbud_file = '../Results/GW_ZBud.hdf'
        >>> zone_defs = '../ZBudget/ZoneDef_SRs.dat'
        >>> gw_zbud = IWFMZBudget(zbud_file)
        >>> gw_zbud.generate_zone_list_from_file(zone_defs)
        >>> gw_zbud.get_zone_list()
        array([1, 2])
        >>> gw_zbud.close_zbudget_file()
        """
        # check to see if the open file procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_GetZoneList"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_ZBudget_GetZoneList")
            )

        # get number of zones
        n_zones = ctypes.c_int(self.get_n_zones())

        # initialize output variables
        zone_list = (ctypes.c_int * n_zones.value)()

        # initialize output variable status
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetZoneList(
            ctypes.byref(n_zones), zone_list, ctypes.byref(status)
        )

        return np.array(zone_list)

    def get_n_time_steps(self):
        """
        Return the number of time steps where zbudget data is available.

        Returns
        -------
        int
            Number of time steps.

        See Also
        --------
        IWFMZBudget.get_time_specs : Return a list of all the time
            stamps and the time interval for the zbudget.

        Example
        -------
        >>> from pywfm import IWFMZBudget
        >>> zbud_file = '../Results/GW_ZBud.hdf'
        >>> zone_defs = '../ZBudget/ZoneDef_SRs.dat'
        >>> gw_zbud = IWFMZBudget(zbud_file)
        >>> gw_zbud.generate_zone_list_from_file(zone_defs)
        >>> gw_zbud.get_n_time_steps()
        3653
        >>> gw_zbud.close_zbudget_file()
        """
        # check to see if the open file procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_GetNTimeSteps"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_ZBudget_GetNTimeSteps")
            )

        # initialize output variables
        n_time_steps = ctypes.c_int(0)

        # initialize output variable status
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetNTimeSteps(
            ctypes.byref(n_time_steps), ctypes.byref(status)
        )

        return n_time_steps.value

    def get_time_specs(self):
        """
        Return a list of all the time stamps and the time interval
        for the zbudget

        Returns
        -------
        dates_list : list
            Dates and times for zbudget results.

        interval: str
            Time interval for dates.

        See Also
        --------
        IWFMZBudget.get_n_time_steps : Return the number of time steps
            where zbudget data is available.

        Example
        -------
        >>> from pywfm import IWFMZBudget
        >>> zbud_file = '../Results/GW_ZBud.hdf'
        >>> zone_defs = '../ZBudget/ZoneDef_SRs.dat'
        >>> gw_zbud = IWFMZBudget(zbud_file)
        >>> gw_zbud.generate_zone_list_from_file(zone_defs)
        >>> dates, interval = gw_zbud.get_time_specs()
        >>> dates
        ['10/01/1990_24:00',
         '10/02/1990_24:00',
         '10/03/1990_24:00',
         '10/04/1990_24:00',
         '10/05/1990_24:00',
         ...]
        >>> interval
        '1DAY'
        >>> gw_zbud.close_zbudget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_GetTimeSpecs"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_ZBudget_GetTimeSpecs")
            )

        # get number of time steps
        n_time_steps = ctypes.c_int(self.get_n_time_steps())

        # set the length of the dates string to 16 times n_timesteps
        length_date_string = ctypes.c_int(16 * n_time_steps.value)

        # set the length of the time interval
        length_time_interval = ctypes.c_int(8)

        # initialize output variables
        raw_dates_string = ctypes.create_string_buffer(length_date_string.value)
        time_interval = ctypes.create_string_buffer(length_time_interval.value)
        delimiter_position_array = (ctypes.c_int * n_time_steps.value)()
        status = ctypes.c_int(0)

        # IW_ZBudget_GetTimeSpecs(cDataDatesAndTimes,iLenDates,cInterval,iLenInterval,NData,iLocArray,iStat)
        self.dll.IW_ZBudget_GetTimeSpecs(
            raw_dates_string,
            ctypes.byref(length_date_string),
            time_interval,
            ctypes.byref(length_time_interval),
            ctypes.byref(n_time_steps),
            delimiter_position_array,
            ctypes.byref(status),
        )

        dates_list = self._string_to_list_by_array(
            raw_dates_string, delimiter_position_array, n_time_steps
        )

        interval = time_interval.value.decode("utf-8")

        return dates_list, interval

    def _get_column_headers_general(self, area_unit="SQ FT", volume_unit="CU FT"):
        """
        Private method returning the Z-Budget column headers (i.e. titles).

        For flow processes that simulate flow exchange between neighboring
        zones (e.g. groundwater process) the inflow and outflow columns
        are lumped into two columns (e.g. “Inflows from Adjacent Zones”
        and “Outflows to Adjacent Zones”) instead of identifying inflows
        from and outflows to individual neighboring zones. These column
        headers apply to any zone regardless of the number of neighboring
        zones.

        Parameters
        ----------
        area_unit : str, default 'SQ FT'
            Unit of area appearing in the Zbudget column headers.

        volume_unit : str, default 'CU FT'
            Unit of volume appearing in the ZBudget column headers.

        Returns
        -------
        list
            List of column names.
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_GetColumnHeaders_General"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format(
                    "IW_ZBudget_GetColumnHeaders_General"
                )
            )

        # set the maximum number of columns
        max_n_column_headers = ctypes.c_int(200)

        # get string length for area_unit and volume_unit
        unit_length = ctypes.c_int(max(len(area_unit), len(volume_unit)))

        # set total length of column headers
        length_column_headers = ctypes.c_int(max_n_column_headers.value * 30)

        # convert area_unit and volume_unit to ctypes
        area_unit = ctypes.create_string_buffer(area_unit.encode("utf-8"))
        volume_unit = ctypes.create_string_buffer(volume_unit.encode("utf-8"))

        # initialize output variables
        raw_column_header_string = ctypes.create_string_buffer(
            length_column_headers.value
        )
        n_columns = ctypes.c_int(0)
        delimiter_position_array = (ctypes.c_int * max_n_column_headers.value)()
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetColumnHeaders_General(
            ctypes.byref(max_n_column_headers),
            area_unit,
            volume_unit,
            ctypes.byref(unit_length),
            ctypes.byref(length_column_headers),
            raw_column_header_string,
            ctypes.byref(n_columns),
            delimiter_position_array,
            ctypes.byref(status),
        )

        return self._string_to_list_by_array(
            raw_column_header_string, delimiter_position_array, n_columns
        )

    def get_column_headers_for_a_zone(
        self,
        zone_id,
        column_list="all",
        area_unit="SQ FT",
        volume_unit="CU FT",
        include_time=True,
    ):
        """
        Return the Z-Budget column headers (i.e. titles) for a
        specified zone for selected data columns.

        For flow processes that simulate flow exchange between neighboring
        zones (e.g. groundwater process), the column headers for inflows
        from and outflows to neighboring zones are listed separately
        for each neighboring zone.

        Parameters
        ----------
        zone_id : int
            Zone identification number used to return the column headers.

        column_list : int, list, np.ndarray, or str='all', default 'all'
            List of header column indices.

            Note
            ----
            This is based on the results from the get_column_headers_general
            method

        area_unit : str, default 'SQ FT'
            Unit of area appearing in the Zbudget column headers.

        volume_unit : str, default 'CU FT'
            Unit of volume appearing in the ZBudget column headers.

        include_time : boolean, default True
            Flag to determine if columns headers include the time column.

        Returns
        -------
        column_headers : list
            Column names.

        column_indices : np.ndarray
            Indices for column names.

        Note
        ----
        These columns are referred to as “diversified columns” since
        the inflows from and outflows to each neighboring zone are
        treated as separate columns.

        Example
        -------
        >>> from pywfm import IWFMZBudget
        >>> zbud_file = '../Results/GW_ZBud.hdf'
        >>> zone_defs = '../ZBudget/ZoneDef_SRs.dat'
        >>> gw_zbud = IWFMZBudget(zbud_file)
        >>> gw_zbud.generate_zone_list_from_file(zone_defs)
        >>> column_names, column_ids = gw_zbud.get_column_headers_for_a_zone(1)
        >>> column_names
        ['Time',
         'GW Storage_Inflow (+)',
         'GW Storage_Outflow (-)',
         'Streams_Inflow (+)',
         'Streams_Outflow (-)',
         'Tile Drains_Inflow (+)',
         'Tile Drains_Outflow (-)',
         'Subsidence_Inflow (+)',
         'Subsidence_Outflow (-)',
         'Deep Percolation_Inflow (+)',
         'Deep Percolation_Outflow (-)',
         'Specified Head BC_Inflow (+)',
         'Specified Head BC_Outflow (-)',
         'Small Watershed Baseflow_Inflow (+)',
         'Small Watershed Baseflow_Outflow (-)',
         'Small Watershed Percolation_Inflow (+)',
         'Small Watershed Percolation_Outflow (-)',
         'Diversion Recoverable Loss_Inflow (+)',
         'Diversion Recoverable Loss_Outflow (-)',
         'Bypass Recoverable Loss_Inflow (+)',
         'Bypass Recoverable Loss_Outflow (-)',
         'Lakes_Inflow (+)',
         'Lakes_Outflow (-)',
         'Pumping by Element_Inflow (+)',
         'Pumping by Element_Outflow (-)',
         'Root Water Uptake_Inflow (+)',
         'Root Water Uptake_Outflow (-)',
         'Inflow from zone 2 (+)',
         'Outflow to zone 2 (-)',
         'Discrepancy (=)',
         'Absolute Storage']
        >>> column_ids
        array([ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17,
               18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31,  0,  0,  0,
                0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
                0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0])
        >>> gw_zbud.close_zbudget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_GetColumnHeaders_ForAZone"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format(
                    "IW_ZBudget_GetColumnHeaders_ForAZone"
                )
            )

        # convert zone_id to ctypes
        zone_id = ctypes.c_int(zone_id)

        # get general column headers
        general_columns = self._get_column_headers_general(area_unit, volume_unit)

        # get number of general columns
        n_general_columns = len(general_columns)

        # get column indices for general_columns
        general_column_indices = np.arange(1, n_general_columns + 1)

        # validate column_list
        if isinstance(column_list, str) and column_list == "all":
            column_list = general_column_indices

        if isinstance(column_list, int):
            column_list = np.array([column_list])

        if isinstance(column_list, list):
            column_list = np.array(column_list)

        # now column_list should be np.ndarray, so validate type
        if not isinstance(column_list, np.ndarray):
            raise TypeError("column_list must be an int, list, np.ndarray, or 'all'")

        # check values in column list are in general_column_indices
        if not np.all(np.isin(column_list, general_column_indices)):
            raise ValueError("one or more indices provided in column_list are invalid")

        # convert column_list to ctypes
        if include_time:
            n_column_list = ctypes.c_int(len(column_list))
            column_list = (ctypes.c_int * n_column_list.value)(*column_list)
        else:
            n_column_list = ctypes.c_int(len(column_list) - 1)
            column_list = (ctypes.c_int * n_column_list.value)(
                *column_list[column_list != 1]
            )

        # set the maximum number of columns
        max_n_column_headers = ctypes.c_int(200)

        # get string length for area_unit and volume_unit
        unit_length = ctypes.c_int(max(len(area_unit), len(volume_unit)))

        # set total length of column headers
        length_column_headers = ctypes.c_int(max_n_column_headers.value * 30)

        # convert area_unit and volume_unit to ctypes
        area_unit = ctypes.create_string_buffer(area_unit.encode("utf-8"))
        volume_unit = ctypes.create_string_buffer(volume_unit.encode("utf-8"))

        # initialize output variables
        raw_column_header_string = ctypes.create_string_buffer(
            length_column_headers.value
        )
        n_columns = ctypes.c_int(0)
        delimiter_position_array = (ctypes.c_int * max_n_column_headers.value)()
        diversified_columns_list = (ctypes.c_int * max_n_column_headers.value)()
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetColumnHeaders_ForAZone(
            ctypes.byref(zone_id),
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
            ctypes.byref(status),
        )

        column_headers = self._string_to_list_by_array(
            raw_column_header_string, delimiter_position_array, n_columns
        )

        column_indices = np.array(diversified_columns_list)

        return column_headers, column_indices

    def get_zone_names(self):
        """
        Return the zone names specified by the user in the zone definitions.

        Returns
        -------
        list
            Names for each zone defined.

        See Also
        --------
        IWFMZBudget.get_n_zones : Return the number of zones specified
            in the zbudget.
        IWFMZBudget.get_zone_list : Return the list of zone numbers.

        Example
        -------
        >>> from pywfm import IWFMZBudget
        >>> zbud_file = '../Results/GW_ZBud.hdf'
        >>> zone_defs = '../ZBudget/ZoneDef_SRs.dat'
        >>> gw_zbud = IWFMZBudget(zbud_file)
        >>> gw_zbud.generate_zone_list_from_file(zone_defs)
        >>> gw_zbud.get_zone_names()
        ['Region1', 'Region2']
        >>> gw_zbud.close_zbudget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_GetZoneNames"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_ZBudget_GetZoneNames")
            )

        # get number of zones
        n_zones = ctypes.c_int(self.get_n_zones())

        # set size of string used to retrieve the names
        length_zone_names_string = ctypes.c_int(n_zones.value * 30)

        # initialize output variables
        raw_zone_names = ctypes.create_string_buffer(length_zone_names_string.value)
        delimiter_location_array = (ctypes.c_int * n_zones.value)()
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetZoneNames(
            ctypes.byref(n_zones),
            ctypes.byref(length_zone_names_string),
            raw_zone_names,
            delimiter_location_array,
            ctypes.byref(status),
        )

        return self._string_to_list_by_array(
            raw_zone_names, delimiter_location_array, n_zones
        )

    def get_n_title_lines(self):
        """
        Return the number of title lines in a ZBudget.

        Returns
        -------
        int
            Number of title lines.

        See Also
        --------
        IWFMZBudget.get_title_lines : Return the title lines for the
            ZBudget data for a zone.

        Example
        -------
        >>> from pywfm import IWFMZBudget
        >>> zbud_file = '../Results/GW_ZBud.hdf'
        >>> zone_defs = '../ZBudget/ZoneDef_SRs.dat'
        >>> gw_zbud = IWFMZBudget(zbud_file)
        >>> gw_zbud.generate_zone_list_from_file(zone_defs)
        >>> gw_zbud.get_n_title_lines()
        3
        >>> gw_zbud.close_zbudget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_GetNTitleLines"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_ZBudget_GetNTitleLines")
            )

        # initialize output variables
        n_title_lines = ctypes.c_int(0)
        status = ctypes.c_int(0)

        # IW_Budget_GetNTitleLines(NTitles,iStat)
        self.dll.IW_ZBudget_GetNTitleLines(
            ctypes.byref(n_title_lines), ctypes.byref(status)
        )

        return n_title_lines.value

    def get_title_lines(
        self,
        zone_id,
        area_conversion_factor=1.0,
        area_unit="SQ FT",
        volume_unit="CU FT",
    ):
        """
        Return the title lines for the ZBudget data for a zone.

        Parameters
        ----------
        zone_id : int
            Zone identification number used to retrieve the title lines.

        area_conversion_factor : int, float, default 1.0
            Factor used to convert area units between the default model
            unit and the desired output unit.
            e.g. ft^2 --> Acre = 2.29568E-05

        area_unit : str, default 'SQ FT'
            Desired output unit for area.

        volume_unit : str, default 'CU FT'
            Desired output unit for volume.

        Returns
        -------
        list
            Title lines for zone.

        Note
        ----
        Title lines are useful for display when ZBudget data is
        imported into files (text, spreadsheet, etc.).

        See Also
        --------
        IWFMZBudget.get_n_title_lines : Return the number of title lines
            in a ZBudget

        Example
        -------
        >>> from pywfm import IWFMZBudget
        >>> zbud_file = '../Results/GW_ZBud.hdf'
        >>> zone_defs = '../ZBudget/ZoneDef_SRs.dat'
        >>> gw_zbud = IWFMZBudget(zbud_file)
        >>> gw_zbud.generate_zone_list_from_file(zone_defs)
        >>> gw_zbud.get_title_lines(1)
        ['IWFM (v2015.0.1273)',
         'GROUNDWATER ZONE BUDGET IN CU FT FOR ZONE 1 (Region1)',
         'ZONE AREA: 8610918912.00 SQ FT']
        >>> gw_zbud.close_zbudget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_GetTitleLines"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_ZBudget_GetTitleLines")
            )

        # get number of title lines
        n_title_lines = ctypes.c_int(self.get_n_title_lines())

        # convert zone_id to ctypes
        zone_id = ctypes.c_int(zone_id)

        # convert area conversion factor and units to ctypes
        area_conversion_factor = ctypes.c_double(area_conversion_factor)
        area_unit = ctypes.create_string_buffer(area_unit.encode("utf-8"))

        # convert volume units to ctypes
        volume_unit = ctypes.create_string_buffer(volume_unit.encode("utf-8"))

        # get character length of units
        length_unit_string = ctypes.c_int(
            max(ctypes.sizeof(area_unit), ctypes.sizeof(volume_unit))
        )

        # set length of title string
        length_title_string = ctypes.c_int(n_title_lines.value * 200)

        # initialize output variables
        raw_title_string = ctypes.create_string_buffer(length_title_string.value)
        delimiter_position_array = (ctypes.c_int * n_title_lines.value)()
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetTitleLines(
            ctypes.byref(n_title_lines),
            ctypes.byref(zone_id),
            ctypes.byref(area_conversion_factor),
            area_unit,
            volume_unit,
            ctypes.byref(length_unit_string),
            raw_title_string,
            ctypes.byref(length_title_string),
            delimiter_position_array,
            ctypes.byref(status),
        )

        return self._string_to_list_by_array(
            raw_title_string, delimiter_position_array, n_title_lines
        )

    def get_values_for_some_zones_for_an_interval(
        self,
        zone_ids="all",
        column_ids="all",
        current_date=None,
        output_interval=None,
        area_conversion_factor=1.0,
        area_units="SQ FT",
        volume_conversion_factor=1.0,
        volume_units="CU FT",
    ):
        """
        Return specified zone flow values for one or more zones at a given
        date and time interval.

        Parameters
        ----------
        zone_ids : int, list, np.ndarray, or str='all', default 'all'
            One or more zone identification numbers to retrieve ZBudget
            data

        column_ids : int, list, or str='all', default 'all'
            One or more data column indices to retrieve ZBudget data

        current_date : str or None, default None
            Valid IWFM date used to return ZBudget data.

            Important
            ---------
            If None (default), uses the first date.

        output_interval : str or None, default None
            Valid IWFM output time interval for returning ZBudget data.

            Note
            ----
            This must be greater than or equal to the simulation time
            step.

        area_conversion_factor : float or int, default 1.0
            Factor to convert area units from the default model units
            to the desired output units.

        area_units : str, default 'SQ FT'
            output units of area

        volume_conversion_factor : float or int, default 1.0
            Factor to convert volume units from the default model units
            to the desired output units.

        volume_units : str, default 'CU FT'
            output units of volume

        Returns
        -------
        dict
            DataFrames of ZBudget output for user-specified columns by
            zone names

        Note
        ----
        Return value includes Time as the first column whether the user
        provided it or not.

        See Also
        --------
        IWFMZBudget.get_values_for_a_zone : Return specified ZBudget
            data columns for a specified zone for a time period.

        Examples
        --------
        >>> from pywfm import IWFMZBudget
        >>> zbud_file = '../Results/GW_ZBud.hdf'
        >>> zone_defs = '../ZBudget/ZoneDef_SRs.dat'
        >>> gw_zbud = IWFMZBudget(zbud_file)
        >>> gw_zbud.generate_zone_list_from_file(zone_defs)
        >>> zone_values = gw_zbud.get_values_for_some_zones_for_an_interval()
        >>> zone_values['Region1']
                Time GW Storage_Inflow (+) GW Storage_Outflow (-) Streams_Inflow (+) Streams_Outflow (-) Tile Drains_Inflow (+) Tile Drains_Outflow (-) Subsidence_Inflow (+) Subsidence_Outflow (-) Deep Percolation_Inflow (+) ... Lakes_Inflow (+) Lakes_Outflow (-) Pumping by Element_Inflow (+) Pumping by Element_Outflow (-) Root Water Uptake_Inflow (+) Root Water Uptake_Outflow (-) Inflow from zone 2 (+) Outflow to zone 2 (-) Discrepancy (=) Absolute Storage
        0 1990-10-01              0.888134           3.152751e+09                0.0                 0.0                    0.0                     0.0                   0.0           7.384521e+06                         0.0 ...     3.068518e+09               0.0                           0.0                            0.0                          0.0                           0.0            9448.000542         499542.470953        0.822217     2.507244e+11
        >>> gw_zbud.close_zbudget_file()

        >>> from pywfm import IWFMZBudget
        >>> zbud_file = '../Results/GW_ZBud.hdf'
        >>> zone_defs = '../ZBudget/ZoneDef_SRs.dat'
        >>> gw_zbud = IWFMZBudget(zbud_file)
        >>> gw_zbud.generate_zone_list_from_file(zone_defs)
        >>> gw_zbud.get_values_for_some_zones_for_an_interval(1, [1, 2, 3])
        {'Region1':         Time  GW Storage_Inflow (+)  GW Storage_Outflow (-)
                    0 1990-10-01               0.888134            3.152751e+09}
        >>> gw_zbud.close_zbudget_file()

        >>> from pywfm import IWFMZBudget
        >>> zbud_file = '../Results/GW_ZBud.hdf'
        >>> zone_defs = '../ZBudget/ZoneDef_SRs.dat'
        >>> gw_zbud = IWFMZBudget(zbud_file)
        >>> gw_zbud.generate_zone_list_from_file(zone_defs)
        >>> gw_zbud.get_values_for_some_zones_for_an_interval(column_ids=[[28, 29], [28, 29, 30, 31]])
        {'Region1':         Time  Inflow from zone 2 (+)  Outflow to zone 2 (-)
                    0 1990-10-01             9448.000542          499542.470953,
         'Region2':         Time  Inflow from zone 1 (+)  Outflow to zone 1 (-)  Discrepancy (=) Absolute Storage
                    0 1990-10-01           499542.470953            9448.000542        -0.151709     2.492766e+11}
        >>> gw_zbud.close_zbudget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_GetValues_ForSomeZones_ForAnInterval"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format(
                    "IW_ZBudget_GetValues_ForSomeZones_ForAnInterval"
                )
            )

        # get all zone ids
        zones = self.get_zone_list()

        # check that zone_ids are valid
        if isinstance(zone_ids, str) and zone_ids == "all":
            zone_ids = zones

        if isinstance(zone_ids, int):
            zone_ids = np.array([zone_ids])

        if isinstance(zone_ids, list):
            zone_ids = np.array(zone_ids)

        # now zone_ids should all be np.ndarray, so check if np.ndarray
        if not isinstance(zone_ids, np.ndarray):
            raise TypeError('zone_ids must be an int, list, np.ndarray, or str="all"')

        # make sure all zone_ids are valid zones
        if not np.all(np.isin(zone_ids, zones)):
            raise ValueError(
                "one or more zone_ids were not found in zone definitions provided"
            )

        # convert zone_ids to ctypes
        n_zones = ctypes.c_int(len(zone_ids))
        zone_ids = (ctypes.c_int * n_zones.value)(*zone_ids)

        # get all possible column ids for each zone and place in zone_header_array
        zone_header_array = []
        column_name_array = []
        n_columns_max = 0

        for zone_id in zone_ids:

            column_names, column_header_ids = self.get_column_headers_for_a_zone(
                zone_id, area_unit=area_units, volume_unit=volume_units, include_time=True
            )

            n_columns = len(column_header_ids[column_header_ids > 0])

            if n_columns > n_columns_max:
                n_columns_max = n_columns

            zone_header_array.append(column_header_ids)
            column_name_array.append(column_names)

        zone_header_array = np.array(zone_header_array)[:, :n_columns_max]

        # handle different options for providing column_ids
        # all must be converted to 2D arrays with each row having same length
        if isinstance(column_ids, str) and column_ids == "all":
            column_ids = zone_header_array

        if isinstance(column_ids, int):
            # add the 'Time' column if user did not include it
            if column_ids != 1:
                column_ids = np.array([[1, column_ids]])

            else:
                print(
                    "Note: only the time column will be returned for the zone requested"
                )
                column_ids = np.array([[column_ids]])

        if isinstance(column_ids, list):

            # first sort each row
            if all([isinstance(val, int) for val in column_ids]):
                if len(column_ids) > 1:
                    column_ids = sorted(column_ids)

                # add the 'Time' column if user did not include it
                if 1 not in column_ids:
                    column_ids = [1] + column_ids

                max_row_length = len(column_ids)

                column_ids = np.array([column_ids])

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

        # valid inputs should all now be np.ndarray so validate type
        if not isinstance(column_ids, np.ndarray):
            raise TypeError("column_ids must be an int, list, or str='all'")

        # check: number of rows in column_ids must match number of zones
        if (column_ids.ndim == 2) and (column_ids.shape[0] != n_zones.value):
            raise ValueError(
                "Each number of rows in column_ids "
                "must match number of zones\nThe number "
                "of zones provided is {}.\nThe number "
                "of zones implied by column_ids is {}".format(
                    n_zones.value, column_ids.shape[0]
                )
            )

        # check row by row if the column_ids are valid for a particular zone
        # this will only catch the first error it finds
        # only check the non-zero values
        for i, row in enumerate(column_ids):
            if not np.all(np.isin(row[row > 0], zone_header_array[i])):
                raise ValueError(
                    "column_ids for zone {} are invalid".format(np.array(zone_ids)[i])
                )

        max_n_columns = ctypes.c_int(column_ids.shape[-1])

        # convert column_ids to 2D ctypes array
        column_id_array = ((ctypes.c_int * max_n_columns.value) * n_zones.value)()
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
                raise ValueError(
                    "current_date was not found in the ZBudget "
                    "file. use get_time_specs() method to check."
                )

        # convert current_date to ctypes
        current_date = ctypes.create_string_buffer(current_date.encode("utf-8"))
        length_date_string = ctypes.c_int(ctypes.sizeof(current_date))

        # handle output interval
        if output_interval is None:
            output_interval = sim_output_interval

        # check output interval is greater than or equal to simulation
        if not self._is_time_interval_greater_or_equal(
            output_interval, sim_output_interval
        ):
            raise ValueError(
                "output_interval must be greater than or "
                "equal to the simulation time step"
            )

        # convert output_interval to ctypes
        output_interval = ctypes.create_string_buffer(output_interval.encode("utf-8"))
        length_output_interval = ctypes.c_int(ctypes.sizeof(output_interval))

        # convert unit conversion factors to ctypes
        area_conversion_factor = ctypes.c_double(area_conversion_factor)
        volume_conversion_factor = ctypes.c_double(volume_conversion_factor)

        # initialize output variables
        zbudget_values = ((ctypes.c_double * max_n_columns.value) * n_zones.value)()
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetValues_ForSomeZones_ForAnInterval(
            ctypes.byref(n_zones),
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
            ctypes.byref(status),
        )

        values = np.array(zbudget_values)

        # get zone names
        zone_names_all = np.array(self.get_zone_names())

        # convert zone_ids and column_id_array back to np.ndarray
        zone_ids = np.array(zone_ids)
        column_id_array = np.array(column_id_array)

        zone_names = zone_names_all[zone_ids - 1]

        # convert output to a dictionary of DataFrames by zone name
        value_dict = {}
        for i, z in enumerate(zone_names):
            zone_columns = column_id_array[i] > 0
            col_ids = column_id_array[i, zone_columns]
            col_names = np.array(column_name_array[i])[col_ids - 1]

            df = pd.DataFrame(
                data=np.atleast_2d(values[i, zone_columns]), columns=col_names
            )
            df["Time"] = df["Time"].astype("timedelta64[D]") + np.array(
                "1899-12-30", dtype="datetime64"
            )

            value_dict[z] = df

        return value_dict

    def get_values_for_a_zone(
        self,
        zone_id,
        column_ids="all",
        begin_date=None,
        end_date=None,
        output_interval=None,
        area_conversion_factor=1.0,
        area_units="SQ FT",
        volume_conversion_factor=1.0,
        volume_units="CU FT",
    ):
        """
        Return specified Z-Budget data columns for a specified zone for
        a time period.

        Parameters
        ----------
        zone_id : int
            Zone identification number used to return zbudget results.

        column_ids : int, list, np.ndarray, or str='all', default 'all'
            One or more column identification numbers for returning
            ZBudget results.

        begin_date : str
            First date where zbudget results are returned.

        end_date : str
            Last date where zbudget results are returned.

        output_interval : str
            Output interval greater than or equal to the model
            simulation time step.

        area_conversion_factor : float or int, default 1.0
            Factor to convert area units from the default model units
            to the desired output units.

        area_units : str, default 'SQ FT'
            output units of area

        volume_conversion_factor : float or int, default 1.0
            Factor to convert volume units from the default model units
            to the desired output units.

        volume_units : str, default 'CU FT'
            output units of volume

        Returns
        -------
        pd.DataFrame
            DataFrame of ZBudget output for user-specified columns for
            a zone.

        Note
        ----
        Return value includes Time as the first column whether the user
        provided it or not.

        See Also
        --------
        IWFMZBudget.get_values_for_some_zones_for_an_interval : Return
            specified zone flow values for one or more zones at a given
            date and time interval.

        Example
        -------
        >>> from pywfm import IWFMZBudget
        >>> zbud_file = '../Results/GW_ZBud.hdf'
        >>> zone_defs = '../ZBudget/ZoneDef_SRs.dat'
        >>> gw_zbud = IWFMZBudget(zbud_file)
        >>> gw_zbud.generate_zone_list_from_file(zone_defs)
        >>> gw_zbud.get_values_for_a_zone(1, begin_date='10/01/1997_24:00', end_date='10/31/1997_24:00', volume_conversion_factor=2.295684E-08)
                  Time GW Storage_Inflow (+) GW Storage_Outflow (-) Streams_Inflow (+) Streams_Outflow (-) Tile Drains_Inflow (+) Tile Drains_Outflow (-) Subsidence_Inflow (+) Subsidence_Outflow (-) Deep Percolation_Inflow (+) ... Lakes_Inflow (+) Lakes_Outflow (-) Pumping by Element_Inflow (+) Pumping by Element_Outflow (-) Root Water Uptake_Inflow (+) Root Water Uptake_Outflow (-) Inflow from zone 2 (+) Outflow to zone 2 (-) Discrepancy (=) Absolute Storage
         0  1997-10-01             79.117137               3.273784           2.736884                 0.0                    0.0                     0.0              0.075730               0.000803                    1.014421 ...         0.174256          0.001044                           0.0                      91.737228                          0.0                           0.0              11.439488              0.011498    6.061790e-06     12682.016587
         1  1997-10-02              3.476564               6.531435           0.983505                 0.0                    0.0                     0.0              0.000181               0.048284                    1.456883 ...         0.168174          0.002426                           0.0                       0.000000                          0.0                           0.0               0.057273              0.012413   -6.353508e-09     12685.071458
         2  1997-10-03              0.118540               3.098311           1.028430                 0.0                    0.0                     0.0              0.000023               0.009861                    1.333921 ...         0.144118          0.003028                           0.0                       0.000000                          0.0                           0.0               0.051278              0.017210   -6.352258e-09     12688.051229
         3  1997-10-04              0.124331               3.139859           1.055758                 0.0                    0.0                     0.0              0.000035               0.000891                    1.356049 ...         0.130077          0.003131                           0.0                       0.000000                          0.0                           0.0               0.045703              0.020294   -6.350949e-09     12691.066758
         4  1997-10-05              0.125371               3.137400           1.071419                 0.0                    0.0                     0.0              0.000035               0.000828                    1.345139 ...         0.122925          0.002835                           0.0                       0.000000                          0.0                           0.0               0.045204              0.021375   -6.349395e-09     12694.078787
         5  1997-10-06              0.121523               3.131010           1.080384                 0.0                    0.0                     0.0              0.000034               0.000826                    1.336899 ...         0.120920          0.003890                           0.0                       0.000000                          0.0                           0.0               0.045043              0.021543   -6.346893e-09     12697.088273
         6  1997-10-07              0.119390               3.127247           1.085778                 0.0                    0.0                     0.0              0.000034               0.000825                    1.331394 ...         0.119790          0.004249                           0.0                       0.000000                          0.0                           0.0               0.044929              0.021578   -6.343586e-09     12700.096130
         7  1997-10-08              0.118504               3.125456           1.089236                 0.0                    0.0                     0.0              0.000033               0.000825                    1.327955 ...         0.119299          0.004664                           0.0                       0.000000                          0.0                           0.0               0.044825              0.021610   -6.329593e-09     12703.103082
         8  1997-10-09              0.116697               3.121263           1.089829                 0.0                    0.0                     0.0              0.000033               0.000824                    1.325716 ...         0.119320          0.005395                           0.0                       0.000000                          0.0                           0.0               0.044724              0.021658   -8.351564e-09     12706.107648
         9  1997-10-10              0.110528               3.069641           1.046827                 0.0                    0.0                     0.0              0.000031               0.000808                    1.323624 ...         0.119355          0.005760                           0.0                       0.000000                          0.0                           0.0               0.044625              0.021718   -6.412480e-09     12709.066761
        10  1997-10-11              0.103343               3.019542           1.013182                 0.0                    0.0                     0.0              0.000029               0.000792                    1.310378 ...         0.121383          0.003774                           0.0                       0.000000                          0.0                           0.0               0.044529              0.021787   -6.397671e-09     12711.982960
        11  1997-10-12              0.097684               2.989921           0.992680                 0.0                    0.0                     0.0              0.000027               0.000783                    1.302120 ...         0.125047          0.002714                           0.0                       0.000000                          0.0                           0.0               0.044449              0.021756   -6.392872e-09     12714.875197
        12  1997-10-13              0.092270               2.977330           0.980767                 0.0                    0.0                     0.0              0.000025               0.000779                    1.303162 ...         0.127959          0.001985                           0.0                       0.000000                          0.0                           0.0               0.044371              0.021740   -6.388498e-09     12717.760257
        13  1997-10-14              0.087135               2.972108           0.974152                 0.0                    0.0                     0.0              0.000024               0.000777                    1.307402 ...         0.129874          0.001615                           0.0                       0.000000                          0.0                           0.0               0.044288              0.021767   -6.380029e-09     12720.645231
        14  1997-10-15              0.083334               2.970342           0.970651                 0.0                    0.0                     0.0              0.000023               0.000777                    1.311762 ...         0.130990          0.001515                           0.0                       0.000000                          0.0                           0.0               0.044203              0.021831   -6.348849e-09     12723.532238
        15  1997-10-16              0.080477               2.969707           0.968900                 0.0                    0.0                     0.0              0.000022               0.000777                    1.315298 ...         0.131575          0.001592                           0.0                       0.000000                          0.0                           0.0               0.044115              0.021921   -1.389897e-09     12726.421469
        16  1997-10-17              0.074166               2.947561           0.950310                 0.0                    0.0                     0.0              0.000020               0.000770                    1.318054 ...         0.131835          0.001773                           0.0                       0.000000                          0.0                           0.0               0.044025              0.022027   -6.493825e-09     12729.294864
        17  1997-10-18              0.068129               2.932866           0.938721                 0.0                    0.0                     0.0              0.000019               0.000766                    1.321243 ...         0.131910          0.002013                           0.0                       0.000000                          0.0                           0.0               0.043935              0.022141   -6.458619e-09     12732.159601
        18  1997-10-19              0.063871               2.928707           0.932968                 0.0                    0.0                     0.0              0.000018               0.000764                    1.327390 ...         0.131989          0.002284                           0.0                       0.000000                          0.0                           0.0               0.043845              0.022259   -6.450796e-09     12735.024437
        19  1997-10-20              0.061503               2.930320           0.930234                 0.0                    0.0                     0.0              0.000017               0.000765                    1.334442 ...         0.132041          0.002569                           0.0                       0.000000                          0.0                           0.0               0.043754              0.022378   -6.445811e-09     12737.893254
        20  1997-10-21              0.058493               2.932425           0.928972                 0.0                    0.0                     0.0              0.000016               0.000766                    1.341225 ...         0.132034          0.002862                           0.0                       0.000000                          0.0                           0.0               0.043663              0.022497   -6.442677e-09     12740.767185
        21  1997-10-22              0.056101               2.933823           0.928477                 0.0                    0.0                     0.0              0.000015               0.000766                    1.345979 ...         0.131970          0.003159                           0.0                       0.000000                          0.0                           0.0               0.043573              0.022617   -6.438571e-09     12743.644907
        22  1997-10-23              0.054233               2.934300           0.928376                 0.0                    0.0                     0.0              0.000015               0.000767                    1.348934 ...         0.131871          0.003459                           0.0                       0.000000                          0.0                           0.0               0.043482              0.022738   -6.433619e-09     12746.524974
        23  1997-10-24              0.052717               2.933964           0.928475                 0.0                    0.0                     0.0              0.000015               0.000767                    1.350545 ...         0.131752          0.003760                           0.0                       0.000000                          0.0                           0.0               0.043391              0.022858   -6.426365e-09     12749.406221
        24  1997-10-25              0.051644               2.933234           0.928675                 0.0                    0.0                     0.0              0.000014               0.000767                    1.351228 ...         0.131625          0.004063                           0.0                       0.000000                          0.0                           0.0               0.043301              0.022978   -6.411061e-09     12752.287811
        25  1997-10-26              0.050762               2.932130           0.928925                 0.0                    0.0                     0.0              0.000014               0.000767                    1.351302 ...         0.131493          0.004366                           0.0                       0.000000                          0.0                           0.0               0.043210              0.023098   -6.363688e-09     12755.169179
        26  1997-10-27              0.049930               2.930711           0.929200                 0.0                    0.0                     0.0              0.000014               0.000767                    1.350987 ...         0.131361          0.004669                           0.0                       0.000000                          0.0                           0.0               0.043120              0.023218   -5.935102e-09     12758.049960
        27  1997-10-28              0.049131               2.927025           0.927415                 0.0                    0.0                     0.0              0.000014               0.000766                    1.350433 ...         0.131227          0.004973                           0.0                       0.000000                          0.0                           0.0               0.043030              0.023338   -9.135705e-09     12760.927854
        28  1997-10-29              0.048360               2.913890           0.916573                 0.0                    0.0                     0.0              0.000013               0.000762                    1.349457 ...         0.131094          0.005276                           0.0                       0.000000                          0.0                           0.0               0.042940              0.023457   -6.602659e-09     12763.793384
        29  1997-10-30              0.048777               2.892041           0.899888                 0.0                    0.0                     0.0              0.000013               0.000756                    1.344420 ...         0.130960          0.005580                           0.0                       0.000000                          0.0                           0.0               0.042849              0.023576   -1.509239e-08     12766.636648
        30  1997-10-31              0.049344               2.846310           0.866150                 0.0                    0.0                     0.0              0.000014               0.000742                    1.332396 ...         0.130828          0.005885                           0.0                       0.000000                          0.0                           0.0               0.042759              0.023694   -6.460522e-09     12769.433613
        >>> gw_zbud.close_zbudget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_ZBudget_GetValues_ForAZone"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_ZBudget_GetValues_ForAZone")
            )

        # check zone_id is an integer
        if not isinstance(zone_id, int):
            raise TypeError("zone_id must be an integer")

        # get possible zones numbers
        zones = self.get_zone_list()

        # check that zone_id is a valid zone ID
        if zone_id not in zones:
            raise ValueError("zone_id was not found in zone definitions provided")

        # get all column headers and column IDs
        column_headers, column_header_ids = self.get_column_headers_for_a_zone(
            zone_id, area_unit=area_units, volume_unit=volume_units, include_time=True
        )

        if isinstance(column_ids, str) and column_ids == "all":
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
            raise ValueError("one or more column_ids provided are not valid")

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
        column_ids = (ctypes.c_int * n_column_ids.value)(*column_ids)

        # handle start and end dates
        # get time specs
        dates_list, sim_output_interval = self.get_time_specs()

        if begin_date is None:
            begin_date = dates_list[0]
        else:
            self._validate_iwfm_date(begin_date)

            if begin_date not in dates_list:
                raise ValueError(
                    "begin_date was not found in the ZBudget "
                    "file. use get_time_specs() method to check."
                )

        if end_date is None:
            end_date = dates_list[-1]
        else:
            self._validate_iwfm_date(end_date)

            if end_date not in dates_list:
                raise ValueError(
                    "end_date was not found in the ZBudget "
                    "file. use get_time_specs() method to check."
                )

        if self.is_date_greater(begin_date, end_date):
            raise ValueError("end_date must occur after begin_date")

        if output_interval is None:
            output_interval = sim_output_interval

        # get number of timestep intervals
        n_timestep_intervals = ctypes.c_int(
            self.get_n_intervals(
                begin_date, end_date, output_interval, includes_end_date=True
            )
        )

        # convert beginning and end dates to ctypes
        begin_date = ctypes.create_string_buffer(begin_date.encode("utf-8"))
        end_date = ctypes.create_string_buffer(end_date.encode("utf-8"))

        length_date_string = ctypes.c_int(ctypes.sizeof(begin_date))

        # check output interval is greater than or equal to simulation
        if not self._is_time_interval_greater_or_equal(
            output_interval, sim_output_interval
        ):
            raise ValueError(
                "output_interval must be greater than or "
                "equal to the simulation time step"
            )

        # convert output_interval to ctypes
        output_interval = ctypes.create_string_buffer(output_interval.encode("utf-8"))
        length_output_interval = ctypes.c_int(ctypes.sizeof(output_interval))

        # convert unit conversion factors to ctypes
        area_conversion_factor = ctypes.c_double(area_conversion_factor)
        volume_conversion_factor = ctypes.c_double(volume_conversion_factor)

        # initialize output variables
        zbudget_values = (
            (ctypes.c_double * n_column_ids.value) * n_timestep_intervals.value
        )()
        n_times_out = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_ZBudget_GetValues_ForAZone(
            ctypes.byref(zone_id),
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
            ctypes.byref(status),
        )

        values = np.array(zbudget_values)

        zbudget = pd.DataFrame(data=values, columns=columns)
        zbudget["Time"] = zbudget["Time"].astype("timedelta64[D]") + np.array(
            "1899-12-30", dtype="datetime64"
        )

        return zbudget
