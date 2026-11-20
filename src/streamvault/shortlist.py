"""Step 6: the shortlist (3 franchises, 5 standalones) and the talent signals.

Combined score (chosen by kasper): for each candidate, where it ranks on
return (revenue / budget) and where it ranks on audience rating, each as a
percentile from 0 to 1, then the average of the two. 1.0 = best on both.
Franchises are ranked against franchises, standalones against standalones,
because they are bought differently.

Weak entries (films rated under the weak line) are shown next to each
franchise as a risk flag, not baked into the score, so a negotiator can see it.
"""
from __future__ import annotations

import pandas as pd

from .analysis import bundle_scores


def _combined(roi: pd.Series, rating: pd.Series) -> pd.Series:
    return ((roi.rank(pct=True) + rating.rank(pct=True)) / 2).round(3)


def rank_franchises(pool: pd.DataFrame, weak_rating: float, from_year: int | None = None) -> pd.DataFrame:
    """Score every franchise bundle. from_year: only count films from that year on
    (for the 2000-onward window); None = all years."""
    if from_year is not None:
        pool = pool.loc[pool["release_year"] >= from_year]
    b = bundle_scores(pool, weak_rating)
    fr = pool.loc[pool["group"] == "franchise"]
    extra = fr.groupby("collection_id").agg(
        films_with_money=("roi", "count"),
        pre_2000_share=("release_year", lambda y: (y < 2000).mean()))
    b = b.merge(extra, on="collection_id", how="left", validate="one_to_one")
    b["score"] = _combined(b["pooled_roi"], b["mean_rating"])
    # Flag bundles whose return rests on only some of their films.
    b["money_data_incomplete"] = b["films_with_money"] < b["films"]
    return b.sort_values(["score", "mean_rating"], ascending=False, ignore_index=True)


def rank_standalones(pool: pd.DataFrame, from_year: int | None = None) -> pd.DataFrame:
    s = pool.loc[pool["group"] == "standalone"]
    if from_year is not None:
        s = s.loc[s["release_year"] >= from_year]
    s = s.assign(score=_combined(s["roi"], s["vote_average"]))
    cols = ["tmdb_id", "title", "release_year", "budget", "revenue", "roi",
            "vote_average", "vote_count", "score"]
    return s.sort_values(["score", "vote_average"], ascending=False, ignore_index=True)[cols]


def film_scores(pool: pd.DataFrame) -> pd.DataFrame:
    """Combined score for every single film in the pool (franchise and standalone
    together), used to judge talent. Films without money data get no score."""
    has_money = pool["roi"].notna()
    scored = pool.loc[has_money].copy()
    scored["film_score"] = _combined(scored["roi"], scored["vote_average"])
    return scored[["tmdb_id", "title", "group", "collection_id", "film_score", "vote_average"]]


def talent_signals(scores: pd.DataFrame, credits: pd.DataFrame, min_films: int,
                   min_independent: int) -> pd.DataFrame:
    """For each person: how many films, how many INDEPENDENT ones, and how good
    their films score on average.

    independent = number of different franchises they worked on, counting each
    standalone as its own. Daniel Radcliffe has 8 films but 1 independent one
    (all Harry Potter), so his record mostly says "Harry Potter is strong",
    not "Radcliffe is a signal". We only call someone a signal with at least
    `min_independent` independent titles.
    """
    # One row per person per film (drop repeats, e.g. two roles in one film),
    # then join the film's score. validate= stops the run if the join would copy films.
    people = credits.drop_duplicates(["tmdb_id", "person_id"])
    joined = people.merge(scores, on="tmdb_id", how="inner", validate="many_to_one")
    joined["franchise_key"] = joined["collection_id"].astype("string").fillna(
        "solo_" + joined["tmdb_id"].astype("string"))
    median = scores["film_score"].median()
    joined["above_median"] = joined["film_score"] > median
    out = joined.groupby(["person_id", "name"]).agg(
        films=("tmdb_id", "nunique"),
        independent_titles=("franchise_key", "nunique"),
        mean_film_score=("film_score", "mean"),
        share_above_median=("above_median", "mean"),
        titles=("title", lambda t: "; ".join(sorted(t)[:6])),
    ).reset_index()
    out["signal"] = (out["films"] >= min_films) & (out["independent_titles"] >= min_independent)
    return out.sort_values(["signal", "mean_film_score"], ascending=False, ignore_index=True).round(3)


def group_combined_scores(pool: pd.DataFrame, cutoff_year: int) -> pd.DataFrame:
    """Average combined score of franchise films vs standalone films, both windows.
    This is the headline comparison under the combined score."""
    scored = film_scores(pool).merge(pool[["tmdb_id", "release_year"]], on="tmdb_id",
                                     validate="one_to_one")
    rows = []
    for name, data in (("all years", scored),
                       (f"{cutoff_year} onward", scored.loc[scored["release_year"] >= cutoff_year])):
        g = data.groupby("group")["film_score"].agg(["mean", "size"]).reset_index()
        rows.append(g.assign(window=name))
    return (pd.concat(rows, ignore_index=True)
            .rename(columns={"mean": "mean_combined_score", "size": "films_scored"})
            [["window", "group", "films_scored", "mean_combined_score"]].round(3))
