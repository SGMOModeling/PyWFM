"""Regression baseline for the SampleModel.

Pins ~20 critical numerical values to a golden JSON file keyed by the
loaded DLL version. The test compares the live model's values against
the baseline; mismatches fail with a diff and a hint about how to
regenerate the file.

To regenerate the baseline (e.g. after a deliberate change to inputs
or after vendoring a new DLL build), run::

    pytest tests/regression --update-baselines

That mode captures values into the JSON instead of comparing — you'll
see PASSED for every spec and the file is rewritten in place. Review
the resulting diff before committing.

Baseline files are stored as ``tests/regression/data/sample_model_<dll_version>.json``
so each DLL variant in the conda matrix has its own pinned set; tests
gracefully skip when no matching baseline exists.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pytest

BASELINE_DIR = Path(__file__).parent / "data"


# ---------------------------------------------------------------------------
# Spec definitions
# ---------------------------------------------------------------------------


@dataclass
class RegressionSpec:
    """One pinnable value extracted from a live model.

    ``tolerance`` is absolute. Use 0 for ints; ~1e-9 or smaller for
    floats from input files (which are read verbatim, so should be
    exact within the float-format precision of the input file).
    """

    name: str
    extract: Callable[[Any], Any]
    tolerance: float = 0.0


# Helper: convert ndarray scalar to Python scalar for JSON serialization
def _to_py(v):
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, np.ndarray):
        return v.tolist()
    return v


# Specs covering the most stable, physically meaningful values.
# Edit this list to add/remove pinned values; the baseline JSON updates
# via the --update-baselines CLI flag.
SAMPLE_SPECS: list[RegressionSpec] = [
    # --- Counts (exact integers) ---
    RegressionSpec("n_nodes",                   lambda m: m.get_n_nodes()),
    RegressionSpec("n_elements",                lambda m: m.get_n_elements()),
    RegressionSpec("n_layers",                  lambda m: m.get_n_layers()),
    RegressionSpec("n_subregions",              lambda m: m.get_n_subregions()),
    RegressionSpec("n_time_steps",              lambda m: m.get_n_time_steps()),
    RegressionSpec("n_stream_nodes",            lambda m: m.get_n_stream_nodes()),
    RegressionSpec("n_stream_reaches",          lambda m: m.get_n_stream_reaches()),
    RegressionSpec("n_stream_inflows",          lambda m: m.get_n_stream_inflows()),
    RegressionSpec("n_lakes",                   lambda m: m.get_n_lakes()),
    RegressionSpec("n_bypasses",                lambda m: m.get_n_bypasses()),
    RegressionSpec("n_diversions",              lambda m: m.get_n_diversions()),
    RegressionSpec("n_groundwater_hydrographs", lambda m: m.get_n_groundwater_hydrographs()),
    RegressionSpec("n_hydrograph_types",        lambda m: m.get_n_hydrograph_types()),

    # --- ID array endpoints (exact ints) ---
    RegressionSpec("first_node_id",             lambda m: int(m.get_node_ids()[0])),
    RegressionSpec("last_node_id",              lambda m: int(m.get_node_ids()[-1])),
    RegressionSpec("first_element_id",          lambda m: int(m.get_element_ids()[0])),

    # --- First-node coordinates (read directly from NodeXY.dat) ---
    RegressionSpec("first_node_x",              lambda m: float(m.get_node_coordinates()[0][0]),
                                                tolerance=1e-9),
    RegressionSpec("first_node_y",              lambda m: float(m.get_node_coordinates()[1][0]),
                                                tolerance=1e-9),

    # --- Stratigraphy (read from Strata.dat) ---
    RegressionSpec("aquifer_top_l1_n1",         lambda m: float(m.get_aquifer_top_elevation()[0, 0]),
                                                tolerance=1e-9),
    RegressionSpec("aquifer_bot_l1_n1",         lambda m: float(m.get_aquifer_bottom_elevation()[0, 0]),
                                                tolerance=1e-9),
    RegressionSpec("ground_surface_n1",         lambda m: float(m.get_ground_surface_elevation()[0]),
                                                tolerance=1e-9),
    RegressionSpec("horizontal_k_l1_n1",        lambda m: float(m.get_aquifer_horizontal_k()[0, 0]),
                                                tolerance=1e-9),

    # --- Geometry sums (derived; should be exact within rounding) ---
    RegressionSpec("total_element_area",        lambda m: float(m.get_element_areas().sum()),
                                                tolerance=1e-6),
]


# ---------------------------------------------------------------------------
# Baseline file resolution
# ---------------------------------------------------------------------------


def _baseline_path(dll_version: str) -> Path:
    """Strip a build-hash suffix (e.g. '2025.0.1747-054223d4' → '2025.0.1747')
    so the same baseline applies to all builds of the same numbered version.
    """
    short = dll_version.split("-")[0]
    return BASELINE_DIR / f"sample_model_{short}.json"


def _load_baseline(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r") as f:
        return json.load(f)


def _save_baseline(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def _baseline_state(dll_version, request):
    """Loads the baseline file at session start; on session teardown, writes
    it back if --update-baselines was passed."""
    path = _baseline_path(dll_version)
    data = _load_baseline(path)
    update_mode = request.config.getoption("--update-baselines")
    captured: dict = {} if update_mode else None

    yield {"path": path, "data": data, "captured": captured, "update": update_mode}

    if update_mode and captured is not None:
        # Only persist if every spec produced a value (i.e. tests didn't fail
        # mid-extract). The captured dict is built up by the test runner.
        captured["_dll_version"] = dll_version
        _save_baseline(path, captured)


@pytest.mark.regression
@pytest.mark.parametrize("spec", SAMPLE_SPECS, ids=lambda s: s.name)
def test_value_matches_baseline(spec, sample_inquiry, _baseline_state):
    """For each RegressionSpec: extract value and compare to baseline."""
    value = _to_py(spec.extract(sample_inquiry))

    if _baseline_state["update"]:
        # Capture mode — record value, don't compare
        _baseline_state["captured"][spec.name] = value
        return

    if not _baseline_state["data"]:
        pytest.skip(
            f"no baseline at {_baseline_state['path']}. "
            "Run `pytest tests/regression --update-baselines` to create one."
        )

    if spec.name not in _baseline_state["data"]:
        pytest.skip(
            f"baseline at {_baseline_state['path']} has no entry for {spec.name!r}. "
            "Run `pytest tests/regression --update-baselines` to refresh."
        )

    expected = _baseline_state["data"][spec.name]

    if isinstance(value, float) or isinstance(expected, float):
        diff = abs(value - expected)
        assert diff <= spec.tolerance, (
            f"{spec.name}: live={value} baseline={expected} diff={diff} "
            f"tolerance={spec.tolerance}"
        )
    else:
        assert value == expected, f"{spec.name}: live={value!r} baseline={expected!r}"
