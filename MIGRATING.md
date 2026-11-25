# Migrating to pywfm 1.0

pywfm 1.0 merges the 0.2.x line (stock DWR libraries) and the 0.3.x line
(the handle-based fork) into one package that works with either library.
Most code runs unchanged. This page lists what does change.

## Everyone

**Python 3.10 or later.** Earlier Python versions are no longer supported.

**The IWFM library is loaded on first use, not at import.** `import pywfm`
no longer fails when no library is installed. The error, which now lists
every place pywfm looked, appears when the first `IWFMModel`,
`IWFMBudget` or `IWFMZBudget` is created. To choose a library explicitly:

```python
import pywfm
pywfm.load_dll("/path/to/libiwfm_c.so")   # before creating any model
```

or set `PYWFM_DLL` to the file, or to the folder that contains it.
`pywfm.IWFM_API` and `pywfm.LIB` still work; using them loads the library.

**One library per process.** Loading a second, different library raises
`IWFMError`. Fortran module state lives in the library and can't be
unloaded safely.

**2015-series libraries are not supported** (2015.0.1273, 2015.0.1403,
2015.1.1443). pywfm 1.0 refuses to load them and points you to
`iwfm-pywfm<0.3`.

**`read_timeseries_data_overwrite` works now.** In earlier versions it
passed the wrong number of arguments to the library and failed whenever an
argument group was left out. In 1.0:
- all arguments are optional keywords (`None` means "don't overwrite");
- new `bypass_ids` and `bypasses` arguments overwrite bypass flows;
- IDs are translated to the positions IWFM uses, so the call also works for
  models whose diversion, inflow or bypass IDs don't run 1…N.

**Budget, zone budget and utility errors raise `IWFMError`.** Earlier
versions ignored the error status of every `IWFMBudget`, `IWFMZBudget` and
utility call, so a failed call returned meaningless values. A failed
budget read also closed the budget file without saying so. These calls now
raise `IWFMError` with the library's message, as `IWFMModel` always has.
`IWFMBudget.get_values_for_a_column` no longer accepts `"Time"` as a
column name.

**One log file per process.** The IWFM library keeps a single log file per
process. The first model opens it; later models share it instead of
failing. Asking for a different log file while one is open gives a warning;
call `close_log_file()` first to switch.

**Stale inquiry data with older stock libraries.** Stock libraries before
2026.0.1848 didn't delete `IW_ModelData_ForInquiry.bin` when asked to before
a model was opened. Reopening a model could then build only part of it, and
the missing parts returned wrong values without an error (for example, no
stream inflows). pywfm now deletes the file itself.

**Removed: `set_preprocessor_path` and `set_simulation_path`.** They wrapped
library procedures that no IWFM release has ever exported, so they always
raised `AttributeError`. Pass full paths to `IWFMModel` instead.

**`fe_interpolate`** returns one node and one coefficient per element
vertex: 3 for a triangle, 4 for a quadrilateral. For a point outside the
model grid it returns `(0, [], [])`. With a pre-2026.0.1848 library,
pywfm calls that library's older form of the procedure automatically.

**`pywfm setup-pywfm`** downloads 2026.0.1848 by default and installs it
into the active environment's library folder (`Library\bin` on Windows,
`lib` on Linux), where pywfm finds it. `pywfm get-api-version` also prints
the library path and API generation.

## From 0.2.x (stock DWR libraries)

**Several models no longer need manual switching.** `switch_active_model`
and `get_current_model_id` are gone. Each `IWFMModel` object now selects
its own model before every library call, under a lock, so you can keep
several objects open and call them in any order:

```python
a = IWFMModel(pp_a, sim_a)
b = IWFMModel(pp_b, sim_b)
a.get_n_nodes(); b.get_n_nodes()   # no switch_active_model() needed
```

The stock kernel still has one limitation: killing one model leaves the
others unusable. Kill them together at the end, or use the fork library.

## From 0.3.x (the handle-based fork)

The public API is the same. What's new is that the same pywfm also runs
on stock DWR libraries (see above), and installs from conda-forge or PyPI
instead of needing a separately downloaded DLL.

**DSS files.** The fork reads only DSS-7 files and stock libraries read
only DSS-6. A model's DSS inputs must match the library you load; convert
them with HEC-DSSVue if needed.

## Checking which library you have

```python
import pywfm
pywfm.dll_path()       # the library file in use
pywfm.abi()            # "handle" (fork) or "switch" (stock)
pywfm.core_version()   # e.g. (2026, 0, 1848)
```
