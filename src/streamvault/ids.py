"""Step 1: read the list of film ids and keep track of every line in it.

Why not just use pd.read_csv? Because it quietly skips blank lines and can
change odd values. We want one row for every line in the file, so the
totals always add up to what we were given.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# The possible labels for each line.
BLANK = "blank_line"
IMDB_ID = "invalid_imdb_id"        # an IMDb id like tt1234567, not a TMDb id
INVALID = "invalid_format"         # anything else that isn't a whole number above 0
DUPLICATE = "duplicate"            # same id as an earlier line
TO_FETCH = "to_fetch"              # first time we see a good id: download it


def build_id_ledger(path: Path, id_column: str = "tmdb_id") -> pd.DataFrame:
    """Make a table with one row per line of the file, and a label for each."""
    # Read the lines ourselves. Works with Windows and Mac/Linux line endings.
    with open(path, encoding="utf-8-sig", newline=None) as fh:
        lines = fh.read().splitlines()
    header, data = lines[0].strip(), lines[1:]
    if header != id_column:
        raise ValueError(f"Expected header '{id_column}' in {path}, found '{header}'")

    ledger = pd.DataFrame({
        "line_no": pd.RangeIndex(2, len(data) + 2),   # line numbers as in the file (line 1 is the header)
        "raw_value": pd.Series(data, dtype="string"),
    })
    value = ledger["raw_value"].str.strip()

    is_blank = value.eq("")
    is_int = value.str.fullmatch(r"[1-9]\d*").fillna(False)   # a whole number above 0, not starting with 0
    is_imdb = value.str.fullmatch(r"tt\d+").fillna(False)

    ledger["tmdb_id"] = pd.to_numeric(value.where(is_int), errors="coerce").astype("Int64")

    # The first line with an id gets downloaded. Later repeats point back to it.
    first_line = (ledger.loc[is_int].groupby("tmdb_id")["line_no"].transform("min")
                  .reindex(ledger.index))   # empty for lines that aren't valid ids
    ledger["duplicate_of_line"] = first_line.where(first_line != ledger["line_no"]).astype("Int64")
    is_dup = ledger["duplicate_of_line"].notna()

    ledger["status"] = INVALID
    ledger.loc[is_int, "status"] = TO_FETCH
    ledger.loc[is_dup, "status"] = DUPLICATE
    ledger.loc[is_imdb, "status"] = IMDB_ID
    ledger.loc[is_blank, "status"] = BLANK
    return ledger


def reconcile(ledger: pd.DataFrame, expected_lines: int | None = None) -> pd.Series:
    """Count lines per label. Stop with an error if the counts don't add up."""
    counts = ledger["status"].value_counts()
    total = int(counts.sum())
    if total != len(ledger):
        raise AssertionError(f"Ledger statuses sum to {total}, but {len(ledger)} lines were read")
    if expected_lines is not None and total != expected_lines:
        raise AssertionError(f"Read {total} lines, expected {expected_lines}")
    return counts
