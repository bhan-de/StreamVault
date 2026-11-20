"""Step 5: franchise vs standalone, in numbers.

The KPIs (business measures) used here:
  roi            revenue / budget. A ratio, so old and new dollars compare
                 fairly (both sides of the division are in the same year's money).
  rating         TMDb audience rating (0-10).
  weak share     share of films rated below a "weak" line (set in config.toml).

Key idea: a franchise is bought as a bundle, all or nothing. So a franchise is
judged on ALL its released films, including the ones not on our list.

Everything is done with groupby / column maths, no loops over rows.
"""
from __future__ import annotations

import pandas as pd


def money_ok(films: pd.DataFrame) -> pd.Series:
    """True where budget and revenue are usable. Films that never played in
    cinemas (direct-to-video sequels) have 0 here: that's 'not applicable',
    not 'earned nothing', so they're left out of ROI but kept for ratings."""
    return films["budget"].gt(0) & films["revenue"].gt(0)


def film_pool(tables: dict[str, pd.DataFrame], single_film_rule: str, view: str) -> pd.DataFrame:
    """Build the set of films to compare, one row per film, with a 'group' column.

    single_film_rule: "franchise" -> a lone film from a franchise counts as franchise
                                     (and brings its whole bundle with it)
                      "standalone" -> it counts as a standalone; its sequels are ignored
    view:             "full_bundle" -> franchises include entries not on the list (correct)
                      "list_only"   -> only films on the list (the naive view, for comparison)
    """
    films, bundle = tables["films"], tables["bundle_films"]
    per_coll = films.groupby("collection_id")["tmdb_id"].transform("size")
    lone = films["collection_id"].notna() & per_coll.eq(1)

    standalone = films.loc[films["collection_id"].isna()]
    if single_film_rule == "standalone":
        standalone = pd.concat([standalone, films.loc[lone]])
        franchise_ids = films.loc[films["collection_id"].notna() & ~lone, "collection_id"].unique()
    else:
        franchise_ids = films["collection_id"].dropna().unique()

    if view == "full_bundle":
        franchise = bundle.loc[bundle["collection_id"].isin(franchise_ids)]
    else:
        franchise = films.loc[films["collection_id"].isin(franchise_ids)].assign(on_list=True)

    cols = ["tmdb_id", "title", "release_year", "budget", "revenue", "vote_average",
            "vote_count", "collection_id", "collection_name"]
    pool = pd.concat([standalone[cols].assign(group="standalone", on_list=True),
                      franchise[cols + ["on_list"]].assign(group="franchise")],
                     ignore_index=True)
    assert pool["tmdb_id"].is_unique, "a film landed in both groups"
    ok = money_ok(pool)
    pool["roi"] = (pool["revenue"] / pool["budget"]).where(ok)
    return pool


def compare_groups(pool: pd.DataFrame, weak_rating: float, cutoff_year: int) -> pd.DataFrame:
    """KPIs per group, for both time windows."""
    pool = pool.assign(is_weak=pool["vote_average"] < weak_rating)
    windows = {"all years": pool,
               f"{cutoff_year} onward": pool.loc[pool["release_year"] >= cutoff_year]}
    out = []
    for name, data in windows.items():          # 2 windows: a tiny fixed loop, not over rows
        kpis = data.groupby("group").agg(
            films=("tmdb_id", "size"),
            films_with_money=("roi", "count"),
            median_roi=("roi", "median"),
            median_rating=("vote_average", "median"),
            weak_share=("is_weak", "mean"),
        )
        out.append(kpis.assign(window=name).reset_index())
    return pd.concat(out, ignore_index=True)[
        ["window", "group", "films", "films_with_money", "median_roi", "median_rating", "weak_share"]
    ].round(3)


def bundle_scores(pool: pd.DataFrame, weak_rating: float) -> pd.DataFrame:
    """One row per franchise bundle: what you'd get for buying all of it.
    pooled_roi = total revenue / total budget across its films with money data."""
    fr = pool.loc[pool["group"] == "franchise"].copy()
    ok = fr["roi"].notna()
    fr["rev_ok"] = fr["revenue"].where(ok)
    fr["bud_ok"] = fr["budget"].where(ok)
    fr["is_weak"] = fr["vote_average"] < weak_rating
    b = fr.groupby(["collection_id", "collection_name"]).agg(
        films=("tmdb_id", "size"), on_list=("on_list", "sum"),
        total_revenue=("rev_ok", "sum"), total_budget=("bud_ok", "sum"),
        mean_rating=("vote_average", "mean"), worst_rating=("vote_average", "min"),
        weak_films=("is_weak", "sum"), first_year=("release_year", "min"),
    ).reset_index()
    b["pooled_roi"] = b["total_revenue"] / b["total_budget"]
    return b.sort_values("pooled_roi", ascending=False, ignore_index=True).round(2)
