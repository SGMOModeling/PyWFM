"""Argument-validation tests for IWFMModel.__init__.

These exercise the validation branches that fail-fast BEFORE any DLL
call, so they don't need a model fixture or a working DLL — they're
pure Python type checks at the top of ``__init__``. Useful as a
regression net when refactoring the constructor's validation order.
"""
import pytest

from pywfm import IWFMModel


@pytest.mark.unit
class TestPreprocessorFileNameValidation:
    def test_non_string_raises(self):
        with pytest.raises(TypeError, match="preprocessor_file_name must be a str"):
            IWFMModel(123, "sim.in")

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            IWFMModel("does/not/exist.in", "also-not-real.in")


@pytest.mark.unit
class TestSimulationFileNameValidation:
    def test_non_string_raises(self, tmp_path):
        # Need a real file for the first arg so the second arg's check fires
        pp = tmp_path / "preprocessor.in"
        pp.write_text("")
        with pytest.raises(TypeError, match="simulation_file_name must be a str"):
            IWFMModel(str(pp), 456)

    def test_missing_file_raises(self, tmp_path):
        pp = tmp_path / "preprocessor.in"
        pp.write_text("")
        with pytest.raises(FileNotFoundError):
            IWFMModel(str(pp), "/no/such/sim.in")


@pytest.mark.unit
class TestRoutedStreamsValidation:
    def test_non_int_raises(self, tmp_path):
        pp = tmp_path / "preprocessor.in"
        sim = tmp_path / "simulation.in"
        pp.write_text("")
        sim.write_text("")
        with pytest.raises(TypeError, match="has_routed_streams must be an int"):
            IWFMModel(str(pp), str(sim), has_routed_streams="yes")

    def test_out_of_range_raises(self, tmp_path):
        pp = tmp_path / "preprocessor.in"
        sim = tmp_path / "simulation.in"
        pp.write_text("")
        sim.write_text("")
        with pytest.raises(ValueError, match="has_routed_streams must be 0 or 1"):
            IWFMModel(str(pp), str(sim), has_routed_streams=2)


@pytest.mark.unit
class TestIsForInquiryValidation:
    def test_non_int_raises(self, tmp_path):
        pp = tmp_path / "preprocessor.in"
        sim = tmp_path / "simulation.in"
        pp.write_text("")
        sim.write_text("")
        with pytest.raises(TypeError, match="is_for_inquiry must be an int"):
            IWFMModel(str(pp), str(sim), is_for_inquiry=True and "true")  # str

    def test_out_of_range_raises(self, tmp_path):
        pp = tmp_path / "preprocessor.in"
        sim = tmp_path / "simulation.in"
        pp.write_text("")
        sim.write_text("")
        with pytest.raises(ValueError, match="is_for_inquiry must be 0 or 1"):
            IWFMModel(str(pp), str(sim), is_for_inquiry=42)
