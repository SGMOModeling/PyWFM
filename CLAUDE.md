# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

`pywfm` is a Python wrapper around the **IWFM (Integrated Water Flow Model) C API DLL** maintained by California DWR. It exposes the Fortran procedures via `ctypes` so users work with regular Python types (str, int, float, list, numpy arrays) instead of raw `ctypes` buffers. Distribution is Windows-only because the IWFM DLL is Windows-only (a Linux `.so` path exists in `__init__.py` but is exploratory).

## Two release lines

The repo maintains two parallel branches because the IWFM kernel had a multi-instance API rewrite (commit 393e02e) that no shipped DLL ships with yet:

- **`master` (this branch, 0.3.x)** — targets the handle-based kernel (393e02e+). Every `IW_Model_*` call takes `iModelID`. `IW_Model_Switch` is gone. Held at `0.3.0-rc1` (no conda upload) until upstream publishes a DLL with the new kernel.
- **`0.2.x`** — maintenance line for stock IWFM DLLs currently in the cadwr-sgmo channel: 2015.0.1273, 2015.0.1403, 2015.1.1443, 2024.2.1594, 2025.0.1747. Bug fixes for those users land here. Uses `IW_Model_Switch` / `IW_Model_GetCurrentModelID` (the previous-generation multi-instance pattern) for 2024/2025; falls through `hasattr` guards on 2015.

When working on a fix, decide which line it belongs to before opening a PR. Cross-port if it applies to both.

## Common commands

Tests use pytest:

```
pytest                              # run all tests
pytest tests/test_multi_instance.py # run one file
pytest tests/test_multi_instance.py::test_two_models_simultaneously
```

The multi-instance test is gated on a sample model existing on disk (default path `../../IWFM/iwfm-2025.0.1747/SampleModel`, override with `IWFM_SAMPLE_MODEL` env var). `test_model.py`, `test_budget.py`, and `test_zbudget.py` are unfinished stubs that import a non-existent `iwfmdll` package and will fail collection — leave them alone unless explicitly asked to fix them.

CLI (installed by `pip install -e .`):

```
pywfm setup-pywfm --version 1747       # download IWFM API zip from CNRA, copy DLL into env's Library/bin
pywfm setup-pywfm --path C:\path\to\IWFM_C_x64.dll  # use a local DLL instead
pywfm get-api-version                  # print version of the loaded DLL
```

Build:

```
pip install -e .                      # editable install
conda build conda.recipe                # build noarch conda pkg, requires conda-build & anaconda-client
```

The conda recipe builds one variant per IWFM API version listed in `conda.recipe/conda_build_config.yaml` and depends on `cadwr-sgmo::iwfmdll==<version>` to vendor the DLL. Targets Python 3.8 per the same config.

## Architecture

### DLL loading happens at import time

`src/pywfm/__init__.py` resolves `LIB` to `<python-env>/Library/bin/IWFM_C_x64.dll` (or `IWFM2015_C_x64.dll`) and calls `ctypes.CDLL(LIB)` into module-level `IWFM_API`. Importing `pywfm` therefore **fails immediately** if the DLL isn't installed — the CLI's `setup-pywfm` command exists to put it there. `IWFM_API` is the singleton handle every class uses via `self.dll`.

Right after the load, a structural guard checks `hasattr(IWFM_API, "IW_Model_Switch")`. That symbol exists on every pre-393e02e DLL and was removed by the kernel rewrite, so its presence is the unambiguous signal that the user has the wrong generation of DLL — the guard raises `IWFMError` with a "pin `iwfm-pywfm<0.3`" message. Don't replace this with a version-string parse; the structural check survives upstream version-label reuse.

### Class hierarchy

```
IWFMMiscellaneous (misc.py)         base — sets self.dll = IWFM_API, exposes IW_Get* helpers
├── IWFMModel    (model.py, ~580k)  IW_Model_*  — the bulk of the API
├── IWFMBudget   (budget.py)        IW_Budget_* — budget HDF post-processing
└── IWFMZBudget  (zbudget.py)       IW_ZBudget_* — zone-based budget
```

`IWFMMiscellaneous` is a base, not standalone — its docstring says "this class is not meant to be called directly," and `cli.py` instantiates it only to call `get_version()`. Most methods follow the same pattern: check `hasattr(self.dll, "IW_X")` (raises `AttributeError` if the loaded DLL is older), pack inputs into ctypes, call the Fortran proc, check `status.value`, raise `IWFMError` on non-zero, return Python types. **When adding methods, follow this pattern exactly** — don't shortcut the `hasattr` guard, since the same code runs against multiple DLL versions.

### Handle-based model API (multi-instance)

`IW_Model_New` returns a `model_id` (slot integer) and every subsequent `IW_Model_*` call takes it as the first argument. `IWFMModel.__init__` captures it as `self.model_id = ctypes.c_int(self.new())`, and every method passes `ctypes.byref(self.model_id)` so multiple `IWFMModel` instances coexist. There's no version branching in `new()` — the structural import-time guard in `__init__.py` already excluded any DLL that doesn't fit this shape.

Two kernel-level limitations bite when using multiple instances simultaneously (documented in `tests/test_multi_instance.py`):

1. `delete_inquiry_data_file` corrupts Fortran unit bookkeeping in current 393e02e+ builds — pass `delete_inquiry_data_file=False` on the 2nd+ instance.
2. IWFM's `DefaultLogger` is a process-wide singleton — only one `set_log_file` call is allowed per process. Subclass `IWFMModel` and override `set_log_file` to a no-op for additional instances, or share the same `log_file`.

These are kernel limits, not pywfm bugs — don't try to "fix" them by changing pywfm.

### IWFMModel modes

- `is_for_inquiry=1` (default): read-only against an already-completed model. Requires the Results/ directory to be populated.
- `is_for_inquiry=0`: run a simulation from Python and interact with it at runtime.

### IWFMBudget / IWFMZBudget

These are stateful in a different way: `IW_Budget_OpenFile` / `IW_ZBudget_OpenFile` open one file at a time and there's no slot ID — the kernel tracks "the open budget." Be aware when writing tests or examples that you can't have two `IWFMBudget` instances open simultaneously the way you can with `IWFMModel`.

## Conventions worth knowing

- Ctypes preparation is verbose-but-uniform: `ctypes.c_int(x)`, `ctypes.create_string_buffer(s.encode("utf-8"))`, `ctypes.sizeof(buf)` for the matching length arg, `ctypes.byref(...)` on every scalar passed to the DLL. Don't refactor toward "cleaner" wrappers — uniform repetition is what makes the file searchable for a given Fortran proc.
- `model.py` is ~580k and ~13k lines; use `Grep` to find the method that wraps a given `IW_Model_*` proc rather than reading top-down.
- Versioning: `__version__` lives in `src/pywfm/__init__.py` and is read by both `pyproject.toml` (`tool.setuptools.dynamic`) and `conda.recipe/meta.yaml` (regex). Bumping requires only that one line. Master is held at `0.3.0-rc1` until upstream ships the 393e02e+ DLL — see "When upstream ships" in `~/.claude/plans/does-this-repo-have-splendid-cookie.md` for the release checklist.
