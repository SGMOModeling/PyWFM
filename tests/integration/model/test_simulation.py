"""Tests for IWFMModel methods that mutate state during a simulation.

The IWFM simulation loop has a fixed call sequence per timestep:

    read_timeseries_data        # pull this step's TS data
    simulate_for_one_timestep   # solve the system
    print_results               # write outputs
    advance_state               # advance internal state
    advance_time                # advance the clock

These tests use the function-scoped ``sample_simulation`` fixture
(a fresh ``IWFMModel(is_for_inquiry=0)`` per test, the ``_SilentLog``
subclass to dodge the DefaultLogger singleton, and
``delete_inquiry_data_file=False`` to keep the kernel's bookkeeping
intact across instances).

We don't run a full simulation here — that's what ``_ensure_results``
in conftest does once per session. These tests exercise a step or two
to confirm the per-step methods work and side-effects propagate.
"""
import re

import numpy as np
import pandas as pd
import pytest


_IWFM_DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}_\d{2}:\d{2}$")


def _parse_iwfm_date(s: str):
    """MM/DD/YYYY_hh:mm → comparable tuple."""
    m, d, rest = s.split("/")
    y, t = rest.split("_")
    hh, mm = t.split(":")
    return (int(y), int(m), int(d), int(hh), int(mm))


@pytest.mark.integration
@pytest.mark.simulation
class TestSingleStepLifecycle:
    """One full timestep call sequence."""

    def test_one_full_timestep(self, sample_simulation):
        """Read → simulate → print → advance_state → advance_time."""
        sample_simulation.read_timeseries_data()
        sample_simulation.simulate_for_one_timestep()
        sample_simulation.print_results()
        sample_simulation.advance_state()
        sample_simulation.advance_time()

    def test_simulate_for_one_timestep_advances_date(self, sample_simulation):
        """After simulate + advance_time, current_date moves forward."""
        sample_simulation.read_timeseries_data()
        before = _parse_iwfm_date(sample_simulation.get_current_date_and_time())
        sample_simulation.simulate_for_one_timestep()
        sample_simulation.advance_state()
        sample_simulation.advance_time()
        after = _parse_iwfm_date(sample_simulation.get_current_date_and_time())
        assert after > before

    def test_two_consecutive_timesteps(self, sample_simulation):
        """Two cycles of the lifecycle. Simulation date advances each time."""
        dates = []
        for _ in range(2):
            sample_simulation.read_timeseries_data()
            sample_simulation.simulate_for_one_timestep()
            sample_simulation.print_results()
            sample_simulation.advance_state()
            sample_simulation.advance_time()
            dates.append(sample_simulation.get_current_date_and_time())
        assert _parse_iwfm_date(dates[1]) > _parse_iwfm_date(dates[0])


@pytest.mark.integration
@pytest.mark.simulation
class TestEndOfSimulation:
    def test_is_end_of_simulation_initially_false(self, sample_simulation):
        """Just-instantiated simulation hasn't started — not at end."""
        result = sample_simulation.is_end_of_simulation()
        # accept either bool or int return for kernel-version flexibility
        assert result in (False, 0)


@pytest.mark.integration
@pytest.mark.simulation
class TestSupplyAdjustmentControls:
    """The set_supply_adjustment_* and turn_supply_adjustment_on_off methods
    don't have getters — verify they don't raise when given valid inputs."""

    def test_set_supply_adjustment_max_iterations(self, sample_simulation):
        sample_simulation.set_supply_adjustment_max_iterations(50)

    def test_set_supply_adjustment_tolerance(self, sample_simulation):
        sample_simulation.set_supply_adjustment_tolerance(0.001)

    def test_turn_supply_adjustment_off_then_simulate(self, sample_simulation):
        """Turn supply adjustment off, then run one step — must succeed."""
        sample_simulation.turn_supply_adjustment_on_off(0, 0)
        sample_simulation.read_timeseries_data()
        sample_simulation.simulate_for_one_timestep()
        sample_simulation.advance_state()
        sample_simulation.advance_time()

    def test_restore_pumping_to_read_values(self, sample_simulation):
        """restore_pumping_to_read_values is idempotent on a fresh model."""
        sample_simulation.read_timeseries_data()
        # Restoring before any modification should be a no-op that doesn't raise
        sample_simulation.restore_pumping_to_read_values()


@pytest.mark.integration
@pytest.mark.simulation
class TestSimulateForAnInterval:
    """simulate_for_an_interval runs multiple internal timesteps to advance
    by a coarser interval (e.g. weekly when the simulation is daily)."""

    def test_simulate_for_an_interval_weekly(self, sample_simulation):
        """Simulate for 1WEEK on a 1DAY-step model — should advance ~7 days.

        Advances one timestep first so ``get_current_date_and_time()`` is
        guaranteed populated. Some IWFM kernel builds (notably 2015.0.1403
        on 0.2.x) return an empty string from this getter when called
        pre-simulation; later builds return BDT. Calling
        simulate_for_one_timestep first keeps the test portable across
        DLL builds while still exercising the same interval-advance
        behavior.
        """
        sample_simulation.read_timeseries_data()
        sample_simulation.simulate_for_one_timestep()
        sample_simulation.advance_state()
        sample_simulation.advance_time()
        sample_simulation.read_timeseries_data()
        before = _parse_iwfm_date(sample_simulation.get_current_date_and_time())
        sample_simulation.simulate_for_an_interval("1WEEK")
        sample_simulation.advance_state()
        sample_simulation.advance_time()
        after = _parse_iwfm_date(sample_simulation.get_current_date_and_time())
        assert after > before
