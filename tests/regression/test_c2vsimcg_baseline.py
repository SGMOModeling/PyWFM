"""Regression baseline for C2VSimCG (Coarse Grid).

Pins ~10 critical numerical values to a golden JSON file. Mirrors
``test_sample_model_baseline.py`` but for the production-scale model.
Skipped by default — gated on ``--runslow`` and on the user having
populated C2VSimCG's Results/ via a prior sim run.

To regenerate the baseline (after a deliberate input change or a new
DLL build):

    pytest tests/regression --runslow --update-baselines

Baselines are stored as
``tests/regression/data/c2vsimcg_<dll_version>.json`` so each
matching DLL/kernel combo has its own pinned set; tests skip with a
clear message when no matching baseline exists.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pytest

import pywfm

BASELINE_DIR = Path(__file__).parent / "data"


@dataclass
class C2VRegressionSpec:
    """Same shape as the SampleModel RegressionSpec — separated only to
    keep the spec lists distinct so a SampleModel-only baseline regen
    doesn't accidentally overwrite the C2VSimCG one."""

    name: str
    extract: Callable[[Any], Any]
    tolerance: float = 0.0
    requires_procedure: tuple = ()


def _to_py(v):
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, np.ndarray):
        return v.tolist()
    return v


# Pinned values for C2VSimCG. Smaller list than SampleModel — for a
# production-scale model, a few high-level dimensions and aggregates
# catch most kinds of regression. Per-element values aren't pinned
# (too brittle to baseline against multi-GB output data).
C2VSIM_SPECS: list[C2VRegressionSpec] = [
    C2VRegressionSpec("n_nodes",        lambda m: m.get_n_nodes()),
    C2VRegressionSpec("n_elements",     lambda m: m.get_n_elements()),
    C2VRegressionSpec("n_layers",       lambda m: m.get_n_layers()),
    C2VRegressionSpec("n_subregions",   lambda m: m.get_n_subregions()),
    C2VRegressionSpec("n_time_steps",   lambda m: m.get_n_time_steps()),
    C2VRegressionSpec("n_stream_nodes", lambda m: m.get_n_stream_nodes()),
    C2VRegressionSpec("n_stream_reaches", lambda m: m.get_n_stream_reaches()),
    C2VRegressionSpec("n_lakes",        lambda m: m.get_n_lakes()),
    C2VRegressionSpec("first_node_id",  lambda m: int(m.get_node_ids()[0])),
    C2VRegressionSpec("last_node_id",   lambda m: int(m.get_node_ids()[-1])),
    C2VRegressionSpec("first_node_x",   lambda m: float(m.get_node_coordinates()[0][0]),
                                        tolerance=1e-6),
    C2VRegressionSpec("first_node_y",   lambda m: float(m.get_node_coordinates()[1][0]),
                                        tolerance=1e-6),
    C2VRegressionSpec("total_element_area", lambda m: float(m.get_element_areas().sum()),
                                        tolerance=1.0,
                                        requires_procedure=("IW_Model_GetElementAreas",)),
]


def _baseline_path(dll_version: str) -> Path:
    short = dll_version.split("-")[0]
    return BASELINE_DIR / f"c2vsimcg_{short}.json"


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


@pytest.fixture(scope="session")
def _c2vsim_baseline_state(dll_version, request):
    path = _baseline_path(dll_version)
    data = _load_baseline(path)
    update_mode = request.config.getoption("--update-baselines")
    captured: dict = {} if update_mode else None

    yield {"path": path, "data": data, "captured": captured, "update": update_mode}

    if update_mode and captured is not None:
        captured["_dll_version"] = dll_version
        _save_baseline(path, captured)


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.parametrize("spec", C2VSIM_SPECS, ids=lambda s: s.name)
def test_c2vsim_value_matches_baseline(spec, c2vsimcg_inquiry, _c2vsim_baseline_state):
    """For each C2VRegressionSpec: extract value and compare to baseline."""
    missing = [
        p for p in spec.requires_procedure
        if not hasattr(pywfm.IWFM_API, p)
    ]
    if missing:
        pytest.skip(f"{spec.name}: DLL doesn't export {missing}")

    value = _to_py(spec.extract(c2vsimcg_inquiry))

    if _c2vsim_baseline_state["update"]:
        _c2vsim_baseline_state["captured"][spec.name] = value
        return

    if not _c2vsim_baseline_state["data"]:
        pytest.skip(
            f"no C2VSimCG baseline at {_c2vsim_baseline_state['path']}. "
            "Run `pytest tests/regression --runslow --update-baselines` "
            "to create one."
        )

    if spec.name not in _c2vsim_baseline_state["data"]:
        pytest.skip(
            f"baseline at {_c2vsim_baseline_state['path']} has no entry for "
            f"{spec.name!r}. Run --update-baselines to refresh."
        )

    expected = _c2vsim_baseline_state["data"][spec.name]
    if isinstance(value, float) or isinstance(expected, float):
        diff = abs(value - expected)
        assert diff <= spec.tolerance, (
            f"{spec.name}: live={value} baseline={expected} diff={diff} "
            f"tolerance={spec.tolerance}"
        )
    else:
        assert value == expected, f"{spec.name}: live={value!r} baseline={expected!r}"
