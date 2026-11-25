"""Smoke tests that prove the package imports and the DLL loads.

These run with @pytest.mark.unit because they don't need a model fixture,
just the loaded DLL. They're the cheapest possible signal that something
catastrophic happened during import or library discovery.
"""
import re

import pytest

import pywfm


@pytest.mark.unit
def test_pywfm_imports():
    """The top-level package and the three classes import cleanly."""
    assert pywfm.IWFMModel is not None
    assert pywfm.IWFMBudget is not None
    assert pywfm.IWFMZBudget is not None


@pytest.mark.unit
def test_dll_loaded(iwfm_library):
    """The library loads and its path is reported."""
    assert pywfm.get_dll() is not None
    assert pywfm.IWFM_API is pywfm.get_dll()
    assert pywfm.LIB.endswith(".dll") or pywfm.LIB.endswith(".so")


@pytest.mark.unit
def test_version_string():
    """__version__ is a PEP 440 release, pre-release or dev version."""
    assert re.match(r"^\d+\.\d+\.\d+((a|b|rc)\d+)?(\.post\d+)?(\.dev\d+)?$", pywfm.__version__), pywfm.__version__


@pytest.mark.unit
def test_dll_reports_iwfm_version(dll_version):
    """The DLL responds to IW_GetVersion with a parseable version string.

    Stock builds report e.g. ``2025.0.1747``; custom kernel builds may
    append a git short-SHA, e.g. ``2026.0.1848-563bc0ef``.
    """
    parts = dll_version.split(".")
    assert len(parts) == 3, f"Expected major.minor.build, got {dll_version!r}"
    major = int(parts[0])
    build = int(re.match(r"\d+", parts[2]).group())
    assert major >= 2024 and build >= 1000


@pytest.mark.unit
def test_abi_matches_exports(iwfm_library):
    """abi() agrees with the structural marker: stock DLLs export IW_Model_Switch."""
    dll = pywfm.get_dll()
    expected = "switch" if hasattr(dll, "IW_Model_Switch") else "handle"
    assert pywfm.abi() == expected


@pytest.mark.unit
def test_load_dll_same_path_is_idempotent(iwfm_library):
    """Re-loading the already-loaded library returns the same handle."""
    assert pywfm.load_dll(pywfm.dll_path()) is pywfm.get_dll()


@pytest.mark.unit
def test_load_dll_other_path_refused(iwfm_library, tmp_path):
    """A process can only use one IWFM library."""
    other = tmp_path / "other.dll"
    other.write_bytes(b"")
    with pytest.raises(pywfm.IWFMError):
        pywfm.load_dll(other)


@pytest.mark.unit
def test_missing_library_error_lists_search_locations():
    """Without a library, the error names every place pywfm looked."""
    try:
        pywfm.get_dll()
    except FileNotFoundError as e:
        assert "PYWFM_DLL" in str(e)
    else:
        pytest.skip("an IWFM library is installed")
