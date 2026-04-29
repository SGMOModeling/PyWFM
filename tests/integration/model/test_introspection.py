"""Invariants that connect the count getters and the corresponding ID arrays.

If ``get_n_X()`` returns N, then ``get_X_ids()`` must return an N-length
array, ``get_X_names()`` must return an N-length list, and so on. These
invariants catch a whole class of off-by-one or bookkeeping bugs that
type/shape sanity tests alone don't detect — for instance, returning the
ID array for the wrong domain, or an off-by-one in count reporting.
"""
import numpy as np
import pytest


@pytest.mark.integration
class TestNodeIntrospection:
    def test_node_ids_count_matches_n_nodes(self, sample_inquiry):
        n = sample_inquiry.get_n_nodes()
        assert len(sample_inquiry.get_node_ids()) == n

    def test_node_coordinates_match_n_nodes(self, sample_inquiry):
        n = sample_inquiry.get_n_nodes()
        x, y = sample_inquiry.get_node_coordinates()
        assert len(x) == n and len(y) == n

    def test_n_nodes_positive(self, sample_inquiry):
        assert sample_inquiry.get_n_nodes() > 0


@pytest.mark.integration
class TestElementIntrospection:
    def test_element_ids_count_matches_n_elements(self, sample_inquiry):
        n = sample_inquiry.get_n_elements()
        assert len(sample_inquiry.get_element_ids()) == n

    def test_element_areas_count_matches_n_elements(self, sample_inquiry):
        n = sample_inquiry.get_n_elements()
        assert len(sample_inquiry.get_element_areas()) == n

    def test_subregions_by_element_count_matches_n_elements(self, sample_inquiry):
        n = sample_inquiry.get_n_elements()
        assert len(sample_inquiry.get_subregions_by_element()) == n

    def test_n_elements_positive(self, sample_inquiry):
        assert sample_inquiry.get_n_elements() > 0


@pytest.mark.integration
class TestSubregionIntrospection:
    def test_subregion_ids_count_matches_n_subregions(self, sample_inquiry):
        n = sample_inquiry.get_n_subregions()
        assert len(sample_inquiry.get_subregion_ids()) == n

    def test_subregion_names_count_matches_n_subregions(self, sample_inquiry):
        n = sample_inquiry.get_n_subregions()
        assert len(sample_inquiry.get_subregion_names()) == n

    def test_subregions_by_element_values_are_known_subregion_ids(self, sample_inquiry):
        """Every element's assigned subregion must be a registered subregion ID."""
        per_elem = sample_inquiry.get_subregions_by_element()
        valid = set(sample_inquiry.get_subregion_ids().tolist())
        unknown = set(per_elem.tolist()) - valid
        assert not unknown, f"Elements assigned to unknown subregions: {unknown}"


@pytest.mark.integration
class TestStreamIntrospection:
    def test_stream_node_ids_count_matches_n_stream_nodes(self, sample_inquiry):
        n = sample_inquiry.get_n_stream_nodes()
        assert len(sample_inquiry.get_stream_node_ids()) == n

    def test_stream_reach_ids_count_matches_n_stream_reaches(self, sample_inquiry):
        n = sample_inquiry.get_n_stream_reaches()
        assert len(sample_inquiry.get_stream_reach_ids()) == n

    def test_stream_reach_names_count_matches_n_stream_reaches(self, sample_inquiry):
        n = sample_inquiry.get_n_stream_reaches()
        assert len(sample_inquiry.get_stream_reach_names()) == n


@pytest.mark.integration
class TestLakeIntrospection:
    def test_lake_ids_count_matches_n_lakes(self, sample_inquiry):
        n = sample_inquiry.get_n_lakes()
        assert len(sample_inquiry.get_lake_ids()) == n


@pytest.mark.integration
class TestBypassDiversionIntrospection:
    def test_bypass_ids_count_matches_n_bypasses(self, sample_inquiry):
        n = sample_inquiry.get_n_bypasses()
        assert len(sample_inquiry.get_bypass_ids()) == n

    def test_diversion_ids_count_matches_n_diversions(self, sample_inquiry):
        n = sample_inquiry.get_n_diversions()
        assert len(sample_inquiry.get_diversion_ids()) == n
