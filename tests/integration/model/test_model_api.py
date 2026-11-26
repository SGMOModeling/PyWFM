"""IWFMModel budget, zone budget, parametric grid, stream, well and land use
wrappers (pywfm 1.0), cross-checked against each other and the budget files.

They share the ``sample_inquiry`` fixture. The per-time-step wrappers are
tested in test_simulation.py (TestSimulationState).
"""
import numpy as np
import pandas as pd
import pytest

import pywfm
from pywfm.exceptions import IWFMError

pytestmark = pytest.mark.integration

WATER_YEAR = ("10/31/1990_24:00", "09/30/1992_24:00")


def _zones_from_subregions(model):
    """Zone definition with one zone per subregion (horizontal zones)."""
    elements = list(model.get_element_ids())
    zones = [int(s) for s in model.get_subregions_by_element()]
    return dict(zone_extent="horizontal", elements=elements, layers=[1] * len(elements),
                zone_ids=zones)


@pytest.fixture(scope="module")
def gw_budget_type(sample_inquiry):
    return sample_inquiry.get_budget_type_ids()["gw"]


@pytest.fixture(scope="module")
def gw_zbudget_type(sample_inquiry):
    return sample_inquiry.get_zbudget_type_ids()["gw"]


# ---------------------------------------------------------------------------
# Budgets
# ---------------------------------------------------------------------------
class TestBudgets:
    def test_budget_list(self, sample_inquiry):
        budgets = sample_inquiry.get_budget_list()
        assert len(budgets) == sample_inquiry.get_n_budgets() > 0
        assert set(budgets.budget_type_id) <= set(sample_inquiry.get_budget_type_ids().values())

    def test_column_titles_match_column_count(self, sample_inquiry, gw_budget_type):
        titles = sample_inquiry.get_budget_column_titles(gw_budget_type, 1)
        assert len(titles) == sample_inquiry.get_budget_n_columns(gw_budget_type, 1)
        assert all(isinstance(t, str) and t for t in titles)

    def test_time_series_matches_budget_file(self, sample_inquiry, gw_budget_type, sample_gw_budget):
        through_model = sample_inquiry.get_budget_time_series(
            gw_budget_type, 1, begin_date=WATER_YEAR[0], end_date=WATER_YEAR[1], interval="1MON")
        from_file = sample_gw_budget.get_values(
            1, begin_date=WATER_YEAR[0], end_date=WATER_YEAR[1], output_interval="1MON")
        assert list(through_model.columns) == list(from_file.columns)
        assert len(through_model) == len(from_file)
        np.testing.assert_array_equal(through_model.iloc[:, 1:].to_numpy(),
                                      from_file.iloc[:, 1:].to_numpy())
        assert (through_model.Time.to_numpy() == from_file.Time.to_numpy()).all()

    def test_time_series_selected_columns(self, sample_inquiry, gw_budget_type):
        titles = sample_inquiry.get_budget_column_titles(gw_budget_type, 1)
        ts = sample_inquiry.get_budget_time_series(gw_budget_type, 1, columns=[2, 3], interval="1MON")
        assert list(ts.columns) == ["Time", titles[1], titles[2]]
        assert len(ts.attrs["data_types"]) == 2

    @pytest.mark.parametrize("calendar_year", [False, True])
    def test_annual_flows(self, sample_inquiry, gw_budget_type, calendar_year):
        flows = sample_inquiry.get_budget_annual_flows(gw_budget_type, 1, calendar_year=calendar_year)
        assert flows.index.name == ("calendar_year" if calendar_year else "water_year")
        assert len(flows) > 0 and flows.shape[1] > 0
        assert np.isfinite(flows.to_numpy()).all()

    def test_monthly_average_flows(self, sample_inquiry, gw_budget_type):
        mean, sd = sample_inquiry.get_budget_monthly_average_flows(gw_budget_type, 1)
        assert list(mean.index) == ["OCT", "NOV", "DEC", "JAN", "FEB", "MAR",
                                    "APR", "MAY", "JUN", "JUL", "AUG", "SEP"]
        assert mean.shape == sd.shape and mean.shape[1] > 0
        assert (sd.to_numpy() >= 0).all()

    def test_cumulative_storage_change_starts_at_zero(self, sample_inquiry):
        cum = sample_inquiry.get_budget_cumulative_gw_storage_change(1, interval="1MON")
        assert cum.cumulative_storage_change.iloc[0] == 0.0
        assert len(cum) > 12

    def test_annual_cumulative_storage_change(self, sample_inquiry):
        if pywfm.abi() == "switch":
            # stock DWR libraries return invalid values here
            with pytest.raises(IWFMError):
                sample_inquiry.get_budget_annual_cumulative_gw_storage_change(1)
            return
        by_budget = sample_inquiry.get_budget_annual_cumulative_gw_storage_change(1)
        by_zone = sample_inquiry.get_zbudget_annual_cumulative_gw_storage_change(
            1, **_zones_from_subregions(sample_inquiry))
        assert by_budget.iloc[0] == 0.0
        np.testing.assert_allclose(by_budget.to_numpy(), by_zone.to_numpy(),
                                   rtol=1e-9, atol=1e-3 * np.abs(by_budget).max())


# ---------------------------------------------------------------------------
# Zone budgets
# ---------------------------------------------------------------------------
class TestZoneBudgets:
    def test_zbudget_list(self, sample_inquiry):
        zbudgets = sample_inquiry.get_zbudget_list()
        assert len(zbudgets) == sample_inquiry.get_n_zbudgets() > 0

    def test_column_titles_match_column_count(self, sample_inquiry, gw_zbudget_type):
        zones = _zones_from_subregions(sample_inquiry)
        titles = sample_inquiry.get_zbudget_column_titles(gw_zbudget_type, 1, **zones)
        assert len(titles) == sample_inquiry.get_zbudget_n_columns(gw_zbudget_type, 1, **zones)

    def test_time_series(self, sample_inquiry, gw_zbudget_type):
        zones = _zones_from_subregions(sample_inquiry)
        ts = sample_inquiry.get_zbudget_time_series(
            gw_zbudget_type, 1, **zones, begin_date=WATER_YEAR[0], end_date=WATER_YEAR[1],
            interval="1MON")
        assert len(ts) == 23 and ts.shape[1] == 1 + sample_inquiry.get_zbudget_n_columns(
            gw_zbudget_type, 1, **zones)

    def test_annual_and_monthly_flows(self, sample_inquiry, gw_zbudget_type):
        zones = _zones_from_subregions(sample_inquiry)
        annual = sample_inquiry.get_zbudget_annual_flows(gw_zbudget_type, 1, **zones)
        mean, sd = sample_inquiry.get_zbudget_monthly_average_flows(gw_zbudget_type, 1, **zones)
        assert len(annual) > 0 and annual.shape[1] == mean.shape[1] == sd.shape[1]

    def test_zone_storage_change_matches_subregion(self, sample_inquiry):
        """Zone 1 is subregion 1, so both cumulative storage changes agree."""
        by_zone = sample_inquiry.get_zbudget_cumulative_gw_storage_change(
            1, **_zones_from_subregions(sample_inquiry), interval="1MON")
        by_subregion = sample_inquiry.get_budget_cumulative_gw_storage_change(1, interval="1MON")
        np.testing.assert_allclose(by_zone.cumulative_storage_change.to_numpy(),
                                   by_subregion.cumulative_storage_change.to_numpy(),
                                   rtol=1e-9, atol=1.0)

    def test_zone_definition_is_validated(self, sample_inquiry, gw_zbudget_type):
        with pytest.raises(ValueError):
            sample_inquiry.get_zbudget_n_columns(gw_zbudget_type, 1, "horizontal", [1, 2], [1], [1, 1])
        with pytest.raises(ValueError):
            sample_inquiry.get_zbudget_n_columns(gw_zbudget_type, 1, "diagonal", [1], [1], [1])

    def test_land_use_zbudget_flows_need_a_land_use_type(self, sample_inquiry):
        """Annual land and water use zone flows for a land use type the budget
        doesn't report are an error, not a process abort."""
        if pywfm.abi() == "switch":
            pytest.skip("stock DWR libraries abort the process here")
        lwu = sample_inquiry.get_zbudget_type_ids()["lwu"]
        if lwu not in set(sample_inquiry.get_zbudget_list().zbudget_type_id):
            pytest.skip("model writes no land and water use zone budget")
        zones = _zones_from_subregions(sample_inquiry)
        with pytest.raises(IWFMError):
            sample_inquiry.get_zbudget_annual_flows(lwu, 1, **zones, land_use_type_id=0)
        ag = sample_inquiry.get_land_use_type_ids_2()["nonponded_ag"]
        flows = sample_inquiry.get_zbudget_annual_flows(lwu, 1, **zones, land_use_type_id=ag)
        assert len(flows) > 0

        # Annual means annual: the supply requirement is the water-year total of
        # the zone budget's own column (DWR's library returned monthly values).
        yearly = sample_inquiry.get_zbudget_time_series(lwu, 1, **zones, interval="1YEAR")
        column = next(c for c in yearly.columns
                      if "non-ponded" in c.lower() and "supply requirement" in c.lower())
        n = min(len(flows), len(yearly))
        np.testing.assert_allclose(-flows["Supply Requirement"].to_numpy()[:n],
                                   yearly[column].to_numpy()[:n], rtol=1e-9)

    def test_land_use_budget_flows_need_a_land_use_type(self, sample_inquiry):
        """The same for the land and water use budget, annual and monthly."""
        if pywfm.abi() == "switch":
            pytest.skip("stock DWR libraries crash here")
        lwu = sample_inquiry.get_budget_type_ids()["lwu"]
        if lwu not in set(sample_inquiry.get_budget_list().budget_type_id):
            pytest.skip("model writes no land and water use budget")
        ids = sample_inquiry.get_land_use_type_ids_2()
        for unreported in (0, ids["rice"]):
            with pytest.raises(IWFMError):
                sample_inquiry.get_budget_annual_flows(lwu, 1, land_use_type_id=unreported)
            with pytest.raises(IWFMError):
                sample_inquiry.get_budget_monthly_average_flows(lwu, 1, land_use_type_id=unreported)
        assert len(sample_inquiry.get_budget_annual_flows(lwu, 1, land_use_type_id=ids["general_ag"])) > 0


def test_zbudget_progress_callback(sample_gw_zbudget):
    """get_values_for_a_zone(progress=...) reports each time stamp and returns
    the same values as without a callback."""
    seen = []
    with_progress = sample_gw_zbudget.get_values_for_a_zone(1, progress=seen.append)
    without = sample_gw_zbudget.get_values_for_a_zone(1)
    pd.testing.assert_frame_equal(with_progress, without)
    assert len(seen) >= len(without) and all("_" in s for s in seen)


# ---------------------------------------------------------------------------
# Parametric grids, wells, diversions, land use, misc
# ---------------------------------------------------------------------------
class TestModelData:
    def test_parametric_grids(self, sample_inquiry):
        n_grids = sample_inquiry.get_n_parametric_grids()
        for grid in range(1, n_grids + 1):
            n_nodes = sample_inquiry.get_n_parametric_nodes(grid)
            x, y = sample_inquiry.get_parametric_node_coordinates(grid)
            assert len(x) == len(y) == n_nodes
            params = sample_inquiry.get_parametric_aquifer_parameters(grid)
            assert set(params) == {"horizontal_k", "aquifer_vertical_k", "aquitard_vertical_k",
                                   "specific_yield", "specific_storage"}
            assert all(a.shape == (sample_inquiry.get_n_layers(), n_nodes) for a in params.values())
            for element in range(1, sample_inquiry.get_n_parametric_elements(grid) + 1):
                vertices = sample_inquiry.get_parametric_element_vertices(grid, element)
                assert len(vertices) == 4 and vertices[:3].min() >= 1

    def test_initial_heads(self, sample_inquiry, sample_dir):
        """The heads equal the FACTHP block of the groundwater main file."""
        try:
            heads = sample_inquiry.get_gw_heads_initial_conditions()
        except IWFMError:
            if pywfm.abi() == "switch":
                # stock libraries misread files with a groundwater return flow
                # block (IFLAGRF) before the initial heads (fixed in the fork)
                pytest.skip("stock library misreads this groundwater main file")
            raise
        n_layers, n_nodes = sample_inquiry.get_n_layers(), sample_inquiry.get_n_nodes()
        assert heads.shape == (n_layers, n_nodes)
        lines = [ln for ln in (sample_dir / "Simulation" / "GW" / "GW_MAIN.dat")
                 .read_text(encoding="latin-1").splitlines() if ln[:1] not in ("C", "c", "*")]
        start = next(i for i, ln in enumerate(lines) if "/ FACTHP" in ln)
        factor = float(lines[start].split()[0])
        rows = [ln.split() for ln in lines[start + 1:start + 1 + n_nodes]]
        expected = {int(r[0]): [float(v) * factor for v in r[1:1 + n_layers]] for r in rows}
        ids = list(sample_inquiry.get_node_ids())
        np.testing.assert_allclose(heads.T, [expected[i] for i in ids])

    def test_well_elements(self, sample_inquiry):
        if sample_inquiry.get_n_wells() == 0:
            pytest.skip("model has no wells")
        well = int(sample_inquiry.get_well_ids()[0])
        elements = sample_inquiry.get_well_elements(well)
        assert len(elements) == sample_inquiry.get_n_well_elements(well)
        assert set(elements) <= set(sample_inquiry.get_element_ids())

    def test_diversion_recharge_zone(self, sample_inquiry):
        for d in sample_inquiry.get_diversion_ids():
            zone = sample_inquiry.get_diversion_recharge_zone(int(d))
            assert set(zone.element_id) <= set(sample_inquiry.get_element_ids())
            if len(zone):
                assert zone.fraction.sum() == pytest.approx(1.0)

    def test_land_use_areas_for_time_period(self, sample_inquiry):
        urban = sample_inquiry.get_land_use_type_ids_2()["urban"]
        if pywfm.abi() == "switch":
            # the stock library reopens land use files the model has open
            with pytest.raises(IWFMError, match="already open"):
                sample_inquiry.get_land_use_areas_for_time_period(
                    urban, begin_date=WATER_YEAR[0], end_date="11/30/1990_24:00")
            return
        areas = sample_inquiry.get_land_use_areas_for_time_period(
            urban, begin_date=WATER_YEAR[0], end_date="11/30/1990_24:00")
        assert areas.shape[1] == sample_inquiry.get_n_elements()
        assert areas.index[0] == WATER_YEAR[0] and (areas.to_numpy() >= 0).all()

    def test_misc_ids(self, sample_inquiry):
        ids = sample_inquiry.get_land_use_type_ids_2()
        assert ids["ponded_ag"] == sample_inquiry.get_land_use_type_id_ponded_ag()
        assert isinstance(sample_inquiry.get_location_type_id_tiledrain(), int)
        assert sample_inquiry.get_kernel_version()
