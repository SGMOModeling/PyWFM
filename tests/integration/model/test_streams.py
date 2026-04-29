"""Invariants on the stream network topology.

Asserts that stream node IDs, reach IDs, and inflow IDs are all
internally consistent. We don't check numerical flow values here —
that's regression-test territory.
"""
import numpy as np
import pytest


@pytest.mark.integration
class TestStreamReaches:
    def test_reach_ids_unique(self, sample_inquiry):
        ids = sample_inquiry.get_stream_reach_ids()
        assert len(ids) == len(np.unique(ids)), "duplicate stream reach IDs"

    def test_reach_count_consistent(self, sample_inquiry):
        n = sample_inquiry.get_n_stream_reaches()
        assert len(sample_inquiry.get_stream_reach_ids()) == n
        assert len(sample_inquiry.get_stream_reach_names()) == n

    def test_reach_names_nonempty(self, sample_inquiry):
        names = sample_inquiry.get_stream_reach_names()
        assert all(isinstance(n, str) and n.strip() for n in names), (
            "reach names should be non-empty strings"
        )


@pytest.mark.integration
class TestStreamNodes:
    def test_stream_node_ids_unique(self, sample_inquiry):
        ids = sample_inquiry.get_stream_node_ids()
        assert len(ids) == len(np.unique(ids)), "duplicate stream node IDs"

    def test_node_count_at_least_reaches_count(self, sample_inquiry):
        """A reach must contain at least one stream node, so n_stream_nodes >= n_stream_reaches."""
        if sample_inquiry.get_n_stream_reaches() == 0:
            pytest.skip("model has no stream reaches")
        assert sample_inquiry.get_n_stream_nodes() >= sample_inquiry.get_n_stream_reaches()


@pytest.mark.integration
class TestStreamInflows:
    def test_inflow_count_nonneg(self, sample_inquiry):
        assert sample_inquiry.get_n_stream_inflows() >= 0
