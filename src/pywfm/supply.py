"""Freeze a supply adjustment run: fixed pumping and diversion input files.

Supply adjustment (``KOPTDV`` in the simulation main file) re-solves every
time step several times to make pumping and diversions meet demand. For
runs that don't change the demand, e.g. calibrating aquifer parameters,
those supplies can be computed once and then specified as fixed input,
which cuts the Newton-Raphson iterations of every time step to one pass.

1. ``record_adjusted_supplies(model)`` runs a model instantiated for
   simulation, with supply adjustment on, and records the required pumping
   at every element pump and well and the required diversion at every
   diversion, each time step.
2. ``freeze_supply_adjustment(simulation_main_file, record)`` writes copies
   of the input files that specify those supplies as fixed data and turn
   supply adjustment off, and returns the new simulation main file.

The frozen run reproduces the adjusted run within the solver tolerance as
long as nothing it is used for changes the water demands or the stream
flow available for diversion; re-record when it does. Pumping that the
adjusted run reduced for lack of water in the aquifer is frozen at its
required (unreduced) value and is reduced again the same way.

Recording needs the handle-based fork library (IW_Model_GetPumpingRequired,
IW_Model_GetStrmDiversionDataValues).

The frozen data files are ASCII and hold values in model units per
simulation time step, as the model used them; the original data files may
be ASCII or DSS. The frozen diversion data file keeps every original column
(bypasses may refer to them) and adds one column per diversion. Each
element pump and well gets its own pumping column, because records sharing
a column split its value; those with no pumping share one zero column.

Supply adjustment changes a diversion's total and keeps the ratio between
its recoverable loss, non-recoverable loss, spill and delivery as read from
the data. A diversion whose components share one data column gets one
frozen column; one whose components use different columns gets a column
per component, from the recorded data (see _freeze_diversions).
"""
import os
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class SupplyRecord:
    """Supplies recorded from a supply adjustment run.

    Each DataFrame has one row per simulation time step (index: IWFM time
    stamps) and one column per element pump, well or diversion, in model
    order and labelled by ID (IDs may repeat: C2VSimFG gives an element's
    agricultural and urban pumping the same ID), in model volume units per
    time step. Pumping is negative for pumping and
    positive for recharge, as in a pumping data file. ``diversion_data``
    holds every column of the diversion data file as the model used it
    (numbered from 1); bypasses and other specifications may refer to them,
    so the frozen diversion data file keeps them.
    """
    element_pumping: pd.DataFrame
    well_pumping: pd.DataFrame
    diversions: pd.DataFrame
    diversion_data: pd.DataFrame


def record_adjusted_supplies(model, progress=None):
    """Run a model and record its required pumping and diversions.

    Parameters
    ----------
    model : IWFMModel
        instantiated for simulation (``is_for_inquiry=0``) at the start of
        the simulation period, with supply adjustment on
    progress : callable, optional
        called with each time stamp after it is simulated

    Returns
    -------
    SupplyRecord
    """
    elem_ids = list(model.get_element_pump_ids()) if model.get_n_element_pumps() else []
    well_ids = list(model.get_well_ids()) if model.get_n_wells() else []
    div_ids = list(model.get_diversion_ids()) if model.get_n_diversions() else []
    dates, elem, wells, divs, div_data = [], [], [], [], []
    # The same order as IW_Model_SimulateAll
    while True:
        model.advance_time()
        model.read_timeseries_data()
        model.simulate_for_one_timestep()
        dates.append(model.get_current_date_and_time())
        if elem_ids:
            elem.append(model.get_pumping_required("element_pumps"))
        if well_ids:
            wells.append(model.get_pumping_required("wells"))
        if div_ids:
            divs.append(model.get_stream_required_diversions())
            div_data.append(model.get_stream_diversion_data_values())
        model.print_results()
        model.advance_state()
        if progress is not None:
            progress(dates[-1])
        if model.is_end_of_simulation():
            break

    def frame(rows, ids):
        return pd.DataFrame(np.array(rows) if rows else np.empty((len(dates), 0)),
                            index=pd.Index(dates, name="time"), columns=ids)

    n_data = len(div_data[0]) if div_data else 0
    return SupplyRecord(frame(elem, elem_ids), frame(wells, well_ids), frame(divs, div_ids),
                        frame(div_data, list(range(1, n_data + 1))))


# ----------------------------------------------------------------------
# IWFM input file handling
# ----------------------------------------------------------------------
def _is_comment(line):
    return line[:1] in ("C", "c", "*") or not line.strip()


def _data_lines(lines):
    """Indices of the non-comment lines."""
    return [i for i, line in enumerate(lines) if not _is_comment(line)]


def _read(path):
    with open(path, encoding="latin-1") as f:
        return f.read().splitlines()


def _write(path, lines):
    with open(path, "w", encoding="latin-1", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")


def _resolve(sim_dir, value):
    """A file name in an IWFM input file, relative to the simulation directory."""
    value = value.strip().replace("\\", os.sep).replace("/", os.sep)
    return value if os.path.isabs(value) else os.path.normpath(os.path.join(sim_dir, value))


def _frozen_name(value, suffix):
    """The file name as written in the input file, with the suffix before the extension."""
    stem, ext = os.path.splitext(value.strip())
    return stem + suffix + ext


def _find_tagged(lines, tag):
    """(index, value) of the data line whose comment after '/' starts with tag."""
    for i in _data_lines(lines):
        value, sep, comment = lines[i].partition("/")
        if sep and comment.strip().upper().startswith(tag.upper()):
            return i, value.strip()
    raise ValueError(f"no '/ {tag}' entry found")


def _find_labelled(lines, label):
    """(index, value) of the data line whose comment contains label."""
    for i in _data_lines(lines):
        value, sep, comment = lines[i].partition("/")
        if sep and label.upper() in comment.upper():
            return i, value.strip()
    raise ValueError(f"no entry labelled '{label}' found")


def _replace_value(line, new_value):
    value, sep, comment = line.partition("/")
    lead = value[: len(value) - len(value.lstrip())]
    width = max(len(value) - len(lead), len(new_value) + 1)
    return lead + new_value.ljust(width) + sep + comment


def _numbers(line):
    """Leading numeric tokens of a data line, and the rest of the line."""
    body, sep, comment = line.partition("/")
    tokens = body.split()
    numbers = []
    for t in tokens:
        try:
            float(t)
        except ValueError:
            break
        numbers.append(t)
    rest = " ".join(tokens[len(numbers):])
    return numbers, rest + ((" /" + comment) if sep else "")


def _join(numbers, rest=""):
    return "   " + "  ".join(numbers) + (("   " + rest) if rest else "")


def _pumping_columns(data):
    """Data columns for pumping records (rows: time steps) and each record's
    1-based column number.

    Records whose pumping is zero throughout share one zero column; every
    other record gets its own. Records sharing a column split its value in
    proportion to their fractions (FRACSK, FRACWL), so they can't share one
    unless the value is zero.
    """
    columns, numbers, zero = [], [], None
    for j in range(data.shape[1]):
        if not np.any(data[:, j]):
            if zero is None:
                columns.append(np.zeros(data.shape[0]))
                zero = len(columns)
            numbers.append(zero)
        else:
            columns.append(data[:, j])
            numbers.append(len(columns))
    return (np.column_stack(columns) if columns else np.empty((data.shape[0], 0))), numbers


def write_time_series_file(path, data, time_stamps, title, n_column_label="NCOL",
                           per_line=10):
    """Write an ASCII IWFM time series data file (pumping or diversions).

    Values are written in model units (conversion factor 1), one row per
    time stamp, ``per_line`` values per line.
    """
    tag = n_column_label[4:] if n_column_label.startswith("NCOL") else ""
    lines = [f"C  {title}",
             "C  Written by pywfm (pywfm.supply); values in model units per time step",
             "C",
             f"    {data.shape[1]:<30d} / {n_column_label}",
             f"    {'1.0':<30s} / FACT{tag}",
             f"    {'1':<30s} / NSP{tag}",
             f"    {'0':<30s} / NFQ{tag}",
             f"    {'':<30s} / DSSFL"]
    for t, row in zip(time_stamps, data):
        values = [f"{v:.17g}" for v in row] or ["0"]
        for k in range(0, len(values), per_line):
            head = t if k == 0 else " " * len(t)
            lines.append(head + "   " + "  ".join(values[k:k + per_line]))
    _write(path, lines)


def _check_count(what, n_file, n_record):
    if n_file != n_record:
        raise ValueError(f"the {what} file has {n_file} records, the recording {n_record}")


# Records are matched with the recording by position: the model keeps them in
# file order, and IDs need not be unique (C2VSimFG gives an element's
# agricultural and urban pumping records the same ID).
def _freeze_element_pumps(lines, columns):
    """ICOLSK -> frozen column, FRACSK 1, IOPTSK 0, ICADJSK 0, ICSKMAX 0, FSKMAX 1."""
    data = _data_lines(lines)
    n = int(float(_numbers(lines[data[0]])[0][0]))
    _check_count("element pumping", n, len(columns))
    for k, i in enumerate(data[1:1 + n]):
        nums, rest = _numbers(lines[i])
        n_layers = len(nums) - 10
        if n_layers < 1:
            raise ValueError(f"unexpected element pumping record: {lines[i]!r}")
        nums[1], nums[2], nums[3] = str(columns[k]), "1.0", "0"
        nums[7 + n_layers], nums[8 + n_layers], nums[9 + n_layers] = "0", "0", "1.0"
        lines[i] = _join(nums, rest)
    return lines


def _freeze_wells(lines, columns):
    """Pumping records: ICOLWL -> frozen column, FRACWL 1, IOPTWL 0, ICADJWL 0, ICWLMAX 0, FWLMAX 1."""
    data = _data_lines(lines)
    n = int(float(_numbers(lines[data[0]])[0][0]))
    _check_count("well", n, len(columns))
    # NWELL, FACTXY, FACTRW, FACTLT, then n well locations, then n pumping records
    for k, i in enumerate(data[4 + n:4 + 2 * n]):
        nums, rest = _numbers(lines[i])
        if len(nums) != 10:
            raise ValueError(f"unexpected well pumping record: {lines[i]!r}")
        nums[1], nums[2], nums[3] = str(columns[k]), "1.0", "0"
        nums[7], nums[8], nums[9] = "0", "0", "1.0"
        lines[i] = _join(nums, rest)
    return lines


def _component_ratios(read):
    """Ratios of a diversion's components (time steps x components, delivery
    last) to their total, as the kernel keeps them: updated at every step
    with a positive total, kept otherwise (0 until the first one, which
    sends the whole diversion to delivery); delivery takes the remainder."""
    ratios = np.zeros_like(read)
    current = np.zeros(read.shape[1])
    current[-1] = 1.0
    for t, row in enumerate(read):
        total = row.sum()
        if total > 0:
            current = row / total
            current[-1] = 1.0 - current[:-1].sum()
        ratios[t] = current
    return ratios


def _freeze_diversions(lines, record, first_column):
    """Rewrite the diversion specifications for the recorded diversions.

    A diversion's recoverable loss, non-recoverable loss, spill (4.2 format)
    and delivery are each a fraction of a diversion data column. If they all
    refer to one column, their ratio is fixed and the diversion gets one
    frozen column holding the recorded diversion, with the fractions
    normalized to sum to 1. Otherwise the ratio can change between time
    steps, and each component gets its own column: the recorded diversion
    times that step's ratio (from the recorded data columns), fraction 1.
    No maximum diversion and no supply adjustment.

    Returns the rewritten lines and the new data columns (time steps x
    columns), numbered from ``first_column``.
    """
    data = _data_lines(lines)
    n = int(float(_numbers(lines[data[0]])[0][0]))
    original = record.diversion_data.to_numpy()
    _check_count("diversion specification", n, len(record.diversions.columns))
    columns = []
    for k, i in enumerate(data[1:1 + n]):
        nums, rest = _numbers(lines[i])
        if len(nums) == 14:        # ...ICOLRL FRACRL ICOLNL FRACNL TYPDSTDL DSTDL ICOLDL FRACDL ICFSIRIG ICADJ
            pairs = [(4, 5), (6, 7), (10, 11)]
        elif len(nums) == 16:      # ...with ICOLSL FRACSL after the non-recoverable loss
            pairs = [(4, 5), (6, 7), (8, 9), (12, 13)]
        else:
            raise ValueError(f"unexpected diversion record: {lines[i]!r}")
        required = record.diversions.iloc[:, k].to_numpy()
        fracs = [float(nums[f]) for _, f in pairs]
        used = {nums[c] for (c, _), f in zip(pairs, fracs) if f != 0.0}
        if len(used) <= 1:
            columns.append(required)
            column = str(first_column + len(columns) - 1)
            total = sum(fracs)
            for (c, f), frac in zip(pairs, fracs):
                nums[c] = column
                nums[f] = repr(frac / total) if total > 0 else "0.0"
        else:
            read = np.column_stack([
                original[:, int(float(nums[c])) - 1] * frac if frac != 0.0 else np.zeros(len(required))
                for (c, _), frac in zip(pairs, fracs)])
            ratios = _component_ratios(read)
            for k, (c, f) in enumerate(pairs):
                columns.append(required * ratios[:, k])
                nums[c] = str(first_column + len(columns) - 1)
                nums[f] = "1.0"
        nums[2], nums[3] = "0", "1.0"   # ICDVMAX, FDVMAX
        nums[-1] = "0"                  # ICADJ
        lines[i] = _join(nums, rest)
    new = np.column_stack(columns) if columns else np.empty((len(original), 0))
    return lines, new


def freeze_supply_adjustment(simulation_main_file, record, suffix="_frozen"):
    """Write input files that specify the recorded supplies as fixed data.

    Copies of the simulation, groundwater, pumping and stream main files,
    the element pumping, well and diversion specification files, and new
    pumping and diversion data files are written next to the originals with
    ``suffix`` added to their names; supply adjustment is turned off
    (``KOPTDV`` = 00) in the simulation main file copy. The originals are
    not changed.

    Parameters
    ----------
    simulation_main_file : str
        the simulation main input file of the recorded run
    record : SupplyRecord
        from record_adjusted_supplies
    suffix : str
        added to the name of every file written

    Returns
    -------
    str
        path of the frozen simulation main file; run it from the same
        directory as the original
    """
    sim_dir = os.path.dirname(os.path.abspath(simulation_main_file))
    stamps = list(record.element_pumping.index if len(record.element_pumping.columns)
                  else record.well_pumping.index if len(record.well_pumping.columns)
                  else record.diversions.index)
    sim_lines = _read(simulation_main_file)
    written = []

    def save(entry_value, lines):
        path = _resolve(sim_dir, _frozen_name(entry_value, suffix))
        _write(path, lines)
        written.append(path)

    # Pumping: element pumps then wells, one column each (all-zero ones share one)
    n_elem, n_wells = len(record.element_pumping.columns), len(record.well_pumping.columns)
    if n_elem or n_wells:
        gw_index, gw_value = _find_labelled(sim_lines, "GROUNDWATER COMPONENT MAIN FILE")
        gw_lines = _read(_resolve(sim_dir, gw_value))
        pump_index, pump_value = _find_tagged(gw_lines, "PUMPFL")
        pump_lines = _read(_resolve(sim_dir, pump_value))
        combined = np.hstack([record.element_pumping.to_numpy(), record.well_pumping.to_numpy()])
        unique, numbers = _pumping_columns(combined)
        elem_columns, well_columns = numbers[:n_elem], numbers[n_elem:]
        if n_elem:
            i, value = _find_tagged(pump_lines, "ELEMPUMPFL")
            save(value, _freeze_element_pumps(_read(_resolve(sim_dir, value)), elem_columns))
            pump_lines[i] = _replace_value(pump_lines[i], _frozen_name(value, suffix))
        if n_wells:
            i, value = _find_tagged(pump_lines, "WELLFL")
            save(value, _freeze_wells(_read(_resolve(sim_dir, value)), well_columns))
            pump_lines[i] = _replace_value(pump_lines[i], _frozen_name(value, suffix))
        i, value = _find_tagged(pump_lines, "PUMPFL")
        path = _resolve(sim_dir, _frozen_name(value, suffix))
        write_time_series_file(path, unique, stamps,
                               "Pumping recorded from a supply adjustment run", "NCOLPUMP")
        written.append(path)
        pump_lines[i] = _replace_value(pump_lines[i], _frozen_name(value, suffix))
        save(pump_value, pump_lines)
        gw_lines[pump_index] = _replace_value(gw_lines[pump_index], _frozen_name(pump_value, suffix))
        save(gw_value, gw_lines)
        sim_lines[gw_index] = _replace_value(sim_lines[gw_index], _frozen_name(gw_value, suffix))

    # Diversions: the original data columns as the model used them, then the
    # frozen diversion columns
    if len(record.diversions.columns):
        st_index, st_value = _find_labelled(sim_lines, "STREAM COMPONENT MAIN FILE")
        st_lines = _read(_resolve(sim_dir, st_value))
        n_data = len(record.diversion_data.columns)
        i, value = _find_tagged(st_lines, "DIVSPECFL")
        spec_lines, frozen = _freeze_diversions(_read(_resolve(sim_dir, value)), record, n_data + 1)
        save(value, spec_lines)
        st_lines[i] = _replace_value(st_lines[i], _frozen_name(value, suffix))
        i, value = _find_tagged(st_lines, "DIVFL")
        path = _resolve(sim_dir, _frozen_name(value, suffix))
        data = np.hstack([record.diversion_data.to_numpy(), frozen])
        write_time_series_file(path, data, stamps,
                               "Diversion data and diversions recorded from a supply adjustment run "
                               f"(columns 1-{n_data}: original data; then the frozen diversions)",
                               "NCOLDV")
        written.append(path)
        st_lines[i] = _replace_value(st_lines[i], _frozen_name(value, suffix))
        save(st_value, st_lines)
        sim_lines[st_index] = _replace_value(sim_lines[st_index], _frozen_name(st_value, suffix))

    i, _ = _find_tagged(sim_lines, "KOPTDV")
    sim_lines[i] = _replace_value(sim_lines[i], "00")
    stem, ext = os.path.splitext(os.path.abspath(simulation_main_file))
    out = stem + suffix + ext
    _write(out, sim_lines)
    return out
