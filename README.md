# pywfm

Python interface to the [Integrated Water Flow Model (IWFM)](https://data.cnra.ca.gov/dataset/iwfm-integrated-water-flow-model)
C API. Run IWFM simulations from Python, query a completed model's inputs
and results, and process budgets and zone budgets, all as NumPy arrays and
pandas DataFrames.

Full documentation: <https://sgmomodeling.github.io/PyWFM/html/index.html>

> **pywfm 1.0** works with both generations of the IWFM library: the stock
> DWR releases (2024.2.1594 and later) and the handle-based
> [2026.0.1848 fork](https://github.com/hatch-tyler/integrated-water-flow-model).
> Coming from 0.2.x or 0.3.x? See [MIGRATING.md](MIGRATING.md).

## Installation

pywfm needs Python 3.10 or later and the IWFM shared library
(`IWFM_C_x64.dll` on Windows, `libiwfm_c.so` on Linux).

**conda** (recommended). The library comes as a separate package,
`libiwfm`, which pywfm depends on:

```bash
conda install -c conda-forge iwfm-pywfm
```

**pip**. The Windows and Linux wheels bundle the IWFM library and install
the Intel Fortran and OpenMP runtimes it needs (`intel-fortran-rt`,
`intel-openmp`) from PyPI:

```bash
pip install iwfm-pywfm
```

**Another IWFM library.** To use a specific build, such as a stock DWR
DLL from the CNRA Open Data Platform or your own, point pywfm at it before
creating a model:

```bash
export PYWFM_DLL=/path/to/libiwfm_c.so   # the file, or a folder containing it
pywfm setup-pywfm --version 1848          # or download a stock DLL into the environment
```

```python
import pywfm
pywfm.load_dll(r"C:\path\to\IWFM_C_x64.dll")
```

pywfm looks for the library on first use, in this order:
1. `pywfm.load_dll(path)`;
2. the `PYWFM_DLL` environment variable;
3. the library bundled in the wheel;
4. the active environment (`Library\bin` on Windows, `lib` on Linux).

To see which library it picked up:

```bash
pywfm get-api-version
```

## Usage

```python
from pywfm import IWFMModel, IWFMBudget, IWFMZBudget

pp_file = "Preprocessor/PreProcessor_MAIN.IN"
sim_file = "Simulation/Simulation_MAIN.IN"

# Inquiry mode: read a model that has already been simulated
with IWFMModel(pp_file, sim_file, is_for_inquiry=1) as model:
    heads = model.get_gwheads_all()

# Budgets and zone budgets from the HDF5 output files
gw = IWFMBudget("Results/GW.hdf")
zb = IWFMZBudget("Results/GW_ZBud.hdf")
```

Simulation mode (`is_for_inquiry=0`) steps a model from Python. At each
time step you can read the time series data as is, or overwrite selected
values:

```python
with IWFMModel(pp_file, sim_file, is_for_inquiry=0) as model:
    while not model.is_end_of_simulation():
        model.advance_time()
        model.read_timeseries_data_overwrite(diversion_ids=[3], diversions=[0.0])
        model.simulate_for_one_timestep()
        model.print_results()
        model.advance_state()
```

`help(IWFMModel)` lists every method.

The IWFM library uses the calling thread's stack, and models need far more
than a Python thread has (the IWFM executables reserve 256 MB). pywfm
therefore runs every library call on a worker thread with a 255 MB stack,
the largest Windows allows a Python thread, one worker per calling thread.
This lets the library be compiled without heap-arrays, which makes it
several times faster (about 7x on C2VSimFG with the fork library).

The library runs parts of a simulation on up to 16 OpenMP threads. That
helps large models but slows small ones: the 2026.0.1848 sample model
simulates in 64 s on one thread and 149 s on sixteen. With the fork library
(2026.0.1848.rev, fork commit a36acdf or later), set `OMP_NUM_THREADS=1` (or
another count) in the environment before pywfm loads the library; stock
libraries always choose their own count.

### Freezing supply adjustment

Supply adjustment (`KOPTDV`) re-solves every time step until pumping and
diversions meet demand. When repeated runs don't change the demands, for
example while calibrating aquifer parameters, `pywfm.supply` records the
adjusted supplies once and writes input files that specify them as fixed
data, with supply adjustment off. This needs the handle-based fork library.

```python
from pywfm import IWFMModel
from pywfm.supply import freeze_supply_adjustment, record_adjusted_supplies

with IWFMModel(pp_file, sim_file, is_for_inquiry=0) as model:
    supplies = record_adjusted_supplies(model)
frozen_main = freeze_supply_adjustment(sim_file, supplies)   # Simulation_MAIN_frozen.IN
```

The frozen files are written next to the originals with a `_frozen`
suffix; the originals are not changed. The frozen run reproduces the
adjusted one within the solver tolerance: on the 2026.0.1848 sample model,
heads within 0.14 ft over 10 years and budgets within a relative 1e-4, in
half the time. Re-record when the demands or the stream flow available for
diversion change.

## Which IWFM library?

| | Stock DWR library (2024.2.1594+) | Handle-based fork (2026.0.1848.rev) |
|---|---|---|
| API generation (`pywfm.abi()`) | `"switch"` | `"handle"` |
| Several `IWFMModel` objects at once | yes: pywfm selects the active model before each call and serializes calls | yes, fully independent |
| Killing one model while others are open | breaks the others (a kernel limitation) | safe |
| DSS input files | DSS-6 | DSS-7 |
| Results compared with the official release | official | within the solver tolerance (its matrix solver keeps the ILUT preconditioner across iterations), and different where upstream bugs are fixed (subsidence v5.0) |
| Required pumping, diversion data values (`pywfm.supply`) | no | yes |
| `get_budget_annual_cumulative_gw_storage_change` | invalid values (raises) | yes |

pywfm 1.0 does not support the 2015-series libraries (2015.0.1273,
2015.0.1403, 2015.1.1443); use `iwfm-pywfm<0.3` for those.

## Development

```bash
pip install -e ".[test]"
PYWFM_DLL=/path/to/library pytest tests/unit tests/integration
pytest --runsim tests/integration/model/test_simulation.py   # simulation mode
```

The test suite chooses the vendored sample model and DSS file to match the
loaded library; see `tests/conftest.py`.

## License

pywfm is MIT-licensed. The IWFM library is GPL-2.0-or-later and is
distributed separately: as the conda `libiwfm` package, or bundled
unmodified in the wheels together with its license.
