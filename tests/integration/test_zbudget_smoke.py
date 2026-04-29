"""Parametrized smoke tests for IWFMZBudget.

The ``sample_gw_zbudget`` fixture in conftest.py opens
SampleModel/Results/GW_ZBud.hdf and eagerly loads zones via
``generate_zone_list_from_file`` from the vendored
``ZBudget/ZoneDef_SRs.dat``. Most queries here are zone-keyed.

Like IWFMBudget, the underlying kernel state is process-stateful — one
open zbudget file per process — so tests run sequentially within a
worker.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import pandas as pd
import pytest

import pywfm
from pywfm.misc import IWFMMiscellaneous


@dataclass
class ZBudgetSpec:
    name: str
    args: tuple | Callable[..., tuple] = ()
    kwargs: dict = field(default_factory=dict)
    expected_type: Any = (int, np.integer)
    shape_check: Callable[..., bool] | None = None
    notes: str = ""

    def resolve_args(self, zb) -> tuple:
        return self.args(zb) if callable(self.args) else self.args


def _first_zone(zb) -> tuple:
    """Lazily resolve the first zone ID from the loaded zone list."""
    zones = zb.get_zone_list()
    return (int(zones[0]),)


ZBUDGET_SPECS: list[ZBudgetSpec] = [
    # --- Counts and basic introspection ---
    ZBudgetSpec("get_n_zones"),
    ZBudgetSpec("get_n_time_steps"),
    ZBudgetSpec("get_n_title_lines"),

    # --- Time spec ---
    ZBudgetSpec(
        "get_time_specs",
        expected_type=tuple,
        shape_check=lambda r, zb: len(r) == 2 and isinstance(r[0], list) and isinstance(r[1], str),
    ),

    # --- Zone introspection ---
    ZBudgetSpec(
        "get_zone_list",
        expected_type=np.ndarray,
        shape_check=lambda r, zb: r.shape == (zb.get_n_zones(),),
    ),
    ZBudgetSpec(
        "get_zone_names",
        expected_type=list,
        shape_check=lambda r, zb: len(r) == zb.get_n_zones(),
    ),

    # --- Zone-keyed queries (use first zone from get_zone_list) ---
    ZBudgetSpec(
        "get_column_headers_for_a_zone",
        args=_first_zone,
        expected_type=(list, tuple, np.ndarray),
    ),
    ZBudgetSpec(
        "get_title_lines",
        args=_first_zone,
        expected_type=list,
        shape_check=lambda r, zb: len(r) == zb.get_n_title_lines(),
    ),
    ZBudgetSpec(
        "get_values_for_a_zone",
        args=_first_zone,
        expected_type=pd.DataFrame,
        shape_check=lambda r, zb: len(r) == zb.get_n_time_steps(),
    ),

    # --- Multi-zone interval query (defaults to 'all') ---
    ZBudgetSpec(
        "get_values_for_some_zones_for_an_interval",
        expected_type=pd.DataFrame,
    ),
]


DEFERRED: dict[str, list[str]] = {
    # Lifecycle: exercised by fixture teardown via conftest.
    "lifecycle": [
        "close_zbudget_file",
    ],
    # Setup: called by the conftest fixture before any test runs. Calling
    # it again would reset zone state and is treated as a setup primitive.
    "setup": [
        "generate_zone_list_from_file",
    ],
}


@pytest.mark.integration
@pytest.mark.parametrize("spec", ZBUDGET_SPECS, ids=lambda s: s.name)
def test_zbudget_method_returns_expected(spec, sample_gw_zbudget):
    """For each ZBudgetSpec: invoke the method and assert return type/shape."""
    method = getattr(sample_gw_zbudget, spec.name)
    args = spec.resolve_args(sample_gw_zbudget)
    result = method(*args, **spec.kwargs)

    assert isinstance(result, spec.expected_type), (
        f"{spec.name}: expected {spec.expected_type}, got {type(result).__name__}"
    )
    if spec.shape_check is not None:
        assert spec.shape_check(result, sample_gw_zbudget), (
            f"{spec.name}: shape_check failed for result type {type(result).__name__}"
        )


def test_zbudget_specs_cover_all_public_methods():
    """Every public IWFMZBudget method is in ZBUDGET_SPECS or DEFERRED."""
    public = {
        n for n in dir(pywfm.IWFMZBudget)
        if not n.startswith("_") and callable(getattr(pywfm.IWFMZBudget, n))
    }
    inherited = {
        n for n in dir(IWFMMiscellaneous)
        if not n.startswith("_") and callable(getattr(IWFMMiscellaneous, n))
    }
    own = public - inherited

    spec_names = {s.name for s in ZBUDGET_SPECS}
    deferred_names = {n for names in DEFERRED.values() for n in names}
    classified = spec_names | deferred_names

    missing = own - classified
    assert not missing, (
        f"{len(missing)} IWFMZBudget method(s) need a ZBudgetSpec or "
        f"DEFERRED entry: {sorted(missing)}"
    )
    extras = classified - own
    assert not extras, (
        f"ZBUDGET_SPECS or DEFERRED references methods that don't exist on "
        f"IWFMZBudget: {sorted(extras)}"
    )
