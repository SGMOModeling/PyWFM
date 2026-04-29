"""Shared fixtures and pytest configuration for the pywfm test suite.

The fixtures here are the foundation for every integration and regression
test. Key design points:

- ``sample_dir`` picks v2015/ or v2025/ at session start based on the
  loaded DLL's IWFM major version. Both SampleModels are vendored under
  ``tests/data/sample_model/`` because the file format genuinely differs
  between 2015 and 2024+ (e.g. Element.dat region naming, Simulation_MAIN.IN
  unit-12 file slot and STOPCVL parameter).
- ``_ensure_results`` runs the simulation once per session if the Results/
  directory is empty, since IWFMBudget/IWFMZBudget tests need .hdf outputs
  that aren't vendored.
- ``_SilentLog`` is a subclass of IWFMModel that no-ops set_log_file. The
  IWFM DefaultLogger is a process-wide singleton, so any second-or-later
  instance in the same process must avoid calling set_log_file. This is
  the pattern that test_multi_instance.py uses on the 0.3.x line.
"""
import os
from pathlib import Path

import pytest

import pywfm
from pywfm.misc import IWFMMiscellaneous

REPO = Path(__file__).resolve().parent.parent
SAMPLE_DIR = REPO / "tests" / "data" / "sample_model"


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true",
        help="run slow tests (e.g. C2VSimCG)",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        return
    skip = pytest.mark.skip(reason="needs --runslow")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip)


class _SilentLog(pywfm.IWFMModel):
    """IWFMModel subclass that no-ops set_log_file.

    IWFM's DefaultLogger is a process-wide singleton — only one
    set_log_file call is allowed per process. Use this for any
    second-or-later instance you create in a test.
    """

    def set_log_file(self, file_name):
        pass


@pytest.fixture(scope="session")
def dll_has_switch():
    """True when the loaded DLL exports IW_Model_Switch.

    On 0.2.x: True for stock 2024/2025 DLLs, False for 2015-series.
    On 0.3.x: always False (the kernel rewrite removed the symbol).
    Drives skip logic for tests that exercise the Switch-based
    multi-instance pattern.
    """
    return hasattr(pywfm.IWFM_API, "IW_Model_Switch")


@pytest.fixture(scope="session")
def dll_version():
    """Returns the loaded DLL's IWFM core version string (e.g. '2025.0.1747')."""
    misc = IWFMMiscellaneous()
    v = misc.get_version()
    return v.get("IWFM Core") or v["IWFM"]


@pytest.fixture(scope="session")
def sample_dir(dll_version):
    """Resolves to v2015/ or v2025/ based on the loaded DLL major version.

    2024.x and 2025.x DLLs use v2025 (post-2015 input format).
    2015.x DLLs use v2015.
    """
    major = int(dll_version.split(".")[0])
    chosen = SAMPLE_DIR / ("v2025" if major >= 2024 else "v2015")
    if not (chosen / "Preprocessor" / "PreProcessor_MAIN.IN").exists():
        pytest.skip(f"SampleModel not vendored at {chosen}")
    return chosen


@pytest.fixture(scope="session")
def sample_pp_sim(sample_dir):
    return (
        sample_dir / "Preprocessor" / "PreProcessor_MAIN.IN",
        sample_dir / "Simulation" / "Simulation_MAIN.IN",
    )


@pytest.fixture(scope="session")
def _ensure_results(sample_dir, sample_pp_sim):
    """Runs the SampleModel simulation once per session if Results/ is empty.

    IWFMBudget/IWFMZBudget need GW.hdf and GW_ZBud.hdf in Results/, which
    are produced by simulate_all() but not vendored (.gitignore excludes
    Results/). Running once per session amortizes the cost.
    """
    pp, sim = sample_pp_sim
    results_dir = sample_dir / "Results"
    if (results_dir / "GW.hdf").exists():
        return
    results_dir.mkdir(exist_ok=True)
    cwd = os.getcwd()
    os.chdir(sample_dir / "Simulation")
    try:
        m = pywfm.IWFMModel(str(pp), str(sim), is_for_inquiry=0)
        m.simulate_all()
        m.kill()
    finally:
        os.chdir(cwd)


@pytest.fixture(scope="session")
def sample_inquiry(sample_dir, sample_pp_sim, _ensure_results):
    """Long-lived read-only IWFMModel — most integration tests share this."""
    pp, sim = sample_pp_sim
    cwd = os.getcwd()
    os.chdir(sample_dir / "Simulation")
    try:
        m = pywfm.IWFMModel(str(pp), str(sim), is_for_inquiry=1)
        yield m
        m.kill()
    finally:
        os.chdir(cwd)


@pytest.fixture
def sample_simulation(sample_dir, sample_pp_sim, _ensure_results):
    """Function-scoped fresh IWFMModel for tests that mutate state.

    Uses _SilentLog so DefaultLogger isn't tripped after sample_inquiry
    has already configured logging. Passes delete_inquiry_data_file=False
    for the same kernel-state-bookkeeping reason.
    """
    pp, sim = sample_pp_sim
    cwd = os.getcwd()
    os.chdir(sample_dir / "Simulation")
    try:
        m = _SilentLog(
            str(pp), str(sim),
            is_for_inquiry=0,
            delete_inquiry_data_file=False,
        )
        yield m
        m.kill()
    finally:
        os.chdir(cwd)


@pytest.fixture(scope="session")
def sample_gw_budget(sample_dir, _ensure_results):
    """IWFMBudget against SampleModel/Results/GW.hdf.

    IW_Budget_OpenFile is process-stateful (one open file per process),
    so this is session-scoped and IWFMBudget tests must run sequentially
    within a worker.
    """
    b = pywfm.IWFMBudget(str(sample_dir / "Results" / "GW.hdf"))
    yield b
    b.close_budget_file()


@pytest.fixture(scope="session")
def sample_gw_zbudget(sample_dir, _ensure_results):
    """IWFMZBudget against SampleModel/Results/GW_ZBud.hdf with zones loaded.

    Most ZBudget queries are zone-keyed (``get_n_zones``, ``get_zone_list``,
    ``get_values_for_a_zone``), so the fixture eagerly loads the vendored
    zone definition file (``ZBudget/ZoneDef_SRs.dat``) via
    ``generate_zone_list_from_file``. Tests that don't need zones still
    work — having zones loaded is harmless to them.
    """
    z = pywfm.IWFMZBudget(str(sample_dir / "Results" / "GW_ZBud.hdf"))
    zone_def = sample_dir / "ZBudget" / "ZoneDef_SRs.dat"
    if zone_def.exists():
        z.generate_zone_list_from_file(str(zone_def))
    yield z
    z.close_zbudget_file()


@pytest.fixture(scope="session")
def c2vsimcg_path():
    """Resolves to the C2VSimCG model directory.

    Set PYWFM_C2VSIMCG to override the default OneDrive path. Tests using
    this fixture should also be marked @pytest.mark.slow so they're
    skipped unless --runslow is passed.
    """
    env = os.environ.get(
        "PYWFM_C2VSIMCG",
        r"C:\Users\hatch\OneDrive\Desktop\c2vsimcg\C2VSimCG_v2025_WY1974-2015",
    )
    p = Path(env)
    if not (p / "Preprocessor").exists():
        pytest.skip(f"C2VSimCG not found at {p}; set PYWFM_C2VSIMCG")
    return p


@pytest.fixture(scope="session")
def c2vsimcg_inquiry(c2vsimcg_path):
    """Long-lived read-only IWFMModel against C2VSimCG."""
    pp = next(c2vsimcg_path.glob("Preprocessor/*MAIN*.IN"))
    sim = next(c2vsimcg_path.glob("Simulation/*MAIN*.IN"))
    cwd = os.getcwd()
    os.chdir(c2vsimcg_path / "Simulation")
    try:
        m = pywfm.IWFMModel(str(pp), str(sim), is_for_inquiry=1)
        yield m
        m.kill()
    finally:
        os.chdir(cwd)
