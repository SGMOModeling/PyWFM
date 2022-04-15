import os
import ctypes
import numpy as np
import pandas as pd

from pywfm import DLL_PATH, DLL

from pywfm.misc import IWFMMiscellaneous


class IWFMBudget(IWFMMiscellaneous):
    """
    IWFM Budget Class for interacting with the IWFM API

    Parameters
    ----------
    budget_file_name : str
        File path and name of the budget file.

    Returns
    -------
    IWFMBudget Object
        instance of the IWFMBudget class and access to the IWFM Budget
        fortran procedures.
    """

    def __init__(self, budget_file_name):

        if not isinstance(budget_file_name, str):
            raise TypeError("budget_file_name must be a string")

        if not os.path.exists(budget_file_name):
            raise FileNotFoundError("{} was not found".format(budget_file_name))

        self.budget_file_name = budget_file_name

        self.dll = ctypes.windll.LoadLibrary(os.path.join(DLL_PATH, DLL))

        # check to see if the open file procedure exists in the dll provided
        if not hasattr(self.dll, "IW_Budget_OpenFile"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_Budget_OpenFile")
            )

        # set input variables name and name length
        budget_file = ctypes.create_string_buffer(self.budget_file_name.encode("utf-8"))
        length_file_name = ctypes.c_int(ctypes.sizeof(budget_file))

        # initialize output variable status
        status = ctypes.c_int(-1)

        self.dll.IW_Budget_OpenFile(
            budget_file, ctypes.byref(length_file_name), ctypes.byref(status)
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_budget_file()

    def close_budget_file(self):
        """
        Close an open budget file for an IWFM model application
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_Budget_CloseFile"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_Budget_CloseFile")
            )

        # initialize output variable status
        status = ctypes.c_int(0)

        self.dll.IW_Budget_CloseFile(ctypes.byref(status))

    def get_n_locations(self):
        """
        Return the number of locations where budget data is available.

        Returns
        -------
        int
            Number of locations.

        Note
        ----
        e.g. if the budget file used is the stream reach budget, the
        number of locations is the number of stream reaches.

        e.g. if the budget file used is the groundwater budget, the
        number of locations is the number of subregions plus one
        (for the entire model area).

        Example
        -------
        >>> from pywfm import IWFMBudget
        >>> bud_file = '../Results/GW.hdf'
        >>> gw_bud = IWFMBudget(bud_file)
        >>> gw_bud.get_n_locations()
        3
        >>> gw_bud.close_budget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_Budget_GetNLocations"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_Budget_GetNLocations")
            )

        # initialize output variables
        n_locations = ctypes.c_int(0)
        status = ctypes.c_int(0)

        self.dll.IW_Budget_GetNLocations(
            ctypes.byref(n_locations), ctypes.byref(status)
        )

        return n_locations.value

    def get_location_names(self):
        """
        Retrieve the location names e.g. subregion names, lake names,
        etc. from the open budget file.

        Returns
        -------
        list
            Names for each location.

        Example
        -------
        >>> from pywfm import IWFMBudget
        >>> bud_file = '../Results/GW.hdf'
        >>> gw_bud = IWFMBudget(bud_file)
        >>> gw_bud.get_location_names()
        ['Region1 (SR1)', 'Region2 (SR2)', 'ENTIRE MODEL AREA']
        >>> gw_bud.close_budget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_Budget_GetLocationNames"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_Budget_GetLocationNames")
            )

        # get number of locations
        n_locations = ctypes.c_int(self.get_n_locations())

        # set length of location names string to 30 times the number of
        #  locations per IWFM DLL programmers guide
        location_names_length = ctypes.c_int(30 * n_locations.value)
        raw_names_string = ctypes.create_string_buffer(location_names_length.value)
        delimiter_position_array = (ctypes.c_int * location_names_length.value)()

        status = ctypes.c_int(0)

        # IW_Budget_GetLocationNames(cLocNames,iLenLocNames,NLocations,iLocArray,iStat)
        self.dll.IW_Budget_GetLocationNames(
            raw_names_string,
            ctypes.byref(location_names_length),
            ctypes.byref(n_locations),
            delimiter_position_array,
            ctypes.byref(status),
        )

        return self._string_to_list_by_array(
            raw_names_string, delimiter_position_array, n_locations
        )

    def get_n_time_steps(self):
        """
        Return the number of time steps where budget data is available.

        Returns
        -------
        int
            Number of time steps.

        Example
        -------
        >>> from pywfm import IWFMBudget
        >>> bud_file = '../Results/GW.hdf'
        >>> gw_bud = IWFMBudget(bud_file)
        >>> gw_bud.get_n_time_steps()
        3653
        >>> gw_bud.close_budget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_Budget_GetNTimeSteps"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_Budget_GetNTimeSteps")
            )

        n_time_steps = ctypes.c_int(0)
        status = ctypes.c_int(0)

        # IW_Budget_GetNTimeSteps(NTimeSteps,iStat)
        self.dll.IW_Budget_GetNTimeSteps(
            ctypes.byref(n_time_steps), ctypes.byref(status)
        )

        return n_time_steps.value

    def get_time_specs(self):
        """
        Return a list of all the time stamps and the time interval for
        the budget.

        Returns
        -------
        dates_list : list
            List of time stamps in the budget.
        interval : str
            Time interval for the time stamps.

        Example
        -------
        >>> from pywfm import IWFMBudget
        >>> bud_file = '../Results/GW.hdf'
        >>> gw_bud = IWFMBudget(bud_file)
        >>> dates, output_interval = gw_bud.get_time_specs()
        >>> dates
        ['10/01/1990_24:00',
         '10/02/1990_24:00',
         '10/03/1990_24:00',
         '10/04/1990_24:00',
         ...
         '07/18/1992_24:00',
         '07/19/1992_24:00',
         '07/20/1992_24:00',
         '07/21/1992_24:00',
         ...]
        >>> output_interval
        '1DAY'
        >>> gw_bud.close_budget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_Budget_GetTimeSpecs"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_Budget_GetTimeSpecs")
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

        # IW_Budget_GetTimeSpecs(cDataDatesAndTimes,iLenDates,cInterval,iLenInterval,NData,iLocArray,iStat)
        self.dll.IW_Budget_GetTimeSpecs(
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

    def get_n_title_lines(self):
        """
        Return the number of title lines for a water budget of a
        location.

        Returns
        -------
        int
            Number of title lines.

        Example
        -------
        >>> from pywfm import IWFMBudget
        >>> bud_file = '../Results/GW.hdf'
        >>> gw_bud = IWFMBudget(bud_file)
        >>> gw_bud.get_n_title_lines()
        3
        >>> gw_bud.close_budget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_Budget_GetNTitleLines"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_Budget_GetNTitleLines")
            )

        # initialize output variables
        n_title_lines = ctypes.c_int(0)
        status = ctypes.c_int(0)

        # IW_Budget_GetNTitleLines(NTitles,iStat)
        self.dll.IW_Budget_GetNTitleLines(
            ctypes.byref(n_title_lines), ctypes.byref(status)
        )

        return n_title_lines.value

    def get_title_length(self):
        """
        Retrieve the length of the title lines.

        Returns
        -------
        int
            Number of characters that make up the title lines.

        Example
        -------
        >>> from pywfm import IWFMBudget
        >>> bud_file = '../Results/GW.hdf'
        >>> gw_bud = IWFMBudget(bud_file)
        >>> gw_bud.get_title_length()
        242
        >>> gw_bud.close_budget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_Budget_GetTitleLength"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_Budget_GetTitleLength")
            )

        # initialize output variables
        title_length = ctypes.c_int(0)
        status = ctypes.c_int(0)

        # IW_Budget_GetTitleLength(iLen,iStat)
        self.dll.IW_Budget_GetTitleLength(
            ctypes.byref(title_length), ctypes.byref(status)
        )

        return title_length.value

    def get_title_lines(
        self,
        location_id,
        area_conversion_factor=1.0,
        length_units="FT",
        area_units="SQ FT",
        volume_units="CU FT",
        alternate_location_name=None,
    ):
        """
        Return the title lines for the budget data.

        Parameters
        ----------
        location_id : int
            ID for location (1 to number of locations)

        area_conversion_factor : float, default=1.0
            Factor to convert budget file area units to user desired
            output area units.

            Note
            ----
            Only the area shows up in the title lines.

        length_units : str, default='FT'
            Units of length used in the budget results.

        area_units : str, default='SQ FT'
            Units of area used in the budget results.

        volume_units : str, default='CU FT'
            Units of volume used in the budget results.

        alternate_location_name : str, optional
            Alternate name for location given by the location_id.

        Returns
        -------
        list
            Titles generated for the Budget.

        Note
        ----
        Conversion from model area units of SQ FT to Acres is 2.29568E-05.

        Example
        -------
        >>> from pywfm import IWFMBudget
        >>> bud_file = '../Results/GW.hdf'
        >>> gw_bud = IWFMBudget(bud_file)
        >>> gw_bud.get_title_lines(1)
        ['IWFM (v2015.0.1273)',
         'GROUNDWATER BUDGET IN cu ft FOR Region1 (SR1)',
         'SUBREGION AREA: 8610918912.00 sq ft']
        >>> gw_bud.close_budget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_Budget_GetTitleLines"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_Budget_GetTitleLines")
            )

        # get the number of title lines
        n_title_lines = ctypes.c_int(self.get_n_title_lines())

        # get number of locations
        n_locations = self.get_n_locations()

        # check that location_id is a number between 1 and n_locations
        if location_id not in [i + 1 for i in range(n_locations)]:
            raise ValueError(
                "location_id is not valid. Must be a value between 1 and {}.".format(
                    n_locations
                )
            )

        # convert the location_id to ctypes
        location_id = ctypes.c_int(location_id)

        # set length of the units string to the maximum of the length, area, and volume units
        units_length = ctypes.c_int(
            max(len(length_units), len(area_units), len(volume_units))
        )

        # convert units to ctypes strings
        length_units = ctypes.create_string_buffer(length_units.encode("utf-8"))
        area_units = ctypes.create_string_buffer(area_units.encode("utf-8"))
        volume_units = ctypes.create_string_buffer(volume_units.encode("utf-8"))

        # convert area conversion factor to ctypes
        area_conversion_factor = ctypes.c_double(area_conversion_factor)

        # get title length
        title_length = ctypes.c_int(self.get_title_length())

        # handle alternate location name
        if alternate_location_name is None:
            alternate_location_name = ctypes.create_string_buffer("".encode("utf-8"))
        else:
            alternate_location_name = ctypes.create_string_buffer(
                alternate_location_name.encode("utf-8")
            )

        length_alternate_location_name = ctypes.c_int(
            ctypes.sizeof(alternate_location_name)
        )

        # compute total length of all lines of the title
        length_titles = ctypes.c_int(title_length.value * n_title_lines.value)

        # initialize output variables
        raw_title_string = ctypes.create_string_buffer(length_titles.value)
        delimiter_position_array = (ctypes.c_int * n_title_lines.value)()

        # set variable status to 0
        status = ctypes.c_int(0)

        self.dll.IW_Budget_GetTitleLines(
            ctypes.byref(n_title_lines),
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
            ctypes.byref(status),
        )

        return self._string_to_list_by_array(
            raw_title_string, delimiter_position_array, n_title_lines
        )

    def get_n_columns(self, location_id):
        """
        Retrieve the number of budget data columns for a specified
        location.

        Parameters
        ----------
        location_id : int
            Location identification number e.g. subregion number, lake
            number, stream reach number where budget data is being
            retrieved.

        Returns
        -------
        int
            Number of budget data columns.

        Example
        -------
        >>> from pywfm import IWFMBudget
        >>> bud_file = '../Results/GW.hdf'
        >>> gw_bud = IWFMBudget(bud_file)
        >>> gw_bud.get_n_columns()
        17
        >>> gw_bud.close_budget_file()
        """
        # check to see if the procedure exists in the dll provided
        if not hasattr(self.dll, "IW_Budget_GetNColumns"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_Budget_GetNColumns")
            )

        # get number of locations
        n_locations = self.get_n_locations()

        # check that location_id is a number between 1 and n_locations
        if location_id not in [i + 1 for i in range(n_locations)]:
            raise ValueError(
                "location_id is not valid. Must be a value between 1 and {}.".format(
                    n_locations
                )
            )

        # convert location_id to ctypes
        location_id = ctypes.c_int(location_id)

        # initialize output variables
        n_columns = ctypes.c_int(0)
        status = ctypes.c_int(0)

        # IW_Budget_GetNColumns(iLoc,NColumns,iStat)
        self.dll.IW_Budget_GetNColumns(
            ctypes.byref(location_id), ctypes.byref(n_columns), ctypes.byref(status)
        )

        return n_columns.value

    def get_column_headers(
        self, location_id, length_unit="FT", area_unit="SQ FT", volume_unit="CU FT"
    ):
        """
        Return the column headers for a budget location.

        Parameters
        ----------
        location_id : int
            Location identification number for budget
            e.g. subregion id, stream reach id, etc.

        length_unit : str, default 'FT'
            Unit of length used in column headers if one is used.

        area_unit : str, default 'SQ FT'
            Unit of area used in column headers if one is used.

        volume_unit : str, default 'CU FT'
            Unit of volume used in column headers if one is used.

        Returns
        -------
        list
            List of column headers for the budget type.

        Example
        -------
        >>> from pywfm import IWFMBudget
        >>> bud_file = '../Results/GW.hdf'
        >>> gw_bud = IWFMBudget(bud_file)
        >>> gw_bud.get_column_headers()
        ['Time',
         'Percolation',
         'Beginning Storage (+)',
         'Ending Storage (-)',
         'Deep Percolation (+)',
         'Gain from Stream (+)',
         'Recharge (+)',
         'Gain from Lake (+)',
         'Boundary Inflow (+)',
         'Subsidence (+)',
         'Subsurface Irrigation (+)',
         'Tile Drain Outflow (-)',
         'Pumping (-)',
         'Outflow to Root Zone (-)',
         'Net Subsurface Inflow (+)',
         'Discrepancy (=)',
         'Cumulative Subsidence']
        >>> gw_bud.close_budget_file()
        """
        if not hasattr(self.dll, "IW_Budget_GetColumnHeaders"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_Budget_GetColumnHeaders")
            )

        # get number of locations
        n_locations = self.get_n_locations()

        # check that location_id is a number between 1 and n_locations
        if location_id not in [i + 1 for i in range(n_locations)]:
            raise ValueError(
                "location_id is not valid. Must be a value between 1 and {}.".format(
                    n_locations
                )
            )

        # get the number of columns
        n_columns = ctypes.c_int(self.get_n_columns(location_id))

        # convert location_id to ctypes
        location_id = ctypes.c_int(location_id)

        # set length of the column headers array to 30 times
        length_column_headers = ctypes.c_int(30 * n_columns.value)

        # get max length of the units
        units_length = ctypes.c_int(
            max(len(length_unit), len(area_unit), len(volume_unit))
        )

        # convert units to ctypes
        length_unit = ctypes.create_string_buffer(length_unit.encode("utf-8"))
        area_unit = ctypes.create_string_buffer(area_unit.encode("utf-8"))
        volume_unit = ctypes.create_string_buffer(volume_unit.encode("utf-8"))

        # initialize output variables
        raw_column_headers = ctypes.create_string_buffer(length_column_headers.value)
        delimiter_position_array = (ctypes.c_int * n_columns.value)()

        # set variable status to 0
        status = ctypes.c_int(0)

        self.dll.IW_Budget_GetColumnHeaders(
            ctypes.byref(location_id),
            raw_column_headers,
            ctypes.byref(length_column_headers),
            ctypes.byref(n_columns),
            length_unit,
            area_unit,
            volume_unit,
            ctypes.byref(units_length),
            delimiter_position_array,
            ctypes.byref(status),
        )

        return self._string_to_list_by_array(
            raw_column_headers, delimiter_position_array, n_columns
        )

    def get_values(
        self,
        location_id,
        columns="all",
        begin_date=None,
        end_date=None,
        output_interval=None,
        length_conversion_factor=1.0,
        length_units="FT",
        area_conversion_factor=1.0,
        area_units="SQ FT",
        volume_conversion_factor=1.0,
        volume_units="CU FT",
    ):
        """
        Return budget data for selected budget columns for a location and specified time interval.

        Parameters
        ----------
        location_id : int
            Location identification number for budget e.g. subregion id,
            stream reach id, etc.

        columns : str or list of str, default='all'
            Column names to obtain budget data.

        begin_date : str
            First date where budget data are returned.

        end_date : str
            Last date where budget data are returned.

        output_interval : str or None, default None
            Valid IWFM output time interval for returning budget data.

            Note
            ----
            This must be greater than or equal to the simulation time
            step.

        length_conversion_factor : float, default 1.0
            Conversion factor to convert simulation units for length
            to another length.

        length_units : str, default 'FT'
            output units of length

        area_conversion_factor : float, default 1.0
            Conversion factor to convert simulation units for area.

        area_units : str, default 'SQ FT'
            output units of area

        volume_conversion_factor : float, default 1.0
            Conversion factor to convert simulation units for volume.

        volume_units : str, default 'CU FT'
            output units of volume

        Returns
        -------
        pd.DataFrame
            DataFrame containing budget data for one or more columns.

        See Also
        --------
        IWFMBudget.get_values_for_a_column : Return the budget data for
            a single column and location for specified beginning and
            ending dates.

        Example
        -------
        >>> from pywfm import IWFMBudget
        >>> bud_file = '../Results/GW.hdf'
        >>> gw_bud = IWFMBudget(bud_file)
        >>> gw_bud.get_values(1, ['Percolation', 'Pumping (-)'], '10/31/1999_24:00', '09/30/2000_24:00')
                     Time     Percolation     Pumping (-)
          0    1999-10-31    5.409162e+06    0.000000e+00
          1    1999-11-01    5.591003e+06    0.000000e+00
          2    1999-11-02    5.774809e+06    0.000000e+00
          3    1999-11-03    5.961015e+06    0.000000e+00
          4    1999-11-04    6.161024e+06    0.000000e+00
        ...    ...    ...    ...
        331    2000-09-26    8.134227e+05    1.905547e+07
        332    2000-09-27    8.144577e+05    1.892258e+07
        333    2000-09-28    8.153966e+05    1.879084e+07
        334    2000-09-29    8.162175e+05    1.879133e+07
        335    2000-09-30    8.168388e+05    1.879282e+07
        >>> gw_bud.close_budget_file()
        """
        if not hasattr(self.dll, "IW_Budget_GetValues"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_Budget_GetValues")
            )

        # get number of locations
        n_locations = self.get_n_locations()

        # check that location_id is a number between 1 and n_locations
        if location_id not in [i + 1 for i in range(n_locations)]:
            raise ValueError(
                "location_id is not valid. "
                "Must be a value between 1 and {}.".format(n_locations)
            )

        # convert location_id to ctypes
        location_id = ctypes.c_int(location_id)

        # get column headers
        column_headers = self.get_column_headers(
            location_id.value, length_units, area_units, volume_units
        )

        # handle columns as a list
        if isinstance(columns, str):
            if columns == "all":
                columns = column_headers[1:]

            else:
                columns = [columns]

        # if columns provided as a str, it should now be a list
        if not isinstance(columns, list):
            raise TypeError("columns must be a list or str")

        # check that all column names provided exist if so create list of column numbers
        column_numbers = []
        for val in columns:
            if val not in column_headers:
                raise ValueError(
                    "columns provided must be one of the "
                    "following:\n {}".format(", ".join(column_headers))
                )
            else:
                column_numbers.append(column_headers.index(val))

        # convert column numbers to ctypes
        n_columns = ctypes.c_int(len(column_numbers))
        column_numbers = (ctypes.c_int * n_columns.value)(*column_numbers)

        # handle start and end dates
        # get time specs
        dates_list, sim_output_interval = self.get_time_specs()

        if begin_date is None:
            begin_date = dates_list[0]
        else:
            self._validate_iwfm_date(begin_date)

            if begin_date not in dates_list:
                raise ValueError(
                    "begin_date was not found in the Budget "
                    "file. use get_time_specs() method to check."
                )

        if end_date is None:
            end_date = dates_list[-1]
        else:
            self._validate_iwfm_date(end_date)

            if end_date not in dates_list:
                raise ValueError(
                    "end_date was not found in the Budget "
                    "file. use get_time_specs() method to check."
                )

        if self.is_date_greater(begin_date, end_date):
            raise ValueError("end_date must occur after begin_date")

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

        # get number of timestep intervals
        n_timestep_intervals = ctypes.c_int(
            self.get_n_intervals(
                begin_date, end_date, output_interval, includes_end_date=True
            )
        )

        # convert output_interval to ctypes
        output_interval = ctypes.create_string_buffer(output_interval.encode("utf-8"))
        length_output_interval = ctypes.c_int(ctypes.sizeof(output_interval))

        # convert beginning and end dates to ctypes
        begin_date = ctypes.create_string_buffer(begin_date.encode("utf-8"))
        end_date = ctypes.create_string_buffer(end_date.encode("utf-8"))

        length_date = ctypes.c_int(ctypes.sizeof(begin_date))

        # convert unit conversion factors to ctypes
        length_conversion_factor = ctypes.c_double(length_conversion_factor)
        area_conversion_factor = ctypes.c_double(area_conversion_factor)
        volume_conversion_factor = ctypes.c_double(volume_conversion_factor)

        # initialize output variables
        budget_values = (
            (ctypes.c_double * (n_columns.value + 1)) * n_timestep_intervals.value
        )()
        n_output_intervals = ctypes.c_int(0)

        # set status to 0
        status = ctypes.c_int(0)

        # IW_Budget_GetValues(iLoc,nReadCols,iReadCols,cDateAndTimeBegin,cDateAndTimeEnd,iLenDateAndTime,
        #                     cOutputInterval,iLenInterval,rFact_LT,rFact_AR,rFact_VL,nTimes_In,Values,nTimes_Out,iStat)
        self.dll.IW_Budget_GetValues(
            ctypes.byref(location_id),
            ctypes.byref(n_columns),
            column_numbers,
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
            ctypes.byref(status),
        )

        budget = pd.DataFrame(data=np.array(budget_values), columns=["Time"] + columns)
        budget["Time"] = budget["Time"].astype("timedelta64[D]") + np.array(
            "1899-12-30", dtype="datetime64"
        )

        return budget

    def get_values_for_a_column(
        self,
        location_id,
        column_name,
        begin_date=None,
        end_date=None,
        output_interval=None,
        length_conversion_factor=1.0,
        length_units="FT",
        area_conversion_factor=1.0,
        area_units="SQ FT",
        volume_conversion_factor=1.0,
        volume_units="CU FT",
    ):
        """
        Return the budget data for a single column and location for a specified
        beginning and ending dates.

        Parameters
        ----------
        location_id : int
            Location_id where the budget data is returned.

        column_name : str
            Name of the budget column to return.

        begin_date : str or None, default=None
            First date for budget values.

        end_date : str or None, default=None
            Last date for budget values.

        output_interval : str or None, default=None
            Valid IWFM output time interval for returning budget data.

            Note
            ----
            This must be greater than or equal to the simulation time
            step.

        length_conversion_factor : float, default 1.0
            Unit conversion factor for length units used in the model
            to some other length unit.

        length_units : str, default 'FT'
            output units of length

        area_conversion_factor : float, default 1.0
            Conversion factor to convert simulation units for area.

        area_units : str, default 'SQ FT'
            output units of area

        volume_conversion_factor : float, default 1.0
            Conversion factor to convert simulation units for volume.

        volume_units : str, default 'CU FT'
            output units of volume

        Returns
        -------
        pd.DataFrame
            DataFrame representing dates and values.

        See Also
        --------
        IWFMBudget.get_values : Return budget data for selected budget
            columns for a location and specified time interval.

        Example
        -------
        >>> from pywfm import IWFMBudget
        >>> bud_file = '../Results/GW.hdf'
        >>> gw_bud = IWFMBudget(bud_file)
        >>> gw_bud.get_values_for_a_column(1, 'Pumping (-)')
                      Time     Pumping (-)
           0    1990-10-01    0.000000e+00
           1    1990-10-02    0.000000e+00
           2    1990-10-03    0.000000e+00
           3    1990-10-04    0.000000e+00
           4    1990-10-05    0.000000e+00
         ...           ...             ...
        3648    2000-09-26    1.905547e+07
        3649    2000-09-27    1.892258e+07
        3650    2000-09-28    1.879084e+07
        3651    2000-09-29    1.879133e+07
        3652    2000-09-30    1.879282e+07
        >>> gw_bud.close_budget_file()
        """
        if not hasattr(self.dll, "IW_Budget_GetValues_ForAColumn"):
            raise AttributeError(
                'IWFM API does not have "{}" procedure. '
                "Check for an updated version".format("IW_Budget_GetValues_ForAColumn")
            )

        # get number of locations
        n_locations = self.get_n_locations()

        # check that location_id is a number between 1 and n_locations
        if location_id not in [i + 1 for i in range(n_locations)]:
            raise ValueError(
                "location_id is not valid. Must be a value "
                "between 1 and {}.".format(n_locations)
            )

        # convert location_id to ctypes
        location_id = ctypes.c_int(location_id)

        # get column_headers
        column_headers = self.get_column_headers(
            location_id.value, length_units, area_units, volume_units
        )

        # check that column name provided exists. if so, get column index.
        if column_name not in column_headers:
            raise ValueError(
                "column_name provided must be one of the "
                "following:\n {}".format(", ".join(column_headers))
            )

        column_id = ctypes.c_int(column_headers.index(column_name))

        # handle start and end dates
        # get time specs
        dates_list, sim_output_interval = self.get_time_specs()

        if begin_date is None:
            begin_date = dates_list[0]
        else:
            self._validate_iwfm_date(begin_date)

            if begin_date not in dates_list:
                raise ValueError(
                    "begin_date was not found in the Budget file. use get_time_specs() method to check."
                )

        if end_date is None:
            end_date = dates_list[-1]
        else:
            self._validate_iwfm_date(end_date)

            if end_date not in dates_list:
                raise ValueError(
                    "end_date was not found in the Budget file. use get_time_specs() method to check."
                )

        if self.is_date_greater(begin_date, end_date):
            raise ValueError("end_date must occur after begin_date")

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

        # get number of timestep intervals
        n_timestep_intervals = ctypes.c_int(
            self.get_n_intervals(
                begin_date, end_date, output_interval, includes_end_date=True
            )
        )

        # convert output_interval to ctypes
        output_interval = ctypes.create_string_buffer(output_interval.encode("utf-8"))
        length_output_interval = ctypes.c_int(ctypes.sizeof(output_interval))

        # convert beginning and end dates to ctypes
        begin_date = ctypes.create_string_buffer(begin_date.encode("utf-8"))
        end_date = ctypes.create_string_buffer(end_date.encode("utf-8"))

        length_date = ctypes.c_int(ctypes.sizeof(begin_date))

        # convert unit conversion factors to ctypes
        length_conversion_factor = ctypes.c_double(length_conversion_factor)
        area_conversion_factor = ctypes.c_double(area_conversion_factor)
        volume_conversion_factor = ctypes.c_double(volume_conversion_factor)

        # initialize output variables
        n_output_intervals = ctypes.c_int(0)
        dates = (ctypes.c_double * n_timestep_intervals.value)()
        values = (ctypes.c_double * n_timestep_intervals.value)()

        # set status to 0
        status = ctypes.c_int(0)

        self.dll.IW_Budget_GetValues_ForAColumn(
            ctypes.byref(location_id),
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
            ctypes.byref(status),
        )

        dates = np.array("1899-12-30", dtype="datetime64") + np.array(
            dates, dtype="timedelta64"
        )
        values = np.array(values)

        return pd.DataFrame({"Time": dates, column_name: values})
