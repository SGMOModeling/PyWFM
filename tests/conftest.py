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
    parser.addoption(
        "--runsim", action="store_true",
        help="run simulation-mode tests — they can't coexist with inquiry-"
             "mode tests in the same pytest session (kernel singleton state), "
             "so they're skipped by default. Use a dedicated pytest invocation: "
             "`pytest --runsim tests/integration/model/test_simulation.py`",
    )
    parser.addoption(
        "--update-baselines", action="store_true",
        help="capture regression values into the baseline JSON instead of "
             "comparing — used to refresh tests/regression/data/*.json",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--runslow"):
        skip = pytest.mark.skip(reason="needs --runslow")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip)
    if not config.getoption("--runsim"):
        skip = pytest.mark.skip(reason="needs --runsim")
        for item in items:
            if "simulation" in item.keywords:
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
def dll_version():
    """Returns the loaded DLL's IWFM core version string.

    On 0.3.x this requires the handle-based 393e02e+ kernel; the
    structural import guard in src/pywfm/__init__.py refuses to load
    against any DLL that still exports IW_Model_Switch, so by the time
    a test runs we know we're on a compatible build.
    """
    misc = IWFMMiscellaneous()
    v = misc.get_version()
    return v.get("IWFM Core") or v["IWFM"]


@pytest.fixture(scope="session")
def sample_dir():
    """The vendored 2025-vintage SampleModel.

    Unlike the 0.2.x suite, 0.3.x only ships one variant — the 2015
    series doesn't have a handle-based kernel build, so a v2015 fixture
    would never apply here.
    """
    chosen = SAMPLE_DIR / "v2025"
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


@pytest.fixture(scope="session")
def sample_simulation(sample_dir, tmp_path_factory):
    """Session-scoped sim-mode IWFMModel — shared across all sim tests.

    Function-scoped sim fixtures don't work on the IWFM kernel: after
    the first IWFMModel(is_for_inquiry=0).kill(), a second instantiation
    in the same process crashes the Fortran runtime (CLOSE error on a
    leaked unit). The kernel's simulation-mode bookkeeping is a process
    singleton that doesn't fully reset on kill. So phase 5 tests share
    one model and run sequentially against it; tests that mutate state
    (advance_state, simulate_*) accumulate effects on the shared model.

    Isolated to a tmp_path so simulation output doesn't truncate the
    vendored Results/ that inquiry-mode tests read.

    Copies the vendored Preprocessor + Simulation inputs to tmp_path so
    the simulation writes its Results there. This keeps the vendored
    Results/ (populated by _ensure_results for inquiry-mode tests)
    safe from truncation — IWFMModel(is_for_inquiry=0) opens Results in
    write mode on instantiation, so a sim test running against the
    vendored location would corrupt subsequent inquiry-mode tests.

    Uses _SilentLog so the DefaultLogger singleton isn't tripped after
    sample_inquiry has configured logging, and delete_inquiry_data_file
    =False for the same kernel-state-bookkeeping reason.
    """
    import shutil

    sim_dir = tmp_path_factory.mktemp("sim")
    for sub in ("Preprocessor", "Simulation"):
        shutil.copytree(sample_dir / sub, sim_dir / sub)
    # Kernel needs Results/ to exist on instantiation (writes output files
    # into it during simulate_*; wants to truncate-or-create them up front).
    (sim_dir / "Results").mkdir(exist_ok=True)
    pp = sim_dir / "Preprocessor" / "PreProcessor_MAIN.IN"
    sim = sim_dir / "Simulation" / "Simulation_MAIN.IN"
    cwd = os.getcwd()
    os.chdir(sim_dir / "Simulation")
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

    Also skips if Results/ is missing or empty — C2VSimCG inquiry-mode
    instantiation reads .hdf and .out files from Results/, which only
    exist after a prior sim run. Users must run simulate_all once
    locally before these tests will pass; the suite doesn't run
    simulate_all itself because C2VSimCG simulations take hours.
    """
    env = os.environ.get(
        "PYWFM_C2VSIMCG",
        r"C:\Users\hatch\OneDrive\Desktop\c2vsimcg\C2VSimCG_v2025_WY1974-2015",
    )
    p = Path(env)
    if not (p / "Preprocessor").exists():
        pytest.skip(f"C2VSimCG not found at {p}; set PYWFM_C2VSIMCG")
    results = p / "Results"
    if not results.exists() or not any(results.glob("*.hdf")):
        pytest.skip(
            f"C2VSimCG Results/ at {results} is empty or missing — "
            "run simulate_all locally first to populate it."
        )
    return p


def _find_main_in(directory, hints):
    """Locate a model component's main entry .in file.

    SampleModel uses ``*MAIN*.IN``; C2VSimCG/FG use names like
    ``C2VSimCG.in`` or ``C2VSimCG_Preprocessor.in``. Try the SampleModel
    convention first, then fall back to substring hints in *.in.
    """
    for pattern in ("*MAIN*.IN", "*MAIN*.in"):
        for p in directory.glob(pattern):
            return p
    candidates = [
        p for p in directory.glob("*.in")
        if any(h.lower() in p.name.lower() for h in hints)
    ]
    if candidates:
        return candidates[0]
    raise FileNotFoundError(f"no main .in file found in {directory}")


@pytest.fixture(scope="session")
def c2vsimcg_inquiry(c2vsimcg_path):
    """Long-lived read-only IWFMModel against C2VSimCG."""
    pp = _find_main_in(c2vsimcg_path / "Preprocessor", ["preproc"])
    sim = _find_main_in(c2vsimcg_path / "Simulation", ["c2vsimcg", "sim"])
    cwd = os.getcwd()
    os.chdir(c2vsimcg_path / "Simulation")
    try:
        m = pywfm.IWFMModel(str(pp), str(sim), is_for_inquiry=1)
        yield m
        m.kill()
    finally:
        os.chdir(cwd)
