"""Budget and zone budget data read through an IWFMModel.

These wrap the IW_Model_GetBudget_* and IW_Model_GetZBudget_* procedures.
Unlike IWFMBudget and IWFMZBudget, which open one budget file, they reach
every budget and zone budget the model writes, by budget type and location.
They work for simulation and inquiry models; the budget files must exist.

Budget types come from ``get_budget_type_ids()`` (zone budgets:
``get_zbudget_type_ids()``); locations are 1-based indices, e.g. the
subregion number for a groundwater budget.

The procedures copy results into caller-sized arrays without checking
their sizes, so the array sizes here are deliberately generous.
"""
import ctypes

import numpy as np
import pandas as pd

from pywfm.exceptions import IWFMError


# Months of the water year, the order the monthly-average procedures use
WATER_YEAR_MONTHS = ["OCT", "NOV", "DEC", "JAN", "FEB", "MAR",
                     "APR", "MAY", "JUN", "JUL", "AUG", "SEP"]

# Excel-style serial date 0, which the procedures return dates relative to
_EXCEL_EPOCH = np.array("1899-12-30", dtype="datetime64[D]")


def _cstr(text):
    """A ctypes string buffer and its length, as the procedures expect."""
    buf = ctypes.create_string_buffer(text.encode("utf-8"))
    return buf, ctypes.c_int(ctypes.sizeof(buf))


def _excel_dates(values):
    """Excel-style serial dates (days since 1899-12-30) to datetime64."""
    days = np.asarray(values, dtype=float)
    return _EXCEL_EPOCH + np.round(days * 1440).astype("timedelta64[m]")


def _int_array(values):
    values = [int(v) for v in values]
    return (ctypes.c_int * max(len(values), 1))(*values), ctypes.c_int(len(values))


class ModelBudgetMixin:
    """IW_Model_GetBudget_* and IW_Model_GetZBudget_* wrappers for IWFMModel."""

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _require(self, name):
        if not hasattr(self.dll, name):
            raise AttributeError(
                f'IWFM API does not have "{name}" procedure. '
                "Check for an updated version"
            )

    def _date_range(self, begin_date, end_date):
        """Default to the simulation period."""
        if begin_date is None or end_date is None:
            time_stamps, _ = self.get_time_specs()
            begin_date = begin_date or time_stamps[0]
            end_date = end_date or time_stamps[-1]
        self._validate_iwfm_date(begin_date)
        self._validate_iwfm_date(end_date)
        if self.is_date_greater(begin_date, end_date):
            raise ValueError("end_date must occur after begin_date")
        return begin_date, end_date

    def _n_output_times(self, begin_date, end_date, interval):
        return self.get_n_intervals(begin_date, end_date, interval, includes_end_date=True) + 1

    @staticmethod
    def _n_years(begin_date, end_date):
        return int(end_date[6:10]) - int(begin_date[6:10]) + 2

    def _zone_arrays(self, zone_extent, elements, layers, zone_ids):
        """Zone definition: one (element, layer, zone ID) triple per entry."""
        if not len(elements) == len(layers) == len(zone_ids):
            raise ValueError("elements, layers and zone_ids must have the same length")
        if zone_extent == "horizontal":
            extent = self.get_zone_extent_id_horizontal()
        elif zone_extent == "vertical":
            extent = self.get_zone_extent_id_vertical()
        else:
            raise ValueError("zone_extent must be 'horizontal' or 'vertical'")
        elems, n = _int_array(elements)
        lays, _ = _int_array(layers)
        zones, _ = _int_array(zone_ids)
        return ctypes.c_int(extent), n, elems, lays, zones

    def _names(self, raw, positions, n):
        return [s.strip() for s in self._string_to_list_by_array(raw, positions, n)]

    # ------------------------------------------------------------------
    # budgets
    # ------------------------------------------------------------------
    def get_n_budgets(self):
        """Return the number of budgets the model writes."""
        self._require("IW_Model_GetBudget_N")
        n = ctypes.c_int(0)
        status = ctypes.c_int(0)
        self._call("IW_Model_GetBudget_N", ctypes.byref(n), ctypes.byref(status))
        self._raise_on_error(status)
        return n.value

    def get_budget_list(self):
        """Return the model's budgets.

        Returns
        -------
        pd.DataFrame
            one row per budget: ``name``, ``budget_type_id`` (see
            ``get_budget_type_ids()``) and ``location_type_id`` (see
            ``get_location_type_ids()``)
        """
        self._require("IW_Model_GetBudget_List")
        n_budgets = self.get_n_budgets()
        if n_budgets == 0:
            return pd.DataFrame(columns=["name", "budget_type_id", "location_type_id"])
        n = ctypes.c_int(n_budgets)
        positions = (ctypes.c_int * n_budgets)()
        length = ctypes.c_int(200 * n_budgets)
        raw = ctypes.create_string_buffer(length.value)
        type_ids = (ctypes.c_int * n_budgets)()
        location_type_ids = (ctypes.c_int * n_budgets)()
        status = ctypes.c_int(0)
        self._call("IW_Model_GetBudget_List", ctypes.byref(n), positions,
                   ctypes.byref(length), raw, type_ids, location_type_ids,
                   ctypes.byref(status))
        self._raise_on_error(status)
        return pd.DataFrame({
            "name": self._names(raw, positions, n),
            "budget_type_id": list(type_ids),
            "location_type_id": list(location_type_ids),
        })

    def get_budget_n_columns(self, budget_type_id, location_index):
        """Return the number of data columns of a budget at a location."""
        self._require("IW_Model_GetBudget_NColumns")
        n_cols = ctypes.c_int(0)
        status = ctypes.c_int(0)
        self._call("IW_Model_GetBudget_NColumns", ctypes.byref(ctypes.c_int(budget_type_id)),
                   ctypes.byref(ctypes.c_int(location_index)), ctypes.byref(n_cols),
                   ctypes.byref(status))
        self._raise_on_error(status)
        return n_cols.value

    def get_budget_column_titles(self, budget_type_id, location_index,
                                 length_unit="FT", area_unit="AC", volume_unit="AF"):
        """Return the column titles of a budget at a location.

        The units replace the unit markers in the titles.
        """
        self._require("IW_Model_GetBudget_ColumnTitles")
        n_cols = self.get_budget_n_columns(budget_type_id, location_index)
        units = [length_unit, area_unit, volume_unit]
        unit_length = ctypes.c_int(max(len(u) for u in units) + 1)
        lt, ar, vl = (ctypes.create_string_buffer(u.encode("utf-8"), unit_length.value) for u in units)
        n = ctypes.c_int(n_cols)
        positions = (ctypes.c_int * max(n_cols, 1))()
        length = ctypes.c_int(200 * max(n_cols, 1))
        raw = ctypes.create_string_buffer(length.value)
        status = ctypes.c_int(0)
        self._call("IW_Model_GetBudget_ColumnTitles", ctypes.byref(ctypes.c_int(budget_type_id)),
                   ctypes.byref(ctypes.c_int(location_index)), ctypes.byref(unit_length),
                   lt, ar, vl, ctypes.byref(n), positions, ctypes.byref(length), raw,
                   ctypes.byref(status))
        self._raise_on_error(status)
        return self._names(raw, positions, n)

    def get_budget_time_series(self, budget_type_id, location_index, columns=None,
                               begin_date=None, end_date=None, interval=None,
                               length_factor=1.0, area_factor=1.0, volume_factor=1.0):
        """Return budget values at a location as a time series.

        Parameters
        ----------
        budget_type_id : int
            budget type, from ``get_budget_type_ids()``
        location_index : int
            1-based location index
        columns : list of int, optional
            1-based data column numbers (default: every column)
        begin_date, end_date : str, optional
            IWFM time stamps (default: the simulation period)
        interval : str, optional
            output interval such as '1MON' or '1YEAR' (default: the
            simulation time step)
        length_factor, area_factor, volume_factor : float
            unit conversion factors

        Returns
        -------
        pd.DataFrame
            ``Time`` and one column per requested budget column, named by
            its title. ``df.attrs['data_types']`` holds each column's data
            type ID.
        """
        self._require("IW_Model_GetBudget_TSData")
        begin_date, end_date = self._date_range(begin_date, end_date)
        if interval is None:
            interval = self.get_time_specs()[1]
        titles = self.get_budget_column_titles(budget_type_id, location_index)
        if columns is None:
            columns = list(range(1, len(titles) + 1))
        cols, n_cols = _int_array(columns)
        n_times = self._n_output_times(begin_date, end_date, interval)
        begin, length_date = _cstr(begin_date)
        end, _ = _cstr(end_date)
        interval_buf, length_interval = _cstr(interval)
        dates = (ctypes.c_double * n_times)()
        values = ((ctypes.c_double * n_times) * max(n_cols.value, 1))()
        data_types = (ctypes.c_int * max(n_cols.value, 1))()
        n_out = ctypes.c_int(0)
        status = ctypes.c_int(0)
        self._call("IW_Model_GetBudget_TSData", ctypes.byref(ctypes.c_int(budget_type_id)),
                   ctypes.byref(ctypes.c_int(location_index)), ctypes.byref(n_cols), cols,
                   ctypes.byref(length_date), begin, end, ctypes.byref(length_interval),
                   interval_buf, ctypes.byref(ctypes.c_double(length_factor)),
                   ctypes.byref(ctypes.c_double(area_factor)),
                   ctypes.byref(ctypes.c_double(volume_factor)), dates,
                   ctypes.byref(ctypes.c_int(n_times)), values, data_types,
                   ctypes.byref(n_out), ctypes.byref(status))
        self._raise_on_error(status)
        k = n_out.value
        df = pd.DataFrame({"Time": _excel_dates(list(dates)[:k])})
        data = np.array(values)[:, :k]
        for i, c in enumerate(columns):
            name = titles[c - 1] if 0 < c <= len(titles) else f"column_{c}"
            df[name] = data[i]
        df.attrs["data_types"] = dict(zip(df.columns[1:], list(data_types)[:n_cols.value]))
        return df

    def _flows(self, procedure, head_args, n_flows, n_times, begin_date, end_date,
               volume_factor, calendar_year):
        """Shared call for the annual-flow procedures (budget and zone budget)."""
        begin, length_date = _cstr(begin_date)
        end, _ = _cstr(end_date)
        flows = ((ctypes.c_double * n_flows) * n_times)()
        n_flows_out = ctypes.c_int(0)
        n_times_out = ctypes.c_int(0)
        length_names = ctypes.c_int(50 * n_flows)
        names = ctypes.create_string_buffer(length_names.value)
        positions = (ctypes.c_int * n_flows)()
        years = (ctypes.c_int * n_times)()
        status = ctypes.c_int(0)
        args = list(head_args) + [ctypes.byref(length_date), begin, end]
        if procedure.endswith("_1"):
            args.append(ctypes.byref(ctypes.c_int(1 if calendar_year else 0)))
        args += [ctypes.byref(ctypes.c_double(volume_factor)), ctypes.byref(ctypes.c_int(n_flows)),
                 ctypes.byref(ctypes.c_int(n_times)), flows, ctypes.byref(n_flows_out),
                 ctypes.byref(n_times_out), ctypes.byref(length_names), names, positions,
                 years, ctypes.byref(status)]
        self._call(procedure, *args)
        self._raise_on_error(status)
        nf, nt = n_flows_out.value, n_times_out.value
        flow_names = self._names(names, positions, ctypes.c_int(nf))
        data = np.array(flows)[:nt, :nf]
        df = pd.DataFrame(data, columns=flow_names, index=list(years)[:nt])
        df.index.name = "calendar_year" if calendar_year else "water_year"
        return df

    def _annual_procedure(self, base, calendar_year):
        if hasattr(self.dll, base + "_1"):
            return base + "_1"
        if calendar_year:
            raise AttributeError(f"the loaded IWFM library has no {base}_1; only water years are available")
        self._require(base)
        return base

    def _flow_bound(self, n_cols):
        # The number of flows is at most the number of budget columns; leave
        # room in case a component reports more.
        return 2 * max(n_cols, 1) + 20

    def get_budget_annual_flows(self, budget_type_id, location_index, land_use_type_id=0,
                                small_watershed_component="root_zone", begin_date=None,
                                end_date=None, volume_factor=1.0, calendar_year=False):
        """Return annual budget flows at a location.

        Parameters
        ----------
        land_use_type_id : int
            for land and water use and root zone budgets, the land use
            (from ``get_land_use_type_ids()``); ignored for other budgets
        small_watershed_component : str
            'root_zone' or 'groundwater', for small watershed budgets
        calendar_year : bool
            sum by calendar year instead of water year

        Returns
        -------
        pd.DataFrame
            one row per year (index ``water_year`` or ``calendar_year``),
            one column per flow
        """
        procedure = self._annual_procedure("IW_Model_GetBudget_AnnualFlows", calendar_year)
        begin_date, end_date = self._date_range(begin_date, end_date)
        n_flows = self._flow_bound(self.get_budget_n_columns(budget_type_id, location_index))
        head = [ctypes.byref(ctypes.c_int(budget_type_id)), ctypes.byref(ctypes.c_int(location_index)),
                ctypes.byref(ctypes.c_int(land_use_type_id)),
                ctypes.byref(ctypes.c_int(self._swshed_component(small_watershed_component)))]
        return self._flows(procedure, head, n_flows, self._n_years(begin_date, end_date),
                           begin_date, end_date, volume_factor, calendar_year)

    @staticmethod
    def _swshed_component(component):
        if component not in ("root_zone", "groundwater"):
            raise ValueError("small_watershed_component must be 'root_zone' or 'groundwater'")
        return 1 if component == "root_zone" else 0

    def _monthly(self, procedure, head_args, n_flows, begin_date, end_date, volume_factor):
        begin, length_date = _cstr(begin_date)
        end, _ = _cstr(end_date)
        flows = ((ctypes.c_double * n_flows) * 12)()
        sd_flows = ((ctypes.c_double * n_flows) * 12)()
        n_flows_out = ctypes.c_int(0)
        length_names = ctypes.c_int(50 * n_flows)
        names = ctypes.create_string_buffer(length_names.value)
        positions = (ctypes.c_int * n_flows)()
        status = ctypes.c_int(0)
        self._call(procedure, *head_args, ctypes.byref(length_date), begin, end,
                   ctypes.byref(ctypes.c_double(volume_factor)), ctypes.byref(ctypes.c_int(n_flows)),
                   flows, sd_flows, ctypes.byref(n_flows_out), ctypes.byref(length_names), names,
                   positions, ctypes.byref(status))
        self._raise_on_error(status)
        nf = n_flows_out.value
        flow_names = self._names(names, positions, ctypes.c_int(nf))
        mean = pd.DataFrame(np.array(flows)[:, :nf], columns=flow_names, index=WATER_YEAR_MONTHS)
        sd = pd.DataFrame(np.array(sd_flows)[:, :nf], columns=flow_names, index=WATER_YEAR_MONTHS)
        mean.index.name = sd.index.name = "month"
        return mean, sd

    def get_budget_monthly_average_flows(self, budget_type_id, location_index, land_use_type_id=0,
                                         small_watershed_component="root_zone", begin_date=None,
                                         end_date=None, volume_factor=1.0):
        """Return the average and standard deviation of budget flows by month.

        The period is trimmed to whole water years (October to September);
        it must contain at least one.

        Returns
        -------
        tuple of pd.DataFrame
            (average, standard deviation): one row per month, October first,
            one column per flow
        """
        self._require("IW_Model_GetBudget_MonthlyAverageFlows")
        begin_date, end_date = self._date_range(begin_date, end_date)
        n_flows = self._flow_bound(self.get_budget_n_columns(budget_type_id, location_index))
        head = [ctypes.byref(ctypes.c_int(budget_type_id)), ctypes.byref(ctypes.c_int(location_index)),
                ctypes.byref(ctypes.c_int(land_use_type_id)),
                ctypes.byref(ctypes.c_int(self._swshed_component(small_watershed_component)))]
        return self._monthly("IW_Model_GetBudget_MonthlyAverageFlows", head, n_flows,
                             begin_date, end_date, volume_factor)

    def _cumulative(self, procedure, head_args, begin_date, end_date, interval, volume_factor):
        begin, length_date = _cstr(begin_date)
        end, _ = _cstr(end_date)
        interval_buf, length_interval = _cstr(interval)
        n_times = self._n_output_times(begin_date, end_date, interval)
        dates = (ctypes.c_double * n_times)()
        values = (ctypes.c_double * n_times)()
        n_out = ctypes.c_int(0)
        status = ctypes.c_int(0)
        self._call(procedure, *head_args, ctypes.byref(length_date), begin, end,
                   ctypes.byref(length_interval), interval_buf,
                   ctypes.byref(ctypes.c_double(volume_factor)), dates,
                   ctypes.byref(ctypes.c_int(n_times)), values, ctypes.byref(n_out),
                   ctypes.byref(status))
        self._raise_on_error(status)
        k = n_out.value
        return pd.DataFrame({"Time": _excel_dates(list(dates)[:k]),
                             "cumulative_storage_change": list(values)[:k]})

    def get_budget_cumulative_gw_storage_change(self, subregion_index, begin_date=None,
                                                end_date=None, interval=None, volume_factor=1.0):
        """Return the cumulative change in groundwater storage in a subregion.

        Returns
        -------
        pd.DataFrame
            ``Time`` and ``cumulative_storage_change``
        """
        self._require("IW_Model_GetBudget_CumGWStorChange")
        begin_date, end_date = self._date_range(begin_date, end_date)
        if interval is None:
            interval = self.get_time_specs()[1]
        return self._cumulative("IW_Model_GetBudget_CumGWStorChange",
                                [ctypes.byref(ctypes.c_int(subregion_index))],
                                begin_date, end_date, interval, volume_factor)

    def _annual_cumulative(self, procedure, head_args, begin_date, end_date, volume_factor,
                           calendar_year):
        begin, length_date = _cstr(begin_date)
        end, _ = _cstr(end_date)
        n_times = self._n_years(begin_date, end_date)
        values = (ctypes.c_double * n_times)()
        years = (ctypes.c_int * n_times)()
        n_out = ctypes.c_int(0)
        status = ctypes.c_int(0)
        args = list(head_args) + [ctypes.byref(length_date), begin, end]
        if procedure.endswith("_1"):
            args.append(ctypes.byref(ctypes.c_int(1 if calendar_year else 0)))
        args += [ctypes.byref(ctypes.c_double(volume_factor)), ctypes.byref(ctypes.c_int(n_times)),
                 values, years, ctypes.byref(n_out), ctypes.byref(status)]
        self._call(procedure, *args)
        self._raise_on_error(status)
        k = n_out.value
        s = pd.Series(list(values)[:k], index=list(years)[:k], name="cumulative_storage_change")
        s.index.name = "calendar_year" if calendar_year else "water_year"
        return s

    def get_budget_annual_cumulative_gw_storage_change(self, subregion_index, begin_date=None,
                                                       end_date=None, volume_factor=1.0,
                                                       calendar_year=False):
        """Return the cumulative change in groundwater storage in a subregion
        at the end of each year.

        Returns
        -------
        pd.Series
            indexed by ``water_year`` or ``calendar_year``

        Note
        ----
        Stock DWR libraries (2026.0.1848 and earlier) return invalid values
        here whenever the full model is loaded, so this raises IWFMError on
        them. The zone budget version
        (``get_zbudget_annual_cumulative_gw_storage_change``) works with
        every library.
        """
        if self._abi == "switch":
            raise IWFMError(
                "IW_Model_GetBudget_AnnualCumGWStorChange returns invalid values in the "
                "stock DWR libraries; use get_zbudget_annual_cumulative_gw_storage_change "
                "with zones equal to the subregions, or the handle-based fork library."
            )
        procedure = self._annual_procedure("IW_Model_GetBudget_AnnualCumGWStorChange", calendar_year)
        begin_date, end_date = self._date_range(begin_date, end_date)
        return self._annual_cumulative(procedure, [ctypes.byref(ctypes.c_int(subregion_index))],
                                       begin_date, end_date, volume_factor, calendar_year)

    # ------------------------------------------------------------------
    # zone budgets
    #
    # A zone definition is one (element, layer, zone ID) triple per entry,
    # with zone_extent 'horizontal' (zones span all layers; layers are
    # ignored) or 'vertical' (zones are defined layer by layer).
    # ------------------------------------------------------------------
    def get_n_zbudgets(self):
        """Return the number of zone budgets the model writes."""
        self._require("IW_Model_GetZBudget_N")
        n = ctypes.c_int(0)
        status = ctypes.c_int(0)
        self._call("IW_Model_GetZBudget_N", ctypes.byref(n), ctypes.byref(status))
        self._raise_on_error(status)
        return n.value

    def get_zbudget_list(self):
        """Return the model's zone budgets.

        Returns
        -------
        pd.DataFrame
            one row per zone budget: ``name`` and ``zbudget_type_id`` (see
            ``get_zbudget_type_ids()``)
        """
        self._require("IW_Model_GetZBudget_List")
        n_zbudgets = self.get_n_zbudgets()
        if n_zbudgets == 0:
            return pd.DataFrame(columns=["name", "zbudget_type_id"])
        n = ctypes.c_int(n_zbudgets)
        positions = (ctypes.c_int * n_zbudgets)()
        length = ctypes.c_int(200 * n_zbudgets)
        raw = ctypes.create_string_buffer(length.value)
        type_ids = (ctypes.c_int * n_zbudgets)()
        status = ctypes.c_int(0)
        self._call("IW_Model_GetZBudget_List", ctypes.byref(n), positions, ctypes.byref(length),
                   raw, type_ids, ctypes.byref(status))
        self._raise_on_error(status)
        return pd.DataFrame({"name": self._names(raw, positions, n),
                             "zbudget_type_id": list(type_ids)})

    def get_zbudget_n_columns(self, zbudget_type_id, zone_id, zone_extent, elements, layers, zone_ids):
        """Return the number of data columns of a zone budget for a zone."""
        self._require("IW_Model_GetZBudget_NColumns")
        extent, n, elems, lays, zones = self._zone_arrays(zone_extent, elements, layers, zone_ids)
        n_cols = ctypes.c_int(0)
        status = ctypes.c_int(0)
        self._call("IW_Model_GetZBudget_NColumns", ctypes.byref(ctypes.c_int(zbudget_type_id)),
                   ctypes.byref(ctypes.c_int(zone_id)), ctypes.byref(extent), ctypes.byref(n),
                   elems, lays, zones, ctypes.byref(n_cols), ctypes.byref(status))
        self._raise_on_error(status)
        return n_cols.value

    def get_zbudget_column_titles(self, zbudget_type_id, zone_id, zone_extent, elements, layers,
                                  zone_ids, area_unit="AC", volume_unit="AF"):
        """Return the column titles of a zone budget for a zone."""
        self._require("IW_Model_GetZBudget_ColumnTitles")
        n_cols = self.get_zbudget_n_columns(zbudget_type_id, zone_id, zone_extent, elements,
                                            layers, zone_ids)
        extent, n, elems, lays, zones = self._zone_arrays(zone_extent, elements, layers, zone_ids)
        unit_length = ctypes.c_int(max(len(area_unit), len(volume_unit)) + 1)
        ar = ctypes.create_string_buffer(area_unit.encode("utf-8"), unit_length.value)
        vl = ctypes.create_string_buffer(volume_unit.encode("utf-8"), unit_length.value)
        nc = ctypes.c_int(n_cols)
        positions = (ctypes.c_int * max(n_cols, 1))()
        length = ctypes.c_int(200 * max(n_cols, 1))
        raw = ctypes.create_string_buffer(length.value)
        status = ctypes.c_int(0)
        self._call("IW_Model_GetZBudget_ColumnTitles", ctypes.byref(ctypes.c_int(zbudget_type_id)),
                   ctypes.byref(ctypes.c_int(zone_id)), ctypes.byref(extent), ctypes.byref(n),
                   elems, lays, zones, ctypes.byref(unit_length), ar, vl, ctypes.byref(nc),
                   positions, ctypes.byref(length), raw, ctypes.byref(status))
        self._raise_on_error(status)
        return self._names(raw, positions, nc)

    def get_zbudget_time_series(self, zbudget_type_id, zone_id, zone_extent, elements, layers,
                                zone_ids, columns=None, begin_date=None, end_date=None,
                                interval=None, area_factor=1.0, volume_factor=1.0):
        """Return zone budget values for a zone as a time series.

        Returns
        -------
        pd.DataFrame
            ``Time`` and one column per requested column, named by its
            title; ``df.attrs['data_types']`` holds each column's data type
        """
        self._require("IW_Model_GetZBudget_TSData")
        begin_date, end_date = self._date_range(begin_date, end_date)
        if interval is None:
            interval = self.get_time_specs()[1]
        titles = self.get_zbudget_column_titles(zbudget_type_id, zone_id, zone_extent, elements,
                                                layers, zone_ids)
        if columns is None:
            columns = list(range(1, len(titles) + 1))
        cols, n_cols = _int_array(columns)
        extent, n, elems, lays, zones = self._zone_arrays(zone_extent, elements, layers, zone_ids)
        n_times = self._n_output_times(begin_date, end_date, interval)
        begin, length_date = _cstr(begin_date)
        end, _ = _cstr(end_date)
        interval_buf, length_interval = _cstr(interval)
        dates = (ctypes.c_double * n_times)()
        values = ((ctypes.c_double * n_times) * max(n_cols.value, 1))()
        data_types = (ctypes.c_int * max(n_cols.value, 1))()
        n_out = ctypes.c_int(0)
        status = ctypes.c_int(0)
        self._call("IW_Model_GetZBudget_TSData", ctypes.byref(ctypes.c_int(zbudget_type_id)),
                   ctypes.byref(ctypes.c_int(zone_id)), ctypes.byref(n_cols), cols,
                   ctypes.byref(extent), ctypes.byref(n), elems, lays, zones,
                   ctypes.byref(length_date), begin, end, ctypes.byref(length_interval),
                   interval_buf, ctypes.byref(ctypes.c_double(area_factor)),
                   ctypes.byref(ctypes.c_double(volume_factor)), dates,
                   ctypes.byref(ctypes.c_int(n_times)), values, data_types, ctypes.byref(n_out),
                   ctypes.byref(status))
        self._raise_on_error(status)
        k = n_out.value
        df = pd.DataFrame({"Time": _excel_dates(list(dates)[:k])})
        data = np.array(values)[:, :k]
        for i, c in enumerate(columns):
            name = titles[c - 1] if 0 < c <= len(titles) else f"column_{c}"
            df[name] = data[i]
        df.attrs["data_types"] = dict(zip(df.columns[1:], list(data_types)[:n_cols.value]))
        return df

    def get_zbudget_annual_flows(self, zbudget_type_id, zone_id, zone_extent, elements, layers,
                                 zone_ids, land_use_type_id=0, begin_date=None, end_date=None,
                                 volume_factor=1.0, calendar_year=False):
        """Return annual zone budget flows for a zone (see get_budget_annual_flows)."""
        procedure = self._annual_procedure("IW_Model_GetZBudget_AnnualFlows", calendar_year)
        begin_date, end_date = self._date_range(begin_date, end_date)
        n_flows = self._flow_bound(self.get_zbudget_n_columns(zbudget_type_id, zone_id, zone_extent,
                                                              elements, layers, zone_ids))
        extent, n, elems, lays, zones = self._zone_arrays(zone_extent, elements, layers, zone_ids)
        head = [ctypes.byref(ctypes.c_int(zbudget_type_id)), ctypes.byref(ctypes.c_int(zone_id)),
                ctypes.byref(ctypes.c_int(land_use_type_id)), ctypes.byref(extent),
                ctypes.byref(n), elems, lays, zones]
        return self._flows(procedure, head, n_flows, self._n_years(begin_date, end_date),
                           begin_date, end_date, volume_factor, calendar_year)

    def get_zbudget_monthly_average_flows(self, zbudget_type_id, zone_id, zone_extent, elements,
                                          layers, zone_ids, land_use_type_id=0, begin_date=None,
                                          end_date=None, volume_factor=1.0):
        """Return the average and standard deviation of zone budget flows by
        month (see get_budget_monthly_average_flows)."""
        self._require("IW_Model_GetZBudget_MonthlyAverageFlows")
        begin_date, end_date = self._date_range(begin_date, end_date)
        n_flows = self._flow_bound(self.get_zbudget_n_columns(zbudget_type_id, zone_id, zone_extent,
                                                              elements, layers, zone_ids))
        extent, n, elems, lays, zones = self._zone_arrays(zone_extent, elements, layers, zone_ids)
        head = [ctypes.byref(ctypes.c_int(zbudget_type_id)), ctypes.byref(ctypes.c_int(zone_id)),
                ctypes.byref(ctypes.c_int(land_use_type_id)), ctypes.byref(extent),
                ctypes.byref(n), elems, lays, zones]
        return self._monthly("IW_Model_GetZBudget_MonthlyAverageFlows", head, n_flows,
                             begin_date, end_date, volume_factor)

    def get_zbudget_cumulative_gw_storage_change(self, zone_id, zone_extent, elements, layers,
                                                 zone_ids, begin_date=None, end_date=None,
                                                 interval=None, volume_factor=1.0):
        """Return the cumulative change in groundwater storage in a zone."""
        self._require("IW_Model_GetZBudget_CumGWStorChange")
        begin_date, end_date = self._date_range(begin_date, end_date)
        if interval is None:
            interval = self.get_time_specs()[1]
        extent, n, elems, lays, zones = self._zone_arrays(zone_extent, elements, layers, zone_ids)
        head = [ctypes.byref(ctypes.c_int(zone_id)), ctypes.byref(extent), ctypes.byref(n),
                elems, lays, zones]
        return self._cumulative("IW_Model_GetZBudget_CumGWStorChange", head, begin_date,
                                end_date, interval, volume_factor)

    def get_zbudget_annual_cumulative_gw_storage_change(self, zone_id, zone_extent, elements,
                                                        layers, zone_ids, begin_date=None,
                                                        end_date=None, volume_factor=1.0,
                                                        calendar_year=False):
        """Return the cumulative change in groundwater storage in a zone at the
        end of each year."""
        procedure = self._annual_procedure("IW_Model_GetZBudget_AnnualCumGWStorChange", calendar_year)
        begin_date, end_date = self._date_range(begin_date, end_date)
        extent, n, elems, lays, zones = self._zone_arrays(zone_extent, elements, layers, zone_ids)
        head = [ctypes.byref(ctypes.c_int(zone_id)), ctypes.byref(extent), ctypes.byref(n),
                elems, lays, zones]
        return self._annual_cumulative(procedure, head, begin_date, end_date, volume_factor,
                                       calendar_year)
