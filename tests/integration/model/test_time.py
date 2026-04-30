"""Invariants on the simulation time spec.

We don't pin specific dates (those vary per model) — only structural
checks that the time spec is internally consistent and the date strings
parse via IWFM's MM/DD/YYYY_hh:mm format.
"""
import re

import pytest


_IWFM_DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}_\d{2}:\d{2}$")


@pytest.mark.integration
class TestTimeSpec:
    def test_n_time_steps_positive(self, sample_inquiry):
        assert sample_inquiry.get_n_time_steps() > 0

    def test_time_specs_count_matches_n_time_steps(self, sample_inquiry):
        n = sample_inquiry.get_n_time_steps()
        dates, _ = sample_inquiry.get_time_specs()
        assert len(dates) == n

    def test_date_format(self, sample_inquiry):
        """Every entry in dates is the IWFM MM/DD/YYYY_hh:mm format."""
        dates, _ = sample_inquiry.get_time_specs()
        bad = [d for d in dates if not _IWFM_DATE_RE.match(d)]
        assert not bad, f"{len(bad)} dates have unexpected format. First: {bad[:3]}"

    def test_dates_strictly_increasing(self, sample_inquiry):
        """Simulation timestamps are monotonically increasing."""
        dates, _ = sample_inquiry.get_time_specs()
        # Lexicographic comparison of MM/DD/YYYY... is wrong, so parse to tuples
        def parse(d):
            m, day, rest = d.split("/")
            year, time = rest.split("_")
            hh, mm = time.split(":")
            return (int(year), int(m), int(day), int(hh), int(mm))

        parsed = [parse(d) for d in dates]
        assert all(a < b for a, b in zip(parsed, parsed[1:])), "dates not strictly increasing"

    def test_current_date_returns_iwfm_format(self, sample_inquiry):
        """get_current_date_and_time returns the BDT — the simulation
        start (one interval BEFORE the first time-spec entry, which is
        end-of-first-step). The date itself just needs to parse as an
        IWFM-format string.
        """
        current = sample_inquiry.get_current_date_and_time()
        assert _IWFM_DATE_RE.match(current), f"current date {current!r} not in IWFM format"

    def test_simulation_interval_in_output_intervals(self, sample_inquiry):
        """The simulation timestep must be one of the supported output intervals.

        get_output_interval returns the list of intervals at which time-
        series data can be retrieved (e.g. 1DAY, 1WEEK, 1MON, 1YEAR). The
        simulation runs at the smallest of these — the time_specs
        interval — so it must be present in the list.
        """
        _, sim_interval = sample_inquiry.get_time_specs()
        output_intervals = sample_inquiry.get_output_interval()
        assert sim_interval in output_intervals, (
            f"simulation interval {sim_interval!r} not in supported output "
            f"intervals {output_intervals!r}"
        )
