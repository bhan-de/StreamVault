"""Scores rank the best candidate first; talent counts independent titles, not repeats."""
import pandas as pd

from streamvault.shortlist import rank_standalones, talent_signals


def test_combined_score_prefers_best_on_both():
    pool = pd.DataFrame({"tmdb_id": [1, 2, 3], "title": list("ABC"), "release_year": [2001] * 3,
                         "budget": [1] * 3, "revenue": [5, 3, 1], "roi": [5.0, 3.0, 1.0],
                         "vote_average": [8.0, 7.0, 6.0], "vote_count": [100] * 3,
                         "group": ["standalone"] * 3})
    assert rank_standalones(pool)["title"].tolist() == ["A", "B", "C"]


def test_talent_needs_independent_titles():
    scores = pd.DataFrame({"tmdb_id": [1, 2, 3, 4], "title": list("abcd"),
                           "group": ["franchise"] * 3 + ["standalone"],
                           "collection_id": pd.array([9, 9, 9, pd.NA], dtype="Int64"),
                           "film_score": [0.9, 0.8, 0.7, 0.1], "vote_average": [8, 8, 8, 5]})
    credits = pd.DataFrame({"tmdb_id": [1, 2, 3, 1, 4, 1],
                            "person_id": [10, 10, 10, 20, 20, 20],   # 20 is listed twice on film 1
                            "name": ["Franchise Only"] * 3 + ["Two Kinds"] * 3})
    out = talent_signals(scores, credits, min_films=2, min_independent=2).set_index("name")
    assert out.loc["Franchise Only", "independent_titles"] == 1
    assert not out.loc["Franchise Only", "signal"]          # 3 films, but all one franchise
    assert out.loc["Two Kinds", "films"] == 2               # duplicate credit counted once
    assert out.loc["Two Kinds", "signal"]
