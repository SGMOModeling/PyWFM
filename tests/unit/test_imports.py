"""Smoke tests that prove the package imports and the DLL loads.

These run with @pytest.mark.unit because they don't need a model fixture,
just the loaded DLL. They're the cheapest possible signal that something
catastrophic happened during import (missing DLL, version mismatch on
0.3.x, etc.).
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
def test_dll_loaded():
    """ctypes successfully loaded the IWFM DLL into IWFM_API."""
    assert pywfm.IWFM_API is not None
    assert pywfm.LIB.endswith(".dll") or pywfm.LIB.endswith(".so")


@pytest.mark.unit
def test_version_string():
    """__version__ matches PEP 440 form."""
    assert re.match(r"^\d+\.\d+\.\d+(-?\w+\d*)?$", pywfm.__version__), pywfm.__version__


@pytest.mark.unit
def test_dll_reports_iwfm_version(dll_version):
    """The DLL responds to IW_GetVersion with a parseable version string.

    Stock builds report ``2025.0.1747``; custom kernel builds may append
    a git short-SHA, e.g. ``2025.0.1747-054223d4``. We only insist on
    major.minor.build_<anything> form.
    """
    parts = dll_version.split(".")
    assert len(parts) == 3, f"Expected major.minor.build, got {dll_version!r}"
    major = int(parts[0])
    minor = int(parts[1])
    build = int(re.match(r"\d+", parts[2]).group())
    assert major >= 2015 and build >= 1000


@pytest.mark.unit
def test_dll_is_handle_based():
    """0.3.x requires the handle-based IWFM kernel (commit 393e02e+).

    The structural import-time guard in src/pywfm/__init__.py raises
    IWFMError if the loaded DLL still exports IW_Model_Switch — that
    symbol's absence is the unambiguous signal of the post-rewrite
    kernel. If this assertion ever fails, the guard didn't fire
    (the DLL was swapped post-import) — investigate before trusting
    any other test result.
    """
    assert not hasattr(pywfm.IWFM_API, "IW_Model_Switch"), (
        "IW_Model_Switch is exported — the DLL is from a pre-393e02e "
        "kernel and 0.3.x's import-time guard should have raised. Use "
        "iwfm-pywfm<0.3 (the 0.2.x maintenance line) with this DLL."
    )
