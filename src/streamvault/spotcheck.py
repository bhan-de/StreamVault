"""Spot checks: pick a few films at random and make sure our tables tell the truth.

Two kinds:
  automatic  compare each value in our films table with the raw JSON TMDb sent.
             If shaping ever garbles a number, this catches it on every run.
  human      write a short sheet of the same random films with a link to each
             TMDb page, so a person can compare by eye (docs/spot-check.md).

The random pick uses a fixed seed, so it's the same films every run
(change the seed in config.toml to pick a fresh set).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

FIELDS = {  # our column -> where it sits in TMDb's JSON
    "title": ("title",), "budget": ("budget",), "revenue": ("revenue",),
    "vote_average": ("vote_average",), "vote_count": ("vote_count",),
    "collection_id": ("belongs_to_collection", "id"),
}


def pick_sample(films: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    return films.sample(n=min(n, len(films)), random_state=seed).sort_values("title")


def _dig(payload: dict, path: tuple) -> object:
    for key in path:
        payload = payload.get(key) if isinstance(payload, dict) else None
    return payload


def automatic_check(sample: pd.DataFrame, movies_dir: Path) -> pd.DataFrame:
    """One row per (film, field) where our table differs from the raw JSON."""
    problems = []
    for _, film in sample.iterrows():   # a handful of sampled films only
        raw = json.loads((movies_dir / f"{film['tmdb_id']}.json").read_text(encoding="utf-8"))
        for col, path in FIELDS.items():
            ours, theirs = film[col], _dig(raw, path)
            same = (pd.isna(ours) and theirs is None) or ours == theirs
            if not same:
                problems.append({"tmdb_id": film["tmdb_id"], "field": col,
                                 "our_value": ours, "raw_value": theirs})
    return pd.DataFrame(problems, columns=["tmdb_id", "field", "our_value", "raw_value"])


def human_sheet(sample: pd.DataFrame, director_names: pd.Series, lead_names: pd.Series) -> str:
    """A Markdown table to fill in by hand while looking at each TMDb page."""
    lines = ["| Film | Year | Budget | Revenue | Director | Lead actor | TMDb page | Matches? |",
             "|---|---|---|---|---|---|---|---|"]
    for _, f in sample.iterrows():
        lines.append(
            f"| {f['title']} | {f['release_year']} | ${f['budget']:,} | ${f['revenue']:,} | "
            f"{director_names.get(f['tmdb_id'], '?')} | {lead_names.get(f['tmdb_id'], '?')} | "
            f"https://www.themoviedb.org/movie/{f['tmdb_id']} | |")
    return "\n".join(lines)
