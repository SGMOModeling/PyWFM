"""Verifies the handle-based multi-instance API (kernel commit 393e02e+).

This is the feature 0.3.x was built for: multiple ``IWFMModel`` objects
can coexist in a single Python process, each operating on its own
``model_id`` slot independently. The single-instance smoke + invariant
suite already proves every ``IW_Model_*`` call passes the right
``model_id``; this file proves slots actually stay isolated.

Run with::

    pytest --runsim tests/integration/model/test_multi_instance.py

These tests are marked ``simulation`` (and skip by default) because
they create their own ``IWFMModel(is_for_inquiry=1)`` instances and
conflict with the session-scoped ``sample_inquiry`` fixture in a
shared session — the IWFM kernel's Fortran-unit bookkeeping doesn't
fully reset between back-to-back instantiations once a sim-mode model
has been created and killed earlier in the same session (which the
``_ensure_results`` fixture does). Run them in their own pytest
invocation to verify multi-instance behavior.

Notes for users opening multiple models simultaneously:

- Pass ``delete_inquiry_data_file=False`` for second-and-later
  instances. The first ``IW_Model_DeleteInquiryDataFile`` call leaves
  Fortran unit bookkeeping in a state that crashes the next
  ``IW_Model_New``. This is a kernel-level limitation, not a pywfm bug.
- Logging in IWFM is a process-wide singleton (``DefaultLogger``).
  Setting a different ``log_file`` on the second IWFMModel triggers a
  fatal "log file already created" error. The conftest ``_SilentLog``
  subclass no-ops ``set_log_file`` for second-and-later instances.
"""
import os

import pytest

import pywfm


@pytest.mark.integration
@pytest.mark.simulation
class TestTwoInquiryInstances:
    """Two IWFMModel instances, both inquiry mode, side by side."""

    def test_distinct_model_ids(self, sample_dir, sample_pp_sim, _ensure_results):
        """First instance gets model_id=1, second gets model_id=2."""
        from tests.conftest import _SilentLog

        pp, sim = sample_pp_sim
        cwd = os.getcwd()
        os.chdir(sample_dir / "Simulation")
        m1 = m2 = None
        try:
            m1 = _SilentLog(str(pp), str(sim), is_for_inquiry=1)
            m2 = _SilentLog(
                str(pp), str(sim),
                is_for_inquiry=1,
                delete_inquiry_data_file=False,
            )
            assert m1.model_id.value != m2.model_id.value
            assert m1.model_id.value >= 1
            assert m2.model_id.value >= 1
        finally:
            if m2 is not None:
                m2.kill()
            if m1 is not None:
                m1.kill()
            os.chdir(cwd)

    def test_independent_queries_match(self, sample_dir, sample_pp_sim, _ensure_results):
        """Both instances see the same SampleModel, so introspection getters
        return identical values when called via different model_ids."""
        from tests.conftest import _SilentLog

        pp, sim = sample_pp_sim
        cwd = os.getcwd()
        os.chdir(sample_dir / "Simulation")
        m1 = m2 = None
        try:
            m1 = _SilentLog(str(pp), str(sim), is_for_inquiry=1)
            m2 = _SilentLog(
                str(pp), str(sim),
                is_for_inquiry=1,
                delete_inquiry_data_file=False,
            )
            assert m1.get_n_nodes() == m2.get_n_nodes()
            assert m1.get_n_elements() == m2.get_n_elements()
            assert m1.get_n_layers() == m2.get_n_layers()
            assert m1.get_n_time_steps() == m2.get_n_time_steps()
        finally:
            if m2 is not None:
                m2.kill()
            if m1 is not None:
                m1.kill()
            os.chdir(cwd)

    def test_kill_one_leaves_other_functional(self, sample_dir, sample_pp_sim, _ensure_results):
        """Killing m1 must not affect m2 — the whole point of handle-based
        slots. A pre-393e02e kernel had a single 'active model' pointer,
        so killing m1 also broke m2; the rewrite fixed that.
        """
        from tests.conftest import _SilentLog

        pp, sim = sample_pp_sim
        cwd = os.getcwd()
        os.chdir(sample_dir / "Simulation")
        m1 = m2 = None
        try:
            m1 = _SilentLog(str(pp), str(sim), is_for_inquiry=1)
            m2 = _SilentLog(
                str(pp), str(sim),
                is_for_inquiry=1,
                delete_inquiry_data_file=False,
            )
            n_before = m2.get_n_nodes()
            m1.kill()
            m1 = None  # avoid double-kill in finally
            assert m2.get_n_nodes() == n_before
            assert m2.get_n_elements() > 0
        finally:
            if m2 is not None:
                m2.kill()
            if m1 is not None:
                m1.kill()
            os.chdir(cwd)
