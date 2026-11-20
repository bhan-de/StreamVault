"""Shaping keeps every film exactly once and unpacks the lists correctly."""
from pathlib import Path

import pandas as pd
import pytest

from streamvault.shape import build_tables, check_tables, load_payloads

MOVIES = Path(__file__).parent / "fixtures" / "movies"
IDS = pd.Series([1, 2])     # film 1 is full; film 2 is mostly empty on purpose


@pytest.fixture
def tables():
    return build_tables(load_payloads(MOVIES, IDS))


def test_one_row_per_film(tables):
    films = tables["films"]
    assert len(films) == 2 and films["tmdb_id"].is_unique
    check_tables(tables, IDS)            # must not raise


def test_child_tables_unpack_lists(tables):
    assert len(tables["genres"]) == 2    # film 1 has 2 genres, film 2 none
    assert len(tables["cast"]) == 2
    assert len(tables["crew"]) == 2      # same person, two jobs = two rows
    assert set(tables["cast"]["tmdb_id"]) == {1}


def test_nothing_is_cleaned_here(tables):
    beta = tables["films"].set_index("tmdb_id").loc[2]
    assert beta["budget"] == 0           # 0 stays 0; the data checks decide what it means
    assert pd.isna(beta["release_date"]) # empty date becomes missing, not a crash
    assert pd.isna(beta["collection_id"])


def test_check_catches_missing_film(tables):
    with pytest.raises(AssertionError):
        check_tables(tables, pd.Series([1, 2, 3]))
