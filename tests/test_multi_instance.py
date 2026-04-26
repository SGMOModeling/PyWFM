"""
Multi-instance smoke test for Track 7 handle-based DLL API.

Demonstrates that two IWFMModel objects can coexist in the same Python
process and operate on independent slots without contaminating each
other's state.

Notes for users opening multiple models simultaneously:

- Pass ``delete_inquiry_data_file=False`` for second-and-later instances.
  The first ``IW_Model_DeleteInquiryDataFile`` call leaves Fortran unit
  bookkeeping in a state that crashes the next ``IW_Model_New``. This is
  a kernel-level limitation, not a pywfm bug. Call delete_inquiry once
  before creating any models, or skip it.
- Logging in IWFM is a process-wide singleton (``DefaultLogger``).
  Setting a different ``log_file`` on the second IWFMModel triggers a
  fatal "log file already created" error in the kernel. Use the same
  ``log_file`` value (or none) across instances.
"""

import os

import pytest

import pywfm


# Locate sample model relative to this repo's standard layout.
_SAMPLE = os.environ.get(
    "IWFM_SAMPLE_MODEL",
    os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            "..", "..", "IWFM", "iwfm-2025.0.1747", "SampleModel",
        )
    ),
)
_PP = os.path.join(_SAMPLE, "Preprocessor", "PreProcessor_MAIN.IN")
_SIM = os.path.join(_SAMPLE, "Simulation", "Simulation_MAIN.IN")
_RESULTS = os.path.join(_SAMPLE, "Results")


def _have_sample_model():
    if not (os.path.isfile(_PP) and os.path.isfile(_SIM)):
        return False
    # Inquiry mode requires the Results/ baseline files to exist.
    return any(f.endswith(".out") for f in os.listdir(_RESULTS)) if os.path.isdir(_RESULTS) else False


@pytest.mark.skipif(not _have_sample_model(),
                    reason=f"sample model not found at {_SAMPLE} or Results/ empty")
def test_two_models_simultaneously(tmp_path, monkeypatch):
    """Two IWFMModel instances run side-by-side, each with its own model_id.

    Validates the Track 7 handle-based DLL API: every method dispatches
    on ``self.model_id``, so killing one model leaves the other fully
    functional.
    """
    monkeypatch.chdir(os.path.dirname(_SIM))

    # IWFM's DefaultLogger is a process-wide singleton — only one
    # set_log_file call is allowed per process. Subclass to suppress
    # the per-instance set_log_file call so both instances share whatever
    # log was set first.
    class M(pywfm.IWFMModel):
        def set_log_file(self, file_name):
            pass

    m1 = M(_PP, _SIM, has_routed_streams=1, is_for_inquiry=1)

    # Second instance must skip delete_inquiry_data_file (kernel limitation).
    m2 = M(
        _PP, _SIM,
        has_routed_streams=1,
        is_for_inquiry=1,
        delete_inquiry_data_file=False,
    )

    try:
        # Slots are distinct.
        assert m1.model_id.value == 1
        assert m2.model_id.value == 2

        # Independent queries return matching data (same input model loaded twice).
        assert m1.get_n_nodes() == m2.get_n_nodes()
        assert m1.get_n_time_steps() == m2.get_n_time_steps()
        assert m1.get_n_elements() == m2.get_n_elements()

        # Killing m1 does NOT affect m2.
        n_nodes_before = m2.get_n_nodes()
        m1.kill()
        assert m2.get_n_nodes() == n_nodes_before
    finally:
        try:
            m2.kill()
        except Exception:
            pass
