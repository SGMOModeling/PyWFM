"""IWFMModel wrappers for parametric grids, stream flow terms, wells,
diversions, future water demands, pumping and transport.

Pumping (get_pumping_required / get_pumping_actual) needs the handle-based
fork library (IW_Model_GetPumpingRequired / IW_Model_GetPumpingActual).
"""
import ctypes

import numpy as np
import pandas as pd

from pywfm._model_budgets import _cstr


class ModelExtrasMixin:
    """Wrappers for IW_Model_* procedures not covered elsewhere."""

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _id_to_index(self, value, ids, what):
        ids = np.asarray(ids)
        hits = np.nonzero(ids == value)[0]
        if hits.size == 0:
            raise ValueError(f"{what} {value} is not valid")
        return int(hits[0]) + 1

    def _stream_node_values(self, procedure, conversion_factor):
        """Per-stream-node values from an (iNNodes, rConvFactor, rValues, iStat) procedure."""
        self._require(procedure)
        n = self.get_n_stream_nodes()
        values = (ctypes.c_double * max(n, 1))()
        status = ctypes.c_int(0)
        self._call(procedure, ctypes.byref(ctypes.c_int(n)),
                   ctypes.byref(ctypes.c_double(conversion_factor)), values,
                   ctypes.byref(status))
        self._raise_on_error(status)
        return np.array(values)[:n]

    # ------------------------------------------------------------------
    # groundwater
    # ------------------------------------------------------------------
    def get_gw_heads_initial_conditions(self):
        """Return the initial groundwater heads.

        Returns
        -------
        np.ndarray
            shape (n_layers, n_nodes)
        """
        self._require("IW_Model_GetGWHeadsIC")
        n_nodes, n_layers = self.get_n_nodes(), self.get_n_layers()
        heads = ((ctypes.c_double * n_nodes) * n_layers)()
        status = ctypes.c_int(0)
        self._call("IW_Model_GetGWHeadsIC", ctypes.byref(ctypes.c_int(n_nodes)),
                   ctypes.byref(ctypes.c_int(n_layers)), heads, ctypes.byref(status))
        self._raise_on_error(status)
        return np.array(heads)

    def get_n_parametric_grids(self):
        """Return the number of parametric grids used to define aquifer parameters."""
        self._require("IW_Model_GetGWNParametricGrids")
        n = ctypes.c_int(0)
        status = ctypes.c_int(0)
        self._call("IW_Model_GetGWNParametricGrids", ctypes.byref(n), ctypes.byref(status))
        self._raise_on_error(status)
        return n.value

    def _parametric_count(self, procedure, grid_id):
        self._require(procedure)
        n = ctypes.c_int(0)
        status = ctypes.c_int(0)
        self._call(procedure, ctypes.byref(ctypes.c_int(grid_id)), ctypes.byref(n),
                   ctypes.byref(status))
        self._raise_on_error(status)
        return n.value

    def get_n_parametric_nodes(self, grid_id):
        """Return the number of nodes of parametric grid ``grid_id`` (1-based)."""
        return self._parametric_count("IW_Model_GetGWNParametricNodes", grid_id)

    def get_n_parametric_elements(self, grid_id):
        """Return the number of elements of parametric grid ``grid_id`` (1-based)."""
        return self._parametric_count("IW_Model_GetGWNParametricElements", grid_id)

    def get_parametric_node_coordinates(self, grid_id):
        """Return the x and y coordinates of the nodes of a parametric grid.

        Returns
        -------
        tuple of np.ndarray
            (x, y)
        """
        self._require("IW_Model_GetGWParametricNodeXY")
        n = self.get_n_parametric_nodes(grid_id)
        x = (ctypes.c_double * max(n, 1))()
        y = (ctypes.c_double * max(n, 1))()
        status = ctypes.c_int(0)
        self._call("IW_Model_GetGWParametricNodeXY", ctypes.byref(ctypes.c_int(grid_id)),
                   ctypes.byref(ctypes.c_int(n)), x, y, ctypes.byref(status))
        self._raise_on_error(status)
        return np.array(x)[:n], np.array(y)[:n]

    def get_parametric_element_vertices(self, grid_id, element_index):
        """Return the node numbers at the vertices of a parametric grid element.

        Returns
        -------
        np.ndarray
            four parametric node numbers; the fourth is 0 for a triangle
        """
        self._require("IW_Model_GetGWParametricElementConfigData")
        vertices = (ctypes.c_int * 4)()
        status = ctypes.c_int(0)
        self._call("IW_Model_GetGWParametricElementConfigData", ctypes.byref(ctypes.c_int(grid_id)),
                   ctypes.byref(ctypes.c_int(element_index)), vertices, ctypes.byref(status))
        self._raise_on_error(status)
        return np.array(vertices)

    def get_parametric_aquifer_parameters(self, grid_id):
        """Return the aquifer parameters at the nodes of a parametric grid.

        Returns
        -------
        dict of np.ndarray
            ``horizontal_k``, ``aquifer_vertical_k``, ``aquitard_vertical_k``,
            ``specific_yield`` and ``specific_storage``, each of shape
            (n_layers, n_parametric_nodes)
        """
        self._require("IW_Model_GetGWParametricAquiferParameters")
        n, n_layers = self.get_n_parametric_nodes(grid_id), self.get_n_layers()
        arrays = [((ctypes.c_double * max(n, 1)) * n_layers)() for _ in range(5)]
        status = ctypes.c_int(0)
        self._call("IW_Model_GetGWParametricAquiferParameters", ctypes.byref(ctypes.c_int(grid_id)),
                   ctypes.byref(ctypes.c_int(n)), ctypes.byref(ctypes.c_int(n_layers)), *arrays,
                   ctypes.byref(status))
        self._raise_on_error(status)
        names = ["horizontal_k", "aquifer_vertical_k", "aquitard_vertical_k",
                 "specific_yield", "specific_storage"]
        return {k: np.array(a)[:, :n] for k, a in zip(names, arrays)}

    # ------------------------------------------------------------------
    # wells and pumping
    # ------------------------------------------------------------------
    def get_n_well_elements(self, well_id):
        """Return the number of elements a well delivers water to."""
        self._require("IW_Model_GetWellNElems")
        index = self._id_to_index(well_id, self.get_well_ids(), "well_id")
        n = ctypes.c_int(0)
        status = ctypes.c_int(0)
        self._call("IW_Model_GetWellNElems", ctypes.byref(ctypes.c_int(index)), ctypes.byref(n),
                   ctypes.byref(status))
        self._raise_on_error(status)
        return n.value

    def get_well_elements(self, well_id):
        """Return the IDs of the elements a well delivers water to."""
        self._require("IW_Model_GetWellElems")
        index = self._id_to_index(well_id, self.get_well_ids(), "well_id")
        n = self.get_n_well_elements(well_id)
        if n == 0:
            return np.array([], dtype=int)
        elements = (ctypes.c_int * n)()
        status = ctypes.c_int(0)
        self._call("IW_Model_GetWellElems", ctypes.byref(ctypes.c_int(index)),
                   ctypes.byref(ctypes.c_int(n)), elements, ctypes.byref(status))
        self._raise_on_error(status)
        return self.get_element_ids()[np.array(elements) - 1]

    def _pumping(self, procedure, pump_type):
        self._require(procedure)
        if pump_type == "wells":
            type_id, n = self.get_supply_type_id_well(), self.get_n_wells()
        elif pump_type == "element_pumps":
            type_id, n = self.get_supply_type_id_elempump(), self.get_n_element_pumps()
        else:
            raise ValueError("pump_type must be 'wells' or 'element_pumps'")
        values = (ctypes.c_double * max(n, 1))()
        status = ctypes.c_int(0)
        self._call(procedure, ctypes.byref(ctypes.c_int(type_id)), ctypes.byref(ctypes.c_int(n)),
                   values, ctypes.byref(status))
        self._raise_on_error(status)
        return np.array(values)[:n]

    def get_pumping_required(self, pump_type):
        """Return the required pumping at every well or element pump for the
        current time step.

        This is the pumping after supply adjustment and before any reduction
        for insufficient water in the aquifer: the values a pumping data
        file must specify to reproduce the time step with supply adjustment
        turned off. Call it after the time step is simulated, before the
        next time series data are read. Needs a model instantiated for
        simulation and the handle-based fork library.

        Parameters
        ----------
        pump_type : str
            'wells' or 'element_pumps'

        Returns
        -------
        np.ndarray
            one value per well or element pump, in model order; negative
            for pumping, positive for recharge, in model volume units per
            simulation time step
        """
        return self._pumping("IW_Model_GetPumpingRequired", pump_type)

    def get_pumping_actual(self, pump_type):
        """Return the actual pumping at every well or element pump for the
        current time step, after reductions for insufficient water in the
        aquifer. See get_pumping_required."""
        return self._pumping("IW_Model_GetPumpingActual", pump_type)

    # ------------------------------------------------------------------
    # streams and diversions
    # ------------------------------------------------------------------
    def get_stream_bypass_inflows(self, conversion_factor=1.0):
        """Return the bypass inflows at every stream node for the current time step."""
        return self._stream_node_values("IW_Model_GetStrmBypassInflows", conversion_factor)

    def get_stream_net_bypass_inflows(self, conversion_factor=1.0):
        """Return the bypass inflows minus bypass outflows at every stream node."""
        return self._stream_node_values("IW_Model_GetStrmNetBypassInflows", conversion_factor)

    def get_stream_evaporation(self, conversion_factor=1.0):
        """Return the evaporation from every stream node for the current time step."""
        return self._stream_node_values("IW_Model_GetStrmEvap", conversion_factor)

    def get_stream_water_supply_available(self, conversion_factor=1.0):
        """Return the water supply available (WSA) at every stream node."""
        return self._stream_node_values("IW_Model_GetStrmWSAs", conversion_factor)

    def get_stream_net_inflows_excluding_diversions(self, conversion_factor=1.0):
        """Return the net inflow to every stream node excluding diversions:
        tributary inflows, rainfall runoff, return flows, tile drains,
        riparian ET, gains from groundwater and lakes, and net bypass
        inflows."""
        return self._stream_node_values("IW_Model_GetStrmNetInflows_ExcDivsInflows", conversion_factor)

    def get_stream_net_inflows_excluding_diversions_and_groundwater(self, conversion_factor=1.0):
        """Return the net inflow to every stream node excluding diversions and
        the gain from groundwater."""
        return self._stream_node_values("IW_Model_GetStrmNetInflows_ExcDivsInflowsGW",
                                        conversion_factor)

    def get_stream_required_diversions(self, diversion_ids=None, conversion_factor=1.0):
        """Return the required diversions for the current time step.

        Supply adjustment changes them during a time step; after the step
        they are the values a diversion data file must specify to reproduce
        it with supply adjustment turned off.

        Parameters
        ----------
        diversion_ids : list of int, optional
            default: every diversion

        Returns
        -------
        np.ndarray
            one value per requested diversion
        """
        self._require("IW_Model_GetStrmRequiredDiversions_AtSomeDiversions")
        all_ids = self.get_diversion_ids()
        if diversion_ids is None:
            diversion_ids = list(all_ids)
        indices = [self._id_to_index(d, all_ids, "diversion_id") for d in diversion_ids]
        n = len(indices)
        idx = (ctypes.c_int * max(n, 1))(*indices)
        values = (ctypes.c_double * max(n, 1))()
        status = ctypes.c_int(0)
        self._call("IW_Model_GetStrmRequiredDiversions_AtSomeDiversions",
                   ctypes.byref(ctypes.c_int(n)), idx,
                   ctypes.byref(ctypes.c_double(conversion_factor)), values,
                   ctypes.byref(status))
        self._raise_on_error(status)
        return np.array(values)[:n]

    def get_stream_diversion_data_values(self):
        """Return every column of the diversion data file for the current time
        step, as the model uses them: in model units per simulation time step,
        after the file's conversion factor and the conversion of rates to the
        time step. Call after read_timeseries_data. Needs a model
        instantiated for simulation and the handle-based fork library.

        Returns
        -------
        np.ndarray
            one value per data column (empty without a diversion data file)
        """
        self._require("IW_Model_GetStrmDiversionDataValues")
        n = ctypes.c_int(0)
        status = ctypes.c_int(0)
        self._call("IW_Model_GetStrmDiversionDataNColumns", ctypes.byref(n), ctypes.byref(status))
        self._raise_on_error(status)
        values = (ctypes.c_double * max(n.value, 1))()
        self._call("IW_Model_GetStrmDiversionDataValues", ctypes.byref(n), values,
                   ctypes.byref(status))
        self._raise_on_error(status)
        return np.array(values)[:n.value]

    def get_diversion_recharge_zone(self, diversion_id):
        """Return the elements that a diversion's recoverable losses recharge.

        Returns
        -------
        pd.DataFrame
            ``element_id`` and ``fraction`` of the recoverable loss
        """
        self._require("IW_Model_GetStrmDiversionRechargeZoneElems")
        index = self._id_to_index(diversion_id, self.get_diversion_ids(), "diversion_id")
        n = ctypes.c_int(0)
        status = ctypes.c_int(0)
        self._call("IW_Model_GetStrmDiversionNRechargeZoneElems", ctypes.byref(ctypes.c_int(index)),
                   ctypes.byref(n), ctypes.byref(status))
        self._raise_on_error(status)
        if n.value == 0:
            return pd.DataFrame({"element_id": [], "fraction": []})
        elements = (ctypes.c_int * n.value)()
        fractions = (ctypes.c_double * n.value)()
        self._call("IW_Model_GetStrmDiversionRechargeZoneElems", ctypes.byref(ctypes.c_int(index)),
                   ctypes.byref(n), elements, fractions, ctypes.byref(status))
        self._raise_on_error(status)
        element_ids = self.get_element_ids()[np.array(elements) - 1]
        return pd.DataFrame({"element_id": element_ids, "fraction": np.array(fractions)})

    # ------------------------------------------------------------------
    # land use and future water demands
    # ------------------------------------------------------------------
    def get_land_use_areas_for_time_period(self, land_use_type_id, crop_index=1, begin_date=None,
                                           end_date=None, area_factor=1.0):
        """Return the area of one land use at every element for a time period.

        Parameters
        ----------
        land_use_type_id : int
            from ``get_land_use_type_ids()`` or ``get_land_use_type_ids_2()``
        crop_index : int
            1-based crop number within the land use type (e.g. which
            non-ponded crop); 1 for land uses with one class
        begin_date, end_date : str, optional
            IWFM time stamps (default: the simulation period)

        Returns
        -------
        pd.DataFrame
            one row per simulation time step, one column per element ID

        Note
        ----
        Stock DWR libraries (2026.0.1848 and earlier) reopen the land use
        area files, which fails ("is already open") while the model has them
        open; the handle-based fork library does not.
        """
        self._require("IW_Model_GetLandUseAreasForTimePeriod")
        begin_date, end_date = self._date_range(begin_date, end_date)
        time_stamps, interval = self.get_time_specs()
        n_times = self.get_n_intervals(begin_date, end_date, interval, includes_end_date=True)
        n_elements = self.get_n_elements()
        begin, length_date = _cstr(begin_date)
        end, _ = _cstr(end_date)
        areas = ((ctypes.c_double * n_elements) * n_times)()
        status = ctypes.c_int(0)
        self._call("IW_Model_GetLandUseAreasForTimePeriod", ctypes.byref(length_date), begin, end,
                   ctypes.byref(ctypes.c_int(land_use_type_id)), ctypes.byref(ctypes.c_int(crop_index)),
                   ctypes.byref(ctypes.c_int(n_elements)), ctypes.byref(ctypes.c_int(n_times)),
                   ctypes.byref(ctypes.c_double(area_factor)), areas, ctypes.byref(status))
        self._raise_on_error(status)
        stamps = [begin_date]
        for _ in range(n_times - 1):
            stamps.append(self.increment_time(stamps[-1], interval, 1))
        return pd.DataFrame(np.array(areas), index=stamps, columns=self.get_element_ids())

    def compute_future_water_demands(self, end_date):
        """Compute water demands from the current time step to ``end_date``.

        Call after the time series data of the current time step are read
        (read_timeseries_data); the time series files are rewound
        afterwards. Then use get_future_water_demand_for_diversion.
        """
        self._require("IW_Model_ComputeFutureWaterDemands")
        self._validate_iwfm_date(end_date)
        end, length_date = _cstr(end_date)
        status = ctypes.c_int(0)
        self._call("IW_Model_ComputeFutureWaterDemands", ctypes.byref(length_date), end,
                   ctypes.byref(status))
        self._raise_on_error(status)

    def get_future_water_demand_for_diversion(self, diversion_id, date, conversion_factor=1.0):
        """Return the water demand a diversion serves at a future date
        (after compute_future_water_demands)."""
        self._require("IW_Model_GetFutureWaterDemand_ForDiversion")
        index = self._id_to_index(diversion_id, self.get_diversion_ids(), "diversion_id")
        self._validate_iwfm_date(date)
        buf, length_date = _cstr(date)
        demand = ctypes.c_double(0)
        status = ctypes.c_int(0)
        self._call("IW_Model_GetFutureWaterDemand_ForDiversion", ctypes.byref(ctypes.c_int(index)),
                   ctypes.byref(length_date), buf, ctypes.byref(ctypes.c_double(conversion_factor)),
                   ctypes.byref(demand), ctypes.byref(status))
        self._raise_on_error(status)
        return demand.value

    # ------------------------------------------------------------------
    # transport
    # ------------------------------------------------------------------
    def simulate_transport_for_one_time_step(self):
        """Simulate solute transport for the current time step (models with
        a transport component), after simulate_for_one_timestep."""
        self._require("IW_Model_SimulateTransportForOneTimeStep")
        status = ctypes.c_int(0)
        self._call("IW_Model_SimulateTransportForOneTimeStep", ctypes.byref(status))
        self._raise_on_error(status)
