"""The inquiry cache (IW_ModelData_ForInquiry.bin) is removed before a model
is created.

When the cache exists, the library builds only part of the model from it, and
the missing parts return wrong values rather than errors (stock 2025.0.1747
reports 0 stream inflows for the SampleModel, which has 1). Stock libraries
before 2026.0.1848 ignore IW_Model_DeleteInquiryDataFile when no model is open,
so pywfm also removes the file itself.
"""
import pytest

from conftest import _SilentLog


@pytest.mark.integration
def test_new_model_removes_stale_inquiry_cache(sample_pp_sim, sample_inquiry):
    pp, sim = sample_pp_sim
    cache = sim.parent / "IW_ModelData_ForInquiry.bin"
    cache.touch()

    _SilentLog(str(pp), str(sim), is_for_inquiry=1, instantiate=False)

    assert not cache.exists()
