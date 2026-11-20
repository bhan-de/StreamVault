"""The comparison puts every film in exactly one group and handles missing money."""
import pandas as pd

from streamvault.analysis import compare_groups, film_pool


def _tables():
    films = pd.DataFrame({
        "tmdb_id": [1, 2, 3], "title": ["Solo", "F1", "Lone"], "release_year": [1995, 2005, 2010],
        "budget": [10, 10, 10], "revenue": [50, 30, 20], "vote_average": [8.0, 7.0, 6.0],
        "vote_count": [1000] * 3, "collection_id": pd.array([pd.NA, 7, 8], dtype="Int64"),
        "collection_name": [None, "F", "L"]})
    films.loc[films["tmdb_id"] == 1, "collection_name"] = None
    bundle = pd.DataFrame({  # franchise F has a weak sequel (id 4) not on the list, with no money data
        "tmdb_id": [2, 4, 3], "title": ["F1", "F2", "Lone"], "release_year": [2005, 2008, 2010],
        "budget": [10, 0, 10], "revenue": [30, 0, 20], "vote_average": [7.0, 5.0, 6.0],
        "vote_count": [1000] * 3, "collection_id": pd.array([7, 7, 8], dtype="Int64"),
        "collection_name": ["F", "F", "L"], "on_list": [True, False, True]})
    return {"films": films, "bundle_films": bundle}


def test_full_bundle_brings_in_missing_entries():
    pool = film_pool(_tables(), "franchise", "full_bundle")
    assert pool["tmdb_id"].is_unique
    assert set(pool.loc[pool["group"] == "franchise", "tmdb_id"]) == {2, 3, 4}
    assert pd.isna(pool.set_index("tmdb_id").loc[4, "roi"])   # 0 budget -> no ROI, not ROI 0


def test_single_film_rule_moves_lone_film():
    # Films 2 and 3 are each the only list film of their franchise, so both move.
    pool = film_pool(_tables(), "standalone", "full_bundle")
    assert set(pool.loc[pool["group"] == "standalone", "tmdb_id"]) == {1, 2, 3}
    assert 4 not in set(pool["tmdb_id"])   # the unlisted sequel is ignored under this rule


def test_windows_and_weak_share():
    out = compare_groups(film_pool(_tables(), "franchise", "full_bundle"), 6.5, 2000)
    fr_all = out.query("window == 'all years' and group == 'franchise'").iloc[0]
    assert fr_all["films"] == 3 and fr_all["films_with_money"] == 2
    assert round(fr_all["weak_share"], 3) == round(2 / 3, 3)   # ratings 6.0 and 5.0 are weak
    assert "standalone" not in set(out.query("window == '2000 onward'")["group"])  # Solo is 1995
