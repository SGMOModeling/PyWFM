"""Geometric invariants on the IWFM mesh.

These check internal consistency of the finite-element mesh: positive
element areas, plausible coordinate ranges, monotone layer ordering.
The actual numerical values aren't pinned here (that's regression
testing in tests/regression/) — we only assert structural properties
that should hold for any valid model.
"""
import numpy as np
import pytest


@pytest.mark.integration
class TestNodeCoordinates:
    def test_finite_coordinates(self, sample_inquiry):
        """No NaN or inf in node coords."""
        x, y = sample_inquiry.get_node_coordinates()
        assert np.all(np.isfinite(x)), "NaN/inf in node x-coordinates"
        assert np.all(np.isfinite(y)), "NaN/inf in node y-coordinates"

    def test_coordinate_range_nontrivial(self, sample_inquiry):
        """Mesh extent has positive width and height — no degenerate model."""
        x, y = sample_inquiry.get_node_coordinates()
        assert x.max() > x.min()
        assert y.max() > y.min()


@pytest.mark.integration
class TestElementAreas:
    def test_positive_areas(self, sample_inquiry):
        """Every element area is strictly positive (no degenerate elements)."""
        areas = sample_inquiry.get_element_areas()
        assert np.all(areas > 0), (
            f"{int((areas <= 0).sum())} of {len(areas)} elements have non-positive area"
        )

    def test_total_area_finite(self, sample_inquiry):
        """Sum of element areas is finite."""
        areas = sample_inquiry.get_element_areas()
        total = areas.sum()
        assert np.isfinite(total) and total > 0


@pytest.mark.integration
class TestLayerStructure:
    def test_at_least_one_layer(self, sample_inquiry):
        assert sample_inquiry.get_n_layers() >= 1


@pytest.mark.integration
class TestBoundary:
    def test_boundary_nodes_subset_of_all_nodes(self, sample_inquiry):
        """Every boundary node ID must be a known node ID.

        get_boundary_nodes returns a DataFrame of boundary segments
        (start_node, end_node, code). Flatten across both ID columns
        and verify each is a known node.
        """
        node_ids = set(int(n) for n in sample_inquiry.get_node_ids())
        boundary = sample_inquiry.get_boundary_nodes()
        # Drop the 'code' column (path-patch directive, not a node ID)
        # if present, then flatten remaining columns.
        id_cols = [c for c in boundary.columns if c.lower() != "code"]
        flat = set(int(v) for v in boundary[id_cols].values.ravel())
        unknown = flat - node_ids
        assert not unknown, f"Boundary references unknown node IDs: {sorted(unknown)[:10]}"
