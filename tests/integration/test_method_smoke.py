"""Parametrized smoke tests across IWFMModel's public method surface.

Each MethodSpec captures (a) the call form, (b) the expected return
type, and (c) optionally a shape check that asserts dimensional
consistency with the model fixture. The parametrized
``test_method_returns_expected`` exercises every spec.

The ``test_specs_cover_all_public_methods`` test fails if a public
IWFMModel method appears in neither ``INQUIRY_SPECS`` nor ``DEFERRED``.
That makes the test surface self-documenting: any new method added to
``model.py`` forces a deliberate categorization at PR time.

This file is the L1 + L2 layer of the test pyramid (smoke + return
type/shape sanity). L3 invariants live in tests/integration/model/.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd
import pytest

import pywfm
from pywfm.misc import IWFMMiscellaneous


# ---------------------------------------------------------------------------
# Spec datatype
# ---------------------------------------------------------------------------


@dataclass
class MethodSpec:
    """Declarative description of how to exercise a single method.

    ``expected_type`` may be a single type or a tuple of types
    (the call to ``isinstance`` accepts either form). Use a tuple to
    accept e.g. both Python ``int`` and ``np.integer`` for scalar returns.

    ``args`` is either a literal tuple or a callable ``model -> tuple``
    so a method that takes a real ID can lazily resolve it from the
    model fixture (e.g. ``args=lambda m: (m.get_subregion_ids()[0],)``).

    ``shape_check`` receives ``(result, model)`` and returns ``True`` if
    the shape is consistent. Use ``None`` to skip.
    """

    name: str
    args: tuple | Callable[..., tuple] = ()
    kwargs: dict = field(default_factory=dict)
    expected_type: Any = (int, np.integer)
    shape_check: Callable[..., bool] | None = None
    precondition: Callable[..., str | None] | None = None
    notes: str = ""

    def resolve_args(self, model) -> tuple:
        return self.args(model) if callable(self.args) else self.args


# Precondition helpers — return a skip reason string, or None if OK
def _need_count(getter: str) -> Callable:
    """Skip if model.<getter>() returns 0."""
    def check(model):
        return None if getattr(model, getter)() > 0 else f"model has no {getter[6:]}"
    return check


# ---------------------------------------------------------------------------
# Common shape-check helpers
# ---------------------------------------------------------------------------


def _ndarray_of_len(getter_name: str) -> Callable:
    """Return a shape_check that asserts result is a 1-D ndarray of length model.<getter>()."""

    def check(result, model):
        expected = getattr(model, getter_name)()
        return isinstance(result, np.ndarray) and result.shape == (expected,)

    return check


def _two_ndarrays_of_len(getter_name: str) -> Callable:
    """For methods returning (x, y) tuples — both length model.<getter>()."""

    def check(result, model):
        expected = getattr(model, getter_name)()
        return (
            isinstance(result, tuple)
            and len(result) == 2
            and all(isinstance(a, np.ndarray) and a.shape == (expected,) for a in result)
        )

    return check


# ---------------------------------------------------------------------------
# Specs — methods exercised by the parametrized smoke test
# ---------------------------------------------------------------------------
#
# Organized by domain so failures are easy to localize. When adding
# a method to model.py, add a MethodSpec here (or, if the method needs
# special handling, add it to DEFERRED with a reason).


# --- Time / lifecycle introspection ----------------------------------------
INQUIRY_SPECS: list[MethodSpec] = [
    MethodSpec("get_current_date_and_time", expected_type=str),
    MethodSpec("get_n_time_steps"),
    MethodSpec("get_output_interval", expected_type=list),
    MethodSpec(
        "get_time_specs",
        expected_type=tuple,
        shape_check=lambda r, m: len(r) == 2 and isinstance(r[0], list) and isinstance(r[1], str),
    ),

    # --- Geometry: counts and coordinates ----------------------------------
    MethodSpec("get_n_nodes"),
    MethodSpec("get_n_elements"),
    MethodSpec("get_n_subregions"),
    MethodSpec("get_n_layers"),
    MethodSpec(
        "get_node_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_nodes"),
    ),
    MethodSpec(
        "get_node_coordinates",
        expected_type=tuple,
        shape_check=_two_ndarrays_of_len("get_n_nodes"),
    ),
    MethodSpec(
        "get_element_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_elements"),
    ),
    MethodSpec(
        "get_element_areas",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_elements"),
    ),
    MethodSpec(
        "get_subregion_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_subregions"),
    ),
    MethodSpec(
        "get_subregion_names",
        expected_type=list,
        shape_check=lambda r, m: len(r) == m.get_n_subregions() and all(isinstance(s, str) for s in r),
    ),
    MethodSpec(
        "get_subregions_by_element",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_elements"),
    ),
    MethodSpec("get_boundary_nodes", expected_type=pd.DataFrame),

    # --- Streams ----------------------------------------------------------
    MethodSpec("get_n_stream_nodes"),
    MethodSpec("get_n_stream_reaches"),
    MethodSpec("get_n_stream_inflows"),
    MethodSpec(
        "get_stream_node_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_nodes"),
    ),
    MethodSpec(
        "get_stream_reach_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_reaches"),
    ),
    MethodSpec(
        "get_stream_reach_names",
        expected_type=list,
        shape_check=lambda r, m: len(r) == m.get_n_stream_reaches(),
    ),

    # --- Lakes ------------------------------------------------------------
    MethodSpec("get_n_lakes"),
    MethodSpec(
        "get_lake_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_lakes"),
    ),

    # --- Bypasses & diversions -------------------------------------------
    MethodSpec("get_n_bypasses"),
    MethodSpec("get_n_diversions"),
    MethodSpec(
        "get_bypass_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_bypasses"),
    ),
    MethodSpec(
        "get_diversion_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_diversions"),
    ),

    # --- Wells & pumps ----------------------------------------------------
    MethodSpec("get_n_wells"),
    MethodSpec("get_n_element_pumps"),

    # --- Tile drains ------------------------------------------------------
    MethodSpec("get_n_tile_drains"),
    MethodSpec("get_n_tile_drain_hydrographs"),

    # --- Hydrograph type registry ----------------------------------------
    MethodSpec("get_n_hydrograph_types"),
    MethodSpec(
        "get_hydrograph_type_list",
        expected_type=dict,
        shape_check=lambda r, m: len(r) == m.get_n_hydrograph_types(),
    ),

    # --- Subsidence / GW hydrographs --------------------------------------
    MethodSpec("get_n_groundwater_hydrographs"),
    MethodSpec("get_n_subsidence_hydrographs"),
    MethodSpec("get_n_stream_hydrographs"),
    MethodSpec("get_n_small_watersheds"),
    MethodSpec("get_n_ag_crops"),

    # --- Aquifer parameters (no args; values per node × per layer) -------
    MethodSpec("get_aquifer_bottom_elevation", expected_type=np.ndarray),
    MethodSpec("get_aquifer_top_elevation", expected_type=np.ndarray),
    MethodSpec("get_aquifer_horizontal_k", expected_type=np.ndarray),
    MethodSpec("get_aquifer_vertical_k", expected_type=np.ndarray),
    MethodSpec("get_aquifer_specific_storage", expected_type=np.ndarray),
    MethodSpec("get_aquifer_specific_yield", expected_type=np.ndarray),
    MethodSpec("get_aquifer_transmissivity", expected_type=pd.DataFrame),
    MethodSpec("get_aquitard_vertical_k", expected_type=np.ndarray),
    MethodSpec("get_aquifer_parameters", expected_type=tuple),
    MethodSpec(
        "get_ground_surface_elevation",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_nodes"),
    ),

    # --- Element / node detail (no args) ----------------------------------
    MethodSpec("get_element_info", expected_type=(np.ndarray, tuple, pd.DataFrame)),
    MethodSpec("get_element_spatial_info", expected_type=(np.ndarray, tuple, pd.DataFrame)),
    MethodSpec(
        "get_element_pump_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_element_pumps"),
        precondition=_need_count("get_n_element_pumps"),
    ),
    MethodSpec("get_node_info", expected_type=(np.ndarray, tuple, pd.DataFrame)),
    MethodSpec("get_model_stratigraphy", expected_type=(np.ndarray, tuple, pd.DataFrame)),

    # --- Stream topology / flows (no args) -------------------------------
    MethodSpec(
        "get_stream_bottom_elevations",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_nodes"),
    ),
    MethodSpec(
        "get_stream_inflow_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_inflows"),
    ),
    MethodSpec(
        "get_stream_inflow_nodes",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_inflows"),
    ),
    MethodSpec("get_stream_network", expected_type=(np.ndarray, tuple, pd.DataFrame)),
    MethodSpec(
        "get_downstream_node_in_stream_reaches",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_reaches"),
        precondition=_need_count("get_n_stream_reaches"),
    ),
    MethodSpec(
        "get_upstream_nodes_in_stream_reaches",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_reaches"),
        precondition=_need_count("get_n_stream_reaches"),
    ),
    MethodSpec(
        "get_reach_outflow_destination",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_reaches"),
        precondition=_need_count("get_n_stream_reaches"),
    ),
    MethodSpec(
        "get_reach_outflow_destination_types",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_reaches"),
        precondition=_need_count("get_n_stream_reaches"),
    ),

    # --- Hydrograph: groundwater / subsidence / stream / tile drain ------
    MethodSpec(
        "get_groundwater_hydrograph_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_groundwater_hydrographs"),
        precondition=_need_count("get_n_groundwater_hydrographs"),
    ),
    MethodSpec(
        "get_groundwater_hydrograph_names",
        expected_type=list,
        shape_check=lambda r, m: len(r) == m.get_n_groundwater_hydrographs(),
        precondition=_need_count("get_n_groundwater_hydrographs"),
    ),
    MethodSpec(
        "get_groundwater_hydrograph_coordinates",
        expected_type=tuple,
        shape_check=_two_ndarrays_of_len("get_n_groundwater_hydrographs"),
        precondition=_need_count("get_n_groundwater_hydrographs"),
    ),
    MethodSpec(
        "get_groundwater_hydrograph_info",
        expected_type=(np.ndarray, tuple, pd.DataFrame),
        precondition=_need_count("get_n_groundwater_hydrographs"),
    ),
    MethodSpec(
        "get_subsidence_hydrograph_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_subsidence_hydrographs"),
        precondition=_need_count("get_n_subsidence_hydrographs"),
    ),
    MethodSpec(
        "get_subsidence_hydrograph_names",
        expected_type=list,
        shape_check=lambda r, m: len(r) == m.get_n_subsidence_hydrographs(),
        precondition=_need_count("get_n_subsidence_hydrographs"),
    ),
    MethodSpec(
        "get_subsidence_hydrograph_coordinates",
        expected_type=tuple,
        shape_check=_two_ndarrays_of_len("get_n_subsidence_hydrographs"),
        precondition=_need_count("get_n_subsidence_hydrographs"),
    ),
    MethodSpec(
        "get_stream_hydrograph_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_hydrographs"),
        precondition=_need_count("get_n_stream_hydrographs"),
    ),
    MethodSpec(
        "get_stream_hydrograph_names",
        expected_type=list,
        shape_check=lambda r, m: len(r) == m.get_n_stream_hydrographs(),
        precondition=_need_count("get_n_stream_hydrographs"),
    ),
    MethodSpec(
        "get_stream_hydrograph_coordinates",
        expected_type=tuple,
        shape_check=_two_ndarrays_of_len("get_n_stream_hydrographs"),
        precondition=_need_count("get_n_stream_hydrographs"),
    ),
    MethodSpec(
        "get_tile_drain_hydrograph_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_tile_drain_hydrographs"),
        precondition=_need_count("get_n_tile_drain_hydrographs"),
    ),
    MethodSpec(
        "get_tile_drain_hydrograph_coordinates",
        expected_type=tuple,
        shape_check=_two_ndarrays_of_len("get_n_tile_drain_hydrographs"),
        precondition=_need_count("get_n_tile_drain_hydrographs"),
    ),

    # --- Wells / tile drains / small watersheds (no args) ---------------
    MethodSpec(
        "get_well_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_wells"),
        precondition=_need_count("get_n_wells"),
    ),
    MethodSpec(
        "get_well_coordinates",
        expected_type=tuple,
        shape_check=_two_ndarrays_of_len("get_n_wells"),
        precondition=_need_count("get_n_wells"),
    ),
    MethodSpec(
        "get_well_perfs",
        expected_type=(np.ndarray, tuple, pd.DataFrame),
        precondition=_need_count("get_n_wells"),
    ),
    MethodSpec(
        "get_tile_drain_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_tile_drains"),
        precondition=_need_count("get_n_tile_drains"),
    ),
    MethodSpec(
        "get_tile_drain_nodes",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_tile_drains"),
        precondition=_need_count("get_n_tile_drains"),
    ),
    MethodSpec(
        "get_small_watershed_ids",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_small_watersheds"),
        precondition=_need_count("get_n_small_watersheds"),
    ),
    MethodSpec(
        "get_subregion_ag_pumping_average_depth_to_water",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_subregions"),
    ),

    # --- All-defaultable args (use defaults: most accept "all" sentinel) -
    MethodSpec("get_diversion_purpose", expected_type=np.ndarray,
               precondition=_need_count("get_n_diversions")),
    MethodSpec("get_element_pump_purpose", expected_type=np.ndarray,
               precondition=_need_count("get_n_element_pumps")),
    MethodSpec("get_well_pumping_purpose", expected_type=np.ndarray,
               precondition=_need_count("get_n_wells")),
    MethodSpec("get_ag_diversion_supply_shortage_at_origin", expected_type=np.ndarray,
               precondition=_need_count("get_n_diversions")),
    MethodSpec("get_ag_elempump_supply_shortage_at_origin", expected_type=np.ndarray,
               precondition=_need_count("get_n_element_pumps")),
    MethodSpec("get_ag_well_supply_shortage_at_origin", expected_type=np.ndarray,
               precondition=_need_count("get_n_wells")),
    MethodSpec("get_urban_diversion_supply_shortage_at_origin", expected_type=np.ndarray,
               precondition=_need_count("get_n_diversions")),
    MethodSpec("get_urban_elempump_supply_shortage_at_origin", expected_type=np.ndarray,
               precondition=_need_count("get_n_element_pumps")),
    MethodSpec("get_urban_well_supply_shortage_at_origin", expected_type=np.ndarray,
               precondition=_need_count("get_n_wells")),
    MethodSpec("get_bypass_outflows", expected_type=np.ndarray,
               precondition=_need_count("get_n_bypasses")),
    MethodSpec("get_net_bypass_inflows", expected_type=np.ndarray,
               precondition=_need_count("get_n_bypasses")),
    MethodSpec("get_gwheads_all", expected_type=np.ndarray),
    MethodSpec("get_subsidence_all", expected_type=np.ndarray),
    MethodSpec("get_stream_diversion_locations", expected_type=np.ndarray,
               precondition=_need_count("get_n_diversions")),
    MethodSpec(
        "get_stream_flows", expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_nodes"),
    ),
    MethodSpec(
        "get_stream_gain_from_groundwater", expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_nodes"),
    ),
    MethodSpec(
        "get_stream_gain_from_lakes", expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_nodes"),
    ),
    MethodSpec("get_stream_pond_drains", expected_type=np.ndarray),
    MethodSpec("get_stream_rainfall_runoff", expected_type=np.ndarray),
    MethodSpec("get_stream_return_flows", expected_type=np.ndarray),
    MethodSpec("get_stream_riparian_evapotranspiration", expected_type=np.ndarray),
    MethodSpec(
        "get_stream_stages", expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_nodes"),
    ),
    MethodSpec("get_stream_tile_drain_flows", expected_type=np.ndarray),
    MethodSpec("get_stream_tributary_inflows", expected_type=np.ndarray),
    MethodSpec(
        "get_stream_reaches_for_stream_nodes",
        expected_type=np.ndarray,
        shape_check=_ndarray_of_len("get_n_stream_nodes"),
    ),

    # --- Lazy-resolved args from real fixture IDs -----------------------
    MethodSpec(
        "get_subregion_name",
        args=lambda m: (int(m.get_subregion_ids()[0]),),
        expected_type=str,
    ),
    MethodSpec(
        "get_element_config",
        args=lambda m: (int(m.get_element_ids()[0]),),
        expected_type=(np.ndarray, tuple, pd.DataFrame),
    ),
    MethodSpec(
        "get_elements_in_lake",
        args=lambda m: (int(m.get_lake_ids()[0]),),
        expected_type=np.ndarray,
        precondition=_need_count("get_n_lakes"),
    ),
    MethodSpec(
        "get_n_elements_in_lake",
        args=lambda m: (int(m.get_lake_ids()[0]),),
        precondition=_need_count("get_n_lakes"),
    ),
    MethodSpec(
        "get_n_nodes_in_stream_reach",
        args=lambda m: (int(m.get_stream_reach_ids()[0]),),
        precondition=_need_count("get_n_stream_reaches"),
    ),
    MethodSpec(
        "get_n_reaches_upstream_of_reach",
        args=lambda m: (int(m.get_stream_reach_ids()[0]),),
        precondition=_need_count("get_n_stream_reaches"),
    ),
    MethodSpec(
        "get_reaches_upstream_of_reach",
        args=lambda m: (int(m.get_stream_reach_ids()[0]),),
        # Returns None when the reach has no upstream reaches (common
        # for the first reach in topological order). Accept ndarray | None.
        expected_type=(np.ndarray, type(None)),
        precondition=_need_count("get_n_stream_reaches"),
    ),
    MethodSpec(
        "get_stream_reach_groundwater_nodes",
        args=lambda m: (int(m.get_stream_reach_ids()[0]),),
        expected_type=np.ndarray,
        precondition=_need_count("get_n_stream_reaches"),
    ),
    MethodSpec(
        "get_stream_reach_stream_nodes",
        args=lambda m: (int(m.get_stream_reach_ids()[0]),),
        expected_type=np.ndarray,
        precondition=_need_count("get_n_stream_reaches"),
    ),
    MethodSpec(
        "get_n_stream_nodes_upstream_of_stream_node",
        args=lambda m: (int(m.get_stream_node_ids()[0]),),
        precondition=_need_count("get_n_stream_nodes"),
    ),
    MethodSpec(
        "get_stream_nodes_upstream_of_stream_node",
        args=lambda m: (int(m.get_stream_node_ids()[0]),),
        # Returns None for headwater stream nodes with no upstream nodes.
        expected_type=(np.ndarray, type(None)),
        precondition=_need_count("get_n_stream_nodes"),
    ),
    MethodSpec(
        "get_n_rating_table_points",
        args=lambda m: (int(m.get_stream_node_ids()[0]),),
        precondition=_need_count("get_n_stream_nodes"),
    ),
    MethodSpec(
        "get_stream_rating_table",
        args=lambda m: (int(m.get_stream_node_ids()[0]),),
        expected_type=tuple,
        precondition=_need_count("get_n_stream_nodes"),
    ),
    MethodSpec(
        "get_stream_flow_at_location",
        args=lambda m: (int(m.get_stream_node_ids()[0]),),
        expected_type=(int, float, np.integer, np.floating, np.ndarray),
        precondition=_need_count("get_n_stream_nodes"),
    ),
    MethodSpec(
        "get_bypass_nonrecoverable_loss_factor",
        args=lambda m: (int(m.get_bypass_ids()[0]),),
        expected_type=(int, float, np.integer, np.floating),
        precondition=_need_count("get_n_bypasses"),
    ),
    MethodSpec(
        "get_bypass_recoverable_loss_factor",
        args=lambda m: (int(m.get_bypass_ids()[0]),),
        expected_type=(int, float, np.integer, np.floating),
        precondition=_need_count("get_n_bypasses"),
    ),
    MethodSpec(
        "get_bypass_export_nodes",
        args=lambda m: (m.get_bypass_ids().tolist(),),
        expected_type=np.ndarray,
        precondition=_need_count("get_n_bypasses"),
    ),
    MethodSpec(
        "get_bypass_exports_destinations",
        args=lambda m: (m.get_bypass_ids().tolist(),),
        expected_type=(np.ndarray, tuple),
        precondition=_need_count("get_n_bypasses"),
    ),
    MethodSpec(
        "get_stream_diversion_elements",
        args=lambda m: (int(m.get_diversion_ids()[0]),),
        expected_type=np.ndarray,
        precondition=_need_count("get_n_diversions"),
    ),
    MethodSpec(
        "get_stream_diversion_n_elements",
        args=lambda m: (int(m.get_diversion_ids()[0]),),
        precondition=_need_count("get_n_diversions"),
    ),
    MethodSpec(
        "get_groundwater_hydrograph",
        args=lambda m: (int(m.get_groundwater_hydrograph_ids()[0]),),
        expected_type=(np.ndarray, tuple, pd.DataFrame),
        precondition=_need_count("get_n_groundwater_hydrographs"),
    ),
    MethodSpec(
        "get_groundwater_hydrograph_at_node_and_layer",
        args=lambda m: (int(m.get_node_ids()[0]), 1),
        expected_type=(np.ndarray, tuple, pd.DataFrame),
    ),
    MethodSpec(
        "get_subsidence_hydrograph",
        args=lambda m: (int(m.get_subsidence_hydrograph_ids()[0]),),
        expected_type=(np.ndarray, tuple, pd.DataFrame),
        precondition=_need_count("get_n_subsidence_hydrographs"),
    ),
    MethodSpec(
        "get_stream_hydrograph",
        args=lambda m: (int(m.get_stream_hydrograph_ids()[0]),),
        expected_type=(np.ndarray, tuple, pd.DataFrame),
        precondition=_need_count("get_n_stream_hydrographs"),
    ),
]


# ---------------------------------------------------------------------------
# Deferred: methods explicitly NOT covered by the parametrized smoke suite,
# grouped by reason so future contributors can see why.
# ---------------------------------------------------------------------------

DEFERRED: dict[str, list[str]] = {
    # Mutators — exercised in tests/integration/model/test_simulation.py
    # under the @pytest.mark.simulation marker (phase 5 work).
    "mutator": [
        "advance_state",
        "advance_time",
        "delete_inquiry_data_file",
        "print_results",
        "read_timeseries_data",
        "read_timeseries_data_overwrite",
        "restore_pumping_to_read_values",
        "set_preprocessor_path",
        "set_simulation_path",
        "set_supply_adjustment_max_iterations",
        "set_supply_adjustment_tolerance",
        "simulate_all",
        "simulate_for_an_interval",
        "simulate_for_one_timestep",
        "turn_supply_adjustment_on_off",
    ],

    # Methods that take non-trivial polymorphic arguments. Each gets a
    # dedicated test in tests/integration/model/test_polymorphic.py
    # (phase 2 follow-up).
    "polymorphic": [
        "get_actual_stream_diversions_at_some_locations",
        "get_stream_inflows_at_some_locations",
        "get_supply_requirement_ag_elements",
        "get_supply_requirement_ag_subregions",
        "get_supply_requirement_urban_elements",
        "get_supply_requirement_urban_subregions",
    ],

    # Methods needing inputs that don't fit a simple "first ID" shape:
    # XY coordinates that must be inside the mesh, paired stream-node
    # arguments, zone definitions, etc. Each gets a dedicated test that
    # can construct or sample appropriate values.
    "complex_args": [
        "fe_interpolate",                             # (x, y) inside the mesh
        "get_stratigraphy_atXYcoordinate",            # (x, y) inside the mesh
        "is_stream_upstream_node",                    # two stream-node IDs
        "get_zone_ag_pumping_average_depth_to_water", # (elements_list, zones_list)
    ],

    # @staticmethod utilities that take a constructed DataFrame rather
    # than a real model state — not parametrizable from a model fixture.
    # Each gets a dedicated test with synthetic input in a follow-up
    # commit.
    "static_utility": [
        "order_boundary_nodes",
    ],

    # Methods that query simulation state during a run — only valid in
    # is_for_inquiry=0 mode at a specific timestep. Tested via the
    # function-scoped sample_simulation fixture (phase 5), not the
    # session-scoped inquiry fixture.
    "simulation_state": [
        "get_depth_to_water",
        "get_gwheads_foralayer",
    ],

    # Visualization — needs matplotlib backend handling, separate concern.
    "plotting": [
        "plot_elements",
        "plot_nodes",
    ],

    # Lifecycle methods exercised implicitly by the conftest fixtures.
    "lifecycle": [
        "kill",
        "new",
        "is_end_of_simulation",
        "is_model_instantiated",
    ],

}


# ---------------------------------------------------------------------------
# The actual tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize("spec", INQUIRY_SPECS, ids=lambda s: s.name)
def test_method_returns_expected(spec, sample_inquiry):
    """For each MethodSpec: invoke the method and assert return type/shape."""
    if spec.precondition is not None:
        reason = spec.precondition(sample_inquiry)
        if reason:
            pytest.skip(f"{spec.name}: {reason}")

    method = getattr(sample_inquiry, spec.name)
    args = spec.resolve_args(sample_inquiry)
    result = method(*args, **spec.kwargs)

    assert isinstance(result, spec.expected_type), (
        f"{spec.name}: expected {spec.expected_type}, got {type(result).__name__}"
    )

    if spec.shape_check is not None:
        assert spec.shape_check(result, sample_inquiry), (
            f"{spec.name}: shape_check failed for result={result!r}"
        )


def test_specs_cover_all_public_methods():
    """Every public IWFMModel method is either in INQUIRY_SPECS or DEFERRED.

    Adding a new public method to ``pywfm/model.py`` without classifying it
    here will fail this test, forcing a deliberate decision about whether
    the method needs a smoke spec or belongs in a deferred bucket.
    """
    public = {
        n for n in dir(pywfm.IWFMModel)
        if not n.startswith("_") and callable(getattr(pywfm.IWFMModel, n))
    }
    inherited = {
        n for n in dir(IWFMMiscellaneous)
        if not n.startswith("_") and callable(getattr(IWFMMiscellaneous, n))
    }
    own = public - inherited

    spec_names = {s.name for s in INQUIRY_SPECS}
    deferred_names = {n for names in DEFERRED.values() for n in names}
    classified = spec_names | deferred_names

    missing = own - classified
    assert not missing, (
        f"{len(missing)} IWFMModel method(s) are neither in INQUIRY_SPECS nor "
        f"DEFERRED. Add a MethodSpec or place in DEFERRED with a reason: "
        f"{sorted(missing)}"
    )

    extras = classified - own
    assert not extras, (
        f"INQUIRY_SPECS or DEFERRED references method(s) that don't exist on "
        f"IWFMModel (renamed/removed?): {sorted(extras)}"
    )

    # Every name appears in exactly one bucket.
    overlap = spec_names & deferred_names
    assert not overlap, (
        f"Methods classified in both INQUIRY_SPECS and DEFERRED: {sorted(overlap)}"
    )


def test_deferred_buckets_are_disjoint():
    """A method shouldn't be deferred for two different reasons."""
    seen: dict[str, str] = {}
    duplicates: list[tuple[str, str, str]] = []
    for bucket, names in DEFERRED.items():
        for n in names:
            if n in seen:
                duplicates.append((n, seen[n], bucket))
            seen[n] = bucket
    assert not duplicates, f"Methods in multiple DEFERRED buckets: {duplicates}"
