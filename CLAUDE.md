# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

`pywfm` is a Python wrapper around the **IWFM (Integrated Water Flow Model) C API library** maintained by California DWR. It exposes the Fortran procedures via `ctypes` so users work with regular Python types (str, int, float, list, numpy arrays) instead of raw `ctypes` buffers. Windows (`IWFM_C_x64.dll`) and Linux (`libiwfm_c.so`) are supported.

## Release lines

- **`1.0-dev`** (this branch, becoming 1.0): one codebase for both IWFM C API generations (see "Two API generations" below), Python 3.10+.
- **`0.3.x`**: handle-based kernel only. Superseded by 1.0.
- **`0.2.x`**: stock DLLs including the 2015 series (1273, 1403, 1443). 1.0 drops the 2015 series; fixes for those users land on 0.2.x.

## Common commands

```
pytest tests/unit tests/integration                  # inquiry-mode suite
pytest --runsim tests/integration/model/test_simulation.py      # sim-mode tests: own session
pytest --runsim tests/integration/model/test_multi_instance.py  # multi-instance: own session
PYWFM_DLL=C:\path\to\IWFM_C_x64.dll pytest ...    # test against a specific library
```

Run the suite once per library (stock 2025.0.1747, stock 2026.0.1848, the handle-based 2026.0.1848.rev build). `tests/conftest.py` picks the vendored SampleModel by the library's major version (`v2025` or `v2026`) and the DSS file by API generation (stock builds read only DSS-6, the handle-based builds only DSS-7), and builds a working copy under `tests/data/sample_model/.work/` (git-ignored; Results are cached there between sessions). `PYWFM_SAMPLE_DIR` overrides the SampleModel.

CLI:

```
pywfm setup-pywfm --version 1848       # download the stock IWFM API from CNRA into the env's library dir
pywfm setup-pywfm --path C:\path\to\IWFM_C_x64.dll  # use a local library instead
pywfm get-api-version                  # version, path, and API generation of the loaded library
```

Build:

```
pip install -e .                      # editable install (library from PYWFM_DLL or the environment)
python -m build --wheel               # pure wheel, or a py3-none-<platform> wheel when src/pywfm/_lib holds the library (setup.py)
rattler-build build -r recipe          # conda package (noarch; depends on libiwfm)
```

## Architecture

### Library loading (`_dll.py`)

The library is loaded on first use, not at import. Search order: `pywfm.load_dll(path)`, then the `PYWFM_DLL` environment variable, then the copy bundled in a platform wheel (`pywfm/_lib`), then the environment (`<prefix>/Library/bin` on Windows, `<prefix>/lib` on Linux, where the `libiwfm` conda package installs it). One library per process. `pywfm.IWFM_API` and `pywfm.LIB` still work (module `__getattr__`) but load the library when accessed.

### Two API generations

`_dll.abi()` classifies the loaded library structurally:

- `"switch"`: stock DWR DLLs (2024.2.1594+). They export `IW_Model_Switch`; the DLL holds one active model.
- `"handle"`: the handle-based kernel (commit 393e02e+, e.g. 2026.0.1848.rev). Every `IW_Model_*` procedure except `_dll.NO_MODEL_ID` takes the model ID as its first argument. Verified against the 2026.0.1848 sources: 165 procedures differ only by that leading argument.

Model methods call `self._call("IW_Model_X", *args)` with the arguments **without** the model ID. `_call` prepends the ID on handle libraries; on switch libraries it calls `IW_Model_Switch` under `_dll.ACTIVE_MODEL_LOCK` first, so several `IWFMModel` objects work on both. Keep the procedure name as the literal first argument so the file stays searchable by Fortran procedure name. When a procedure's arguments changed between releases, branch on `_dll.core_version()` inside the method (see `fe_interpolate`: 2026.0.1848 added NVertex and iStat). 2015-series DLLs are rejected at load.

### Class hierarchy

```
IWFMMiscellaneous (misc.py)         base — sets self.dll = get_dll(), exposes IW_Get* helpers
├── IWFMModel    (model.py, ~580k)  IW_Model_*  — the bulk of the API
├── IWFMBudget   (budget.py)        IW_Budget_* — budget HDF post-processing
└── IWFMZBudget  (zbudget.py)       IW_ZBudget_* — zone-based budget
```

`IWFMMiscellaneous` is a base, not standalone — its docstring says "this class is not meant to be called directly," and `cli.py` instantiates it only to call `get_version()`. Most methods follow the same pattern: check `hasattr(self.dll, "IW_X")` (raises `AttributeError` if the loaded DLL is older), pack inputs into ctypes, call the Fortran proc, check `status.value`, raise `IWFMError` on non-zero, return Python types. **When adding methods, follow this pattern exactly** — don't shortcut the `hasattr` guard, since the same code runs against multiple DLL versions.

### Multi-instance limitations

Two kernel-level limitations bite when using multiple instances simultaneously (documented in `tests/integration/model/test_multi_instance.py`):

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
- Versioning: `__version__` lives in `src/pywfm/__init__.py` (read by `pyproject.toml`); `recipe/recipe.yaml` repeats it in `context.version`.
