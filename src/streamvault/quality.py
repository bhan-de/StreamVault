"""Step 4: data checks. Find problems, count them, but don't hide them.

Every check returns the films it flags, so we can say exactly how many films
each problem touches. Nothing is deleted here: the analysis decides what to do
with flagged films, and the notes explain why.

All checks use whole-column operations (no loops over rows).
"""
from __future__ import annotations

import pandas as pd


def _flag(films: pd.DataFrame, mask: pd.Series, check: str, detail: pd.Series | str) -> pd.DataFrame:
    """Turn a True/False column into a small table of flagged films."""
    out = films.loc[mask, ["tmdb_id", "title"]].copy()
    out["check"] = check
    out["detail"] = detail[mask] if isinstance(detail, pd.Series) else detail
    return out


def check_films(tables: dict[str, pd.DataFrame], cutoff_year: int) -> pd.DataFrame:
    """Run every film-level check. Returns one row per (film, problem)."""
    films, cast, crew = tables["films"], tables["cast"], tables["crew"]
    flags = []

    # 1. A "collection" with only one film on our list can't be bought as a bundle
    #    of that list. Either the rest of the franchise is missing, or it isn't really one.
    per_collection = films.groupby("collection_id")["tmdb_id"].transform("size")
    flags.append(_flag(films, per_collection.eq(1), "single_film_collection",
                       "only film of '" + films["collection_name"].fillna("") + "' on the list"))

    # 2. Released before the cutoff: box office in old, non-inflation-adjusted dollars.
    flags.append(_flag(films, films["release_year"] < cutoff_year, "pre_cutoff_release",
                       "released " + films["release_year"].astype("string")))

    # 3. Figures that look like estimates (exact millions / hundred-thousands).
    flags.append(_flag(films, films["budget"].gt(0) & films["budget"].mod(1_000_000).eq(0),
                       "budget_is_round_estimate", "budget is a whole number of millions"))
    flags.append(_flag(films, films["revenue"].gt(0) & films["revenue"].mod(100_000).eq(0),
                       "revenue_is_round_estimate", "revenue is a whole number of 100k"))

    # 4. Missing or zero money figures (none today, but next year's list may have them).
    flags.append(_flag(films, films["budget"].fillna(0).le(0), "budget_missing", "budget is 0 or blank"))
    flags.append(_flag(films, films["revenue"].fillna(0).le(0), "revenue_missing", "revenue is 0 or blank"))

    # 5. Popularity far above everyone else: TMDb popularity is a "trending now"
    #    score that changes daily, so one spike can dominate any average.
    median_pop = films["popularity"].median()
    flags.append(_flag(films, films["popularity"] > 4 * median_pop, "popularity_spike",
                       "popularity " + films["popularity"].round(1).astype("string")
                       + " vs median " + str(round(median_pop, 1))))

    # 6. Few votes: a rating from a handful of people isn't reliable.
    flags.append(_flag(films, films["vote_count"] < 500, "few_votes", "fewer than 500 votes"))

    # 7. More than one director: if each gets full credit, a film counts twice in talent stats.
    directors = crew.loc[crew["job"] == "Director"]
    n_dir = films["tmdb_id"].map(directors.groupby("tmdb_id").size()).fillna(0)
    flags.append(_flag(films, n_dir > 1, "multiple_directors",
                       n_dir.astype(int).astype("string") + " directors"))
    flags.append(_flag(films, n_dir == 0, "no_director", "no director credited"))

    # 8. The same actor listed twice in one film (two roles): would double-count in talent stats.
    dup_people = cast.loc[cast.duplicated(["tmdb_id", "person_id"]), "tmdb_id"].unique()
    flags.append(_flag(films, films["tmdb_id"].isin(dup_people), "actor_listed_twice",
                       "same actor appears more than once in the cast"))

    # 9. Franchise only partly on the list: the studio sells all of it, but we only
    #    see some entries. Uses the full film lists from the collection endpoint.
    parts = tables.get("collection_parts")
    if parts is not None and not parts.empty:
        released = parts.loc[parts["released"]]
        missing = released.loc[~released["on_list"]].groupby("collection_id").size()
        n_missing = films["collection_id"].map(missing).fillna(0).astype(int)
        flags.append(_flag(films, n_missing > 0, "franchise_incomplete_on_list",
                           n_missing.astype("string") + " released entries of '"
                           + films["collection_name"].fillna("") + "' not on the list"))

    return pd.concat(flags, ignore_index=True)


def franchise_coverage(parts: pd.DataFrame) -> pd.DataFrame:
    """One row per franchise: how many released films it has, how many are on
    our list, and the average rating of the ones on vs off the list."""
    released = parts.loc[parts["released"]].copy()
    released["rating_on"] = released["vote_average"].where(released["on_list"])
    released["rating_off"] = released["vote_average"].where(~released["on_list"])
    cov = (released.groupby(["collection_id", "collection_name"])
           .agg(released_films=("tmdb_id", "size"), on_list=("on_list", "sum"),
                avg_rating_on_list=("rating_on", "mean"),
                avg_rating_not_on_list=("rating_off", "mean"))
           .reset_index())
    cov["complete"] = cov["released_films"] == cov["on_list"]
    return cov.round(2)


def list_level_facts(films: pd.DataFrame, ledger: pd.DataFrame) -> dict:
    """Facts about the list as a whole (not about single films)."""
    in_collection = films["collection_id"].notna()
    return {
        "lines_given": len(ledger),
        "films_analysed": len(films),
        "lines_lost": int((ledger["outcome"] != "fetched").sum()),
        "franchise_films": int(in_collection.sum()),
        "standalone_films": int((~in_collection).sum()),
        "collections": int(films["collection_id"].nunique()),
        "films_losing_money": int((films["revenue"] < films["budget"]).sum()),
        "lowest_vote_count": int(films["vote_count"].min()),
        "lowest_rating": float(films["vote_average"].min()),
        "newest_release_year": int(films["release_year"].max()),
    }


def summarise(flags: pd.DataFrame, n_films: int) -> pd.DataFrame:
    """One row per check: how many films it touches, and a few examples."""
    summary = (flags.groupby("check")
               .agg(films_affected=("tmdb_id", "nunique"),
                    examples=("title", lambda s: "; ".join(s.head(4))))
               .reset_index())
    summary["share_of_films"] = (summary["films_affected"] / n_films).round(3)
    return summary.sort_values("films_affected", ascending=False, ignore_index=True)
