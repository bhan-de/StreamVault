"""The automatic spot check catches a value that doesn't match the raw JSON."""
from pathlib import Path

import pandas as pd

from streamvault.shape import build_tables, load_payloads
from streamvault.spotcheck import automatic_check

MOVIES = Path(__file__).parent / "fixtures" / "movies"


def test_clean_tables_pass_and_tampered_value_is_caught():
    films = build_tables(load_payloads(MOVIES, pd.Series([1, 2])))["films"]
    assert automatic_check(films, MOVIES).empty
    films.loc[films["tmdb_id"] == 1, "budget"] = 999       # pretend shaping broke a number
    problems = automatic_check(films, MOVIES)
    assert problems[["tmdb_id", "field"]].values.tolist() == [[1, "budget"]]
