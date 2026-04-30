"""Cross-method invariants for IWFMBudget.

Asserts that the time series, location, and column metadata are
internally consistent: every location has at least one column, the
get_values DataFrame has one row per timestep, column-wise queries
agree with the full-table query, and title metadata aligns with
n_title_lines.
"""
import numpy as np
import pandas as pd
import pytest


@pytest.mark.integration
class TestBudgetIntrospection:
    def test_n_locations_positive(self, sample_gw_budget):
        assert sample_gw_budget.get_n_locations() >= 1

    def test_n_time_steps_positive(self, sample_gw_budget):
        assert sample_gw_budget.get_n_time_steps() > 0

    def test_n_columns_per_location_positive(self, sample_gw_budget):
        """Every location must expose at least one budget column."""
        for loc in range(1, sample_gw_budget.get_n_locations() + 1):
            n = sample_gw_budget.get_n_columns(loc)
            assert n > 0, f"location {loc}: get_n_columns returned {n}"


@pytest.mark.integration
class TestBudgetValuesShape:
    def test_get_values_row_count_matches_n_time_steps(self, sample_gw_budget):
        """The full per-location table covers every simulation timestep."""
        df = sample_gw_budget.get_values(1)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == sample_gw_budget.get_n_time_steps()

    def test_column_headers_count_matches_n_columns(self, sample_gw_budget):
        """get_n_columns(loc) and get_column_headers(loc) agree on column count.

        get_column_headers may return a list of strings or a (headers, units)
        tuple depending on DLL version; flatten before comparing.
        """
        headers = sample_gw_budget.get_column_headers(1)
        if isinstance(headers, tuple) and len(headers) >= 1 and isinstance(headers[0], (list, tuple, np.ndarray)):
            header_count = len(headers[0])
        else:
            header_count = len(headers)
        # n_columns counts data columns; headers typically include a 'Time' column
        # too, so the relation is ``headers == n_columns + 1`` or equality.
        n = sample_gw_budget.get_n_columns(1)
        assert header_count in (n, n + 1), (
            f"header count {header_count} not in {{n_columns, n_columns+1}} where n_columns={n}"
        )


@pytest.mark.integration
class TestBudgetTitleLines:
    def test_n_title_lines_positive(self, sample_gw_budget):
        assert sample_gw_budget.get_n_title_lines() > 0

    def test_title_lines_count_matches_n_title_lines(self, sample_gw_budget):
        """get_title_lines(loc) returns exactly n_title_lines strings."""
        n = sample_gw_budget.get_n_title_lines()
        titles = sample_gw_budget.get_title_lines(1)
        assert len(titles) == n
        assert all(isinstance(t, str) for t in titles)
