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

    ``shape_check`` receives ``(result, model)`` and returns ``True`` if
    the shape is consistent. Use ``None`` to skip.
    """

    name: str
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    expected_type: Any = (int, np.integer)
    shape_check: Callable[..., bool] | None = None
    skip_if_no_switch: bool = False
    notes: str = ""


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
    MethodSpec("get_boundary_nodes", expected_type=np.ndarray),

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

    # --- Branch-specific (0.2.x stock 2024/2025 only) ---------------------
    MethodSpec(
        "get_current_model_id",
        skip_if_no_switch=True,
        notes="Removed by handle-based kernel rewrite (393e02e+).",
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

    # Methods that take a required scalar id/index — covered by dedicated
    # tests once we know what IDs exist in the SampleModel fixture
    # (test_introspection.py iterates IDs returned by get_X_ids).
    "needs_args": [
        "fe_interpolate",
        "get_ag_diversion_supply_shortage_at_origin",
        "get_ag_elempump_supply_shortage_at_origin",
        "get_ag_well_supply_shortage_at_origin",
        "get_aquifer_bottom_elevation",
        "get_aquifer_horizontal_k",
        "get_aquifer_parameters",
        "get_aquifer_specific_storage",
        "get_aquifer_specific_yield",
        "get_aquifer_top_elevation",
        "get_aquifer_transmissivity",
        "get_aquifer_vertical_k",
        "get_aquitard_vertical_k",
        "get_bypass_export_nodes",
        "get_bypass_exports_destinations",
        "get_bypass_nonrecoverable_loss_factor",
        "get_bypass_outflows",
        "get_bypass_recoverable_loss_factor",
        "get_depth_to_water",
        "get_diversion_purpose",
        "get_downstream_node_in_stream_reaches",
        "get_element_config",
        "get_element_info",
        "get_element_pump_ids",
        "get_element_pump_purpose",
        "get_element_spatial_info",
        "get_elements_in_lake",
        "get_ground_surface_elevation",
        "get_groundwater_hydrograph",
        "get_groundwater_hydrograph_at_node_and_layer",
        "get_groundwater_hydrograph_coordinates",
        "get_groundwater_hydrograph_ids",
        "get_groundwater_hydrograph_info",
        "get_groundwater_hydrograph_names",
        "get_gwheads_all",
        "get_gwheads_foralayer",
        "get_model_stratigraphy",
        "get_n_elements_in_lake",
        "get_n_nodes_in_stream_reach",
        "get_n_rating_table_points",
        "get_n_reaches_upstream_of_reach",
        "get_n_stream_nodes_upstream_of_stream_node",
        "get_net_bypass_inflows",
        "get_node_info",
        "get_reach_outflow_destination",
        "get_reach_outflow_destination_types",
        "get_reaches_upstream_of_reach",
        "get_small_watershed_ids",
        "get_stratigraphy_atXYcoordinate",
        "get_stream_bottom_elevations",
        "get_stream_diversion_elements",
        "get_stream_diversion_locations",
        "get_stream_diversion_n_elements",
        "get_stream_flow_at_location",
        "get_stream_flows",
        "get_stream_gain_from_groundwater",
        "get_stream_gain_from_lakes",
        "get_stream_hydrograph",
        "get_stream_hydrograph_coordinates",
        "get_stream_hydrograph_ids",
        "get_stream_hydrograph_names",
        "get_stream_inflow_ids",
        "get_stream_inflow_nodes",
        "get_stream_network",
        "get_stream_nodes_upstream_of_stream_node",
        "get_stream_pond_drains",
        "get_stream_rainfall_runoff",
        "get_stream_rating_table",
        "get_stream_reach_groundwater_nodes",
        "get_stream_reach_stream_nodes",
        "get_stream_reaches_for_stream_nodes",
        "get_stream_return_flows",
        "get_stream_riparian_evapotranspiration",
        "get_stream_stages",
        "get_stream_tile_drain_flows",
        "get_stream_tributary_inflows",
        "get_subregion_ag_pumping_average_depth_to_water",
        "get_subregion_name",
        "get_subsidence_all",
        "get_subsidence_hydrograph",
        "get_subsidence_hydrograph_coordinates",
        "get_subsidence_hydrograph_ids",
        "get_subsidence_hydrograph_names",
        "get_tile_drain_hydrograph_coordinates",
        "get_tile_drain_hydrograph_ids",
        "get_tile_drain_ids",
        "get_tile_drain_nodes",
        "get_upstream_nodes_in_stream_reaches",
        "get_urban_diversion_supply_shortage_at_origin",
        "get_urban_elempump_supply_shortage_at_origin",
        "get_urban_well_supply_shortage_at_origin",
        "get_well_coordinates",
        "get_well_ids",
        "get_well_perfs",
        "get_well_pumping_purpose",
        "get_zone_ag_pumping_average_depth_to_water",
        "is_stream_upstream_node",
        "order_boundary_nodes",
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

    # Branch-specific multi-instance: present on 0.2.x with stock 2024/2025
    # DLLs, removed from 0.3.x. Covered separately in test_multi_instance.
    "branch_specific": [
        "switch_active_model",
    ],
}


# ---------------------------------------------------------------------------
# The actual tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize("spec", INQUIRY_SPECS, ids=lambda s: s.name)
def test_method_returns_expected(spec, sample_inquiry, dll_has_switch):
    """For each MethodSpec: invoke the method and assert return type/shape."""
    if spec.skip_if_no_switch and not dll_has_switch:
        pytest.skip(f"{spec.name} requires IW_Model_Switch")

    method = getattr(sample_inquiry, spec.name)
    result = method(*spec.args, **spec.kwargs)

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
