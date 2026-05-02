"""Production-scale smoke tests against C2VSimCG.

C2VSimCG is the California Central Valley Simulation Model, Coarse Grid
variant — millions of stream-node-timestep cells, multi-decade time
series. Every test here mirrors a SampleModel test but exercises the
same code path at production scale, where bugs that don't surface on
a 441-node toy model become visible (large-array allocations, file
I/O against multi-GB HDF outputs, edge cases in the stream network).

These tests are gated on ``--runslow`` (skipped by default; opt in
with ``pytest --runslow``). They also require the C2VSimCG
``Results/`` directory to be populated — see the ``c2vsimcg_path``
fixture in conftest.py for the skip message.

We deliberately do NOT run a full simulate_all here — C2VSimCG sims
take hours and would never be appropriate for a test suite. The
intent is inquiry-mode introspection only.
"""
import numpy as np
import pandas as pd
import pytest


@pytest.mark.integration
@pytest.mark.slow
class TestC2VSimCGSizes:
    """C2VSimCG dimensions are orders of magnitude larger than SampleModel.
    These tests verify the count getters survive the larger scale and
    the model loads at all in inquiry mode."""

    def test_n_nodes_at_production_scale(self, c2vsimcg_inquiry):
        """C2VSimCG has thousands of nodes; SampleModel has 441."""
        n = c2vsimcg_inquiry.get_n_nodes()
        assert n > 1000, f"C2VSimCG should have >1000 nodes, got {n}"

    def test_n_elements_at_production_scale(self, c2vsimcg_inquiry):
        n = c2vsimcg_inquiry.get_n_elements()
        assert n > 1000, f"C2VSimCG should have >1000 elements, got {n}"

    def test_n_layers(self, c2vsimcg_inquiry):
        """C2VSimCG is a 2-3 layer model."""
        n = c2vsimcg_inquiry.get_n_layers()
        assert 1 <= n <= 10

    def test_n_subregions(self, c2vsimcg_inquiry):
        n = c2vsimcg_inquiry.get_n_subregions()
        assert n >= 1

    def test_n_time_steps_at_production_scale(self, c2vsimcg_inquiry):
        """C2VSimCG_v2025_WY1974-2015 covers ~40 water years monthly,
        so n_time_steps should be in the hundreds at minimum."""
        n = c2vsimcg_inquiry.get_n_time_steps()
        assert n > 100, f"C2VSimCG should have >100 timesteps, got {n}"


@pytest.mark.integration
@pytest.mark.slow
class TestC2VSimCGArrays:
    """Large array returns. The point isn't to validate the values,
    just that the marshalling code can move thousands of elements
    across the ctypes boundary without a crash or truncation."""

    def test_node_ids_length_matches(self, c2vsimcg_inquiry):
        n = c2vsimcg_inquiry.get_n_nodes()
        ids = c2vsimcg_inquiry.get_node_ids()
        assert len(ids) == n
        assert isinstance(ids, np.ndarray)

    def test_node_coordinates_length_matches(self, c2vsimcg_inquiry):
        n = c2vsimcg_inquiry.get_n_nodes()
        x, y = c2vsimcg_inquiry.get_node_coordinates()
        assert len(x) == n and len(y) == n
        assert np.all(np.isfinite(x)) and np.all(np.isfinite(y))

    def test_element_areas_positive(self, c2vsimcg_inquiry):
        areas = c2vsimcg_inquiry.get_element_areas()
        assert (areas > 0).all(), (
            f"{int((areas <= 0).sum())} elements have non-positive area"
        )


@pytest.mark.integration
@pytest.mark.slow
class TestC2VSimCGStreams:
    """Stream network at production scale."""

    def test_stream_node_count_matches_ids(self, c2vsimcg_inquiry):
        n = c2vsimcg_inquiry.get_n_stream_nodes()
        ids = c2vsimcg_inquiry.get_stream_node_ids()
        assert len(ids) == n

    def test_stream_reach_count_at_production_scale(self, c2vsimcg_inquiry):
        """C2VSimCG models the Sacramento + San Joaquin networks —
        many reaches expected."""
        n = c2vsimcg_inquiry.get_n_stream_reaches()
        assert n >= 1
