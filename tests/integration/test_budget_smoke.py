"""Parametrized smoke tests for IWFMBudget.

Covers all 12 public methods on IWFMBudget. Most are location-keyed —
``location_id`` is the IWFM term for a subregion or other budget unit
(e.g. lake, small watershed). The lazy-resolved args use the first
location ID returned by ``get_n_locations()`` so tests adapt to whatever
budget HDF file is being exercised.

The IWFMBudget kernel state is process-stateful (one open file per
process), so tests within a worker run sequentially. The
``sample_gw_budget`` session-scoped fixture in conftest.py opens
SampleModel/Results/GW.hdf for the entire session.
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
class BudgetSpec:
    """Same shape as the IWFMModel MethodSpec, but for IWFMBudget."""

    name: str
    args: tuple | Callable[..., tuple] = ()
    kwargs: dict = field(default_factory=dict)
    expected_type: Any = (int, np.integer)
    shape_check: Callable[..., bool] | None = None
    notes: str = ""

    def resolve_args(self, budget) -> tuple:
        return self.args(budget) if callable(self.args) else self.args


def _ndarray_or_list_of_len(getter: str) -> Callable:
    def check(result, b):
        n = getattr(b, getter)()
        return (
            (isinstance(result, np.ndarray) and result.shape == (n,))
            or (isinstance(result, (list, tuple)) and len(result) == n)
        )
    return check


# Most IWFMBudget methods that take a location_id use the first valid
# location. ``get_n_locations()`` is the count; locations are 1-indexed.
def _first_location(b) -> tuple:
    return (1,)


BUDGET_SPECS: list[BudgetSpec] = [
    # --- Counts and basic introspection ---
    BudgetSpec("get_n_locations"),
    BudgetSpec("get_n_time_steps"),
    BudgetSpec("get_n_title_lines"),
    BudgetSpec("get_title_length"),

    # --- Names and time spec (no args) ---
    BudgetSpec(
        "get_location_names",
        expected_type=list,
        shape_check=_ndarray_or_list_of_len("get_n_locations"),
    ),
    BudgetSpec(
        "get_time_specs",
        expected_type=tuple,
        shape_check=lambda r, b: len(r) == 2 and isinstance(r[0], list) and isinstance(r[1], str),
    ),

    # --- Location-keyed (use location 1) ---
    BudgetSpec("get_n_columns", args=_first_location),
    BudgetSpec(
        "get_column_headers",
        args=_first_location,
        expected_type=(list, tuple, np.ndarray),
    ),
    BudgetSpec(
        "get_title_lines",
        args=_first_location,
        expected_type=list,
        shape_check=lambda r, b: len(r) == b.get_n_title_lines(),
    ),
    BudgetSpec(
        "get_values",
        args=_first_location,
        expected_type=pd.DataFrame,
        shape_check=lambda r, b: len(r) == b.get_n_time_steps(),
    ),
    BudgetSpec(
        "get_values_for_a_column",
        args=lambda b: (1, _first_column_name_for_loc1(b)),
        expected_type=pd.DataFrame,
        # Row count may differ from n_time_steps if the column has its
        # own output schedule (some columns are aggregated to monthly
        # or annual). Just assert non-empty.
        shape_check=lambda r, b: len(r) > 0,
    ),
]


def _first_column_name_for_loc1(b):
    """Resolve the first column header of location 1 — needed by
    get_values_for_a_column."""
    headers = b.get_column_headers(1)
    # get_column_headers may return a tuple (headers, units) or a list of strings
    if isinstance(headers, tuple) and len(headers) >= 1:
        first = headers[0]
        if isinstance(first, (list, tuple, np.ndarray)) and len(first):
            # Skip the time/date column (typically at index 0 or 1) and take a real column name
            return first[1] if len(first) > 1 else first[0]
        return first
    return headers[0] if hasattr(headers, "__getitem__") else headers


DEFERRED: dict[str, list[str]] = {
    # Lifecycle: exercised by fixture teardown via conftest.
    "lifecycle": [
        "close_budget_file",
    ],
}


@pytest.mark.integration
@pytest.mark.parametrize("spec", BUDGET_SPECS, ids=lambda s: s.name)
def test_budget_method_returns_expected(spec, sample_gw_budget):
    """For each BudgetSpec: invoke the method and assert return type/shape."""
    method = getattr(sample_gw_budget, spec.name)
    args = spec.resolve_args(sample_gw_budget)
    result = method(*args, **spec.kwargs)

    assert isinstance(result, spec.expected_type), (
        f"{spec.name}: expected {spec.expected_type}, got {type(result).__name__}"
    )
    if spec.shape_check is not None:
        assert spec.shape_check(result, sample_gw_budget), (
            f"{spec.name}: shape_check failed for result type {type(result).__name__}"
        )


def test_budget_specs_cover_all_public_methods():
    """Every public IWFMBudget method is in BUDGET_SPECS or DEFERRED."""
    public = {
        n for n in dir(pywfm.IWFMBudget)
        if not n.startswith("_") and callable(getattr(pywfm.IWFMBudget, n))
    }
    inherited = {
        n for n in dir(IWFMMiscellaneous)
        if not n.startswith("_") and callable(getattr(IWFMMiscellaneous, n))
    }
    own = public - inherited

    spec_names = {s.name for s in BUDGET_SPECS}
    deferred_names = {n for names in DEFERRED.values() for n in names}
    classified = spec_names | deferred_names

    missing = own - classified
    assert not missing, (
        f"{len(missing)} IWFMBudget method(s) need a BudgetSpec or DEFERRED "
        f"entry: {sorted(missing)}"
    )
    extras = classified - own
    assert not extras, (
        f"BUDGET_SPECS or DEFERRED references methods that don't exist on "
        f"IWFMBudget: {sorted(extras)}"
    )
