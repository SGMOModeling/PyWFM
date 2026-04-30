"""Cross-method invariants on aquifer parameters and groundwater state.

These check internal consistency of the aquifer system: per-layer/per-node
arrays have the right shape, parameters are physically plausible (storage
in [0,1], conductivities >= 0), and the layered geometry is monotonically
ordered (top of layer N+1 <= bottom of layer N for typical layered models).
Numerical values aren't pinned here — that's regression-test territory.
"""
import numpy as np
import pytest


@pytest.mark.integration
class TestAquiferGeometry:
    def test_top_bottom_shape_consistency(self, sample_inquiry):
        """Top and bottom elevation arrays match in shape and align to (n_layers, n_nodes)."""
        top = sample_inquiry.get_aquifer_top_elevation()
        bot = sample_inquiry.get_aquifer_bottom_elevation()
        assert top.shape == bot.shape
        assert top.shape == (sample_inquiry.get_n_layers(), sample_inquiry.get_n_nodes())

    def test_top_above_bottom(self, sample_inquiry):
        """Layer top elevation > bottom elevation everywhere (no zero-thickness aquifer)."""
        top = sample_inquiry.get_aquifer_top_elevation()
        bot = sample_inquiry.get_aquifer_bottom_elevation()
        bad = np.where(top <= bot)
        assert bad[0].size == 0, (
            f"{bad[0].size} (layer, node) pairs have top <= bot; first three: "
            f"layers={bad[0][:3]} nodes={bad[1][:3]} top={top[bad][:3]} bot={bot[bad][:3]}"
        )

    def test_ground_surface_within_aquifer_range(self, sample_inquiry):
        """Ground surface elevation lies within the overall aquifer envelope."""
        gs = sample_inquiry.get_ground_surface_elevation()
        top = sample_inquiry.get_aquifer_top_elevation()
        bot = sample_inquiry.get_aquifer_bottom_elevation()
        # Ground surface should be at-or-above the bottom of the deepest layer
        # and not unreasonably above the top of the shallowest.
        assert (gs >= bot.min()).all(), "ground surface below deepest aquifer bottom"
        assert (gs <= top.max() + 1e-3).all(), "ground surface above topmost aquifer top"
        assert gs.shape == (sample_inquiry.get_n_nodes(),)


@pytest.mark.integration
class TestAquiferParameters:
    def test_horizontal_k_nonnegative(self, sample_inquiry):
        hk = sample_inquiry.get_aquifer_horizontal_k()
        assert (hk >= 0).all(), "negative horizontal hydraulic conductivity"
        assert hk.shape == (sample_inquiry.get_n_layers(), sample_inquiry.get_n_nodes())

    def test_specific_yield_in_unit_range(self, sample_inquiry):
        """Specific yield is a dimensionless porosity-like quantity, in [0, 1]."""
        sy = sample_inquiry.get_aquifer_specific_yield()
        assert (sy >= 0).all() and (sy <= 1).all(), (
            f"specific_yield out of [0,1] range: min={sy.min()} max={sy.max()}"
        )
