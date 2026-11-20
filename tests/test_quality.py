"""Data checks flag the right films and never delete anything."""
from pathlib import Path

import pandas as pd

from streamvault.quality import check_films, summarise
from streamvault.shape import build_tables, load_payloads

MOVIES = Path(__file__).parent / "fixtures" / "movies"


def test_checks_flag_expected_films():
    tables = build_tables(load_payloads(MOVIES, pd.Series([1, 2])))
    flags = check_films(tables, cutoff_year=2000)
    by_check = flags.groupby("check")["tmdb_id"].apply(set).to_dict()
    assert by_check["single_film_collection"] == {1}   # film 1 is alone in its collection
    assert by_check["pre_cutoff_release"] == {1}       # 1995
    assert by_check["budget_missing"] == {2}           # budget 0
    assert by_check["few_votes"] == {1, 2}             # 100 and 0 votes
    assert len(tables["films"]) == 2                   # checks didn't remove anything
    assert summarise(flags, 2)["films_affected"].le(2).all()


def test_franchise_coverage_counts_missing_released_entries():
    from streamvault.quality import franchise_coverage
    from streamvault.shape import build_collection_parts
    parts = build_collection_parts(MOVIES.parent / "collections", pd.Series([10]),
                                   pd.Series([1, 2]), pd.Timestamp("2026-01-01"))
    assert parts["released"].tolist() == [True, True, False]   # Alpha 3 has no date yet
    cov = franchise_coverage(parts).iloc[0]
    assert (cov["released_films"], cov["on_list"], cov["complete"]) == (2, 1, False)
    assert cov["avg_rating_not_on_list"] == 5.0
