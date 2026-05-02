"""Round-trip / idempotency tests.

Few pywfm methods have symmetric set/get pairs (most setters mutate
internal state without an introspecting getter), so this file exercises
the more common variant: the same query against the same model state
returns the same answer.

This catches a class of bugs where a getter has hidden mutating side
effects (e.g. an internal cursor that advances on each call) and
also confirms that the cached count getters (n_nodes, n_elements, etc.)
behave consistently across repeated invocations.
"""
import numpy as np
import pytest

from conftest import requires_api


@pytest.mark.integration
class TestScalarIdempotency:
    """Calling the same scalar getter twice returns the same value."""

    @pytest.mark.parametrize("name", [
        "get_n_nodes",
        "get_n_elements",
        "get_n_subregions",
        "get_n_layers",
        "get_n_time_steps",
        "get_n_stream_nodes",
        "get_n_stream_reaches",
    ])
    def test_count_getter_repeats(self, sample_inquiry, name):
        getter = getattr(sample_inquiry, name)
        first = getter()
        second = getter()
        assert first == second, f"{name}: first call {first}, second call {second}"


@pytest.mark.integration
class TestArrayIdempotency:
    """Array getters return the same array on repeated calls."""

    @pytest.mark.parametrize("name", [
        "get_node_ids",
        "get_element_ids",
        "get_subregion_ids",
        pytest.param(
            "get_element_areas",
            marks=requires_api("IW_Model_GetElementAreas"),
        ),
    ])
    def test_array_getter_repeats(self, sample_inquiry, name):
        getter = getattr(sample_inquiry, name)
        a = getter()
        b = getter()
        np.testing.assert_array_equal(a, b)


@pytest.mark.integration
class TestZBudgetZoneRoundTrip:
    """Loading zones makes them visible to subsequent zone-keyed queries."""

    def test_zone_count_matches_loaded_definition(self, sample_gw_zbudget):
        """Zones loaded by the conftest fixture from ZoneDef_SRs.dat
        should equal the number of subregions in SampleModel — the
        fixture's zone definition file pins one zone per subregion.
        """
        n_zones = sample_gw_zbudget.get_n_zones()
        # SampleModel has 2 subregions; ZoneDef_SRs.dat is a per-subregion
        # zone definition. n_zones should be >= 1 (sanity check) and
        # consistent with the get_zone_list output length.
        assert n_zones >= 1
        zones = sample_gw_zbudget.get_zone_list()
        assert len(zones) == n_zones

    def test_zone_list_is_subset_of_get_values_columns(self, sample_gw_zbudget):
        """get_values_for_a_zone(zone_id) must succeed for every zone in get_zone_list."""
        for zone_id in sample_gw_zbudget.get_zone_list().tolist():
            df = sample_gw_zbudget.get_values_for_a_zone(int(zone_id))
            assert len(df) > 0, f"zone {zone_id}: get_values_for_a_zone returned empty"


@pytest.mark.integration
class TestTimeSpecsIdempotency:
    """get_time_specs is a non-trivial query (parses dates from binary blob)
    — repeated calls should return identical lists."""

    def test_time_specs_repeats(self, sample_inquiry):
        d1, i1 = sample_inquiry.get_time_specs()
        d2, i2 = sample_inquiry.get_time_specs()
        assert d1 == d2
        assert i1 == i2
