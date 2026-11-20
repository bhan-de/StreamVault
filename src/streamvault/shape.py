"""Step 3: turn the nested JSON of each film into flat tables.

Each TMDb answer is one big nested document: a film, with lists inside it
(genres, cast, crew, companies) and a small "collection" box (the franchise).
Tables are easier to analyse, so we split it up. Each table has one clear
meaning per row:

  films      one row per film            (key: tmdb_id)
  genres     one row per film + genre
  cast       one row per film + actor    (order 0 = top-billed actor)
  crew       one row per film + person + job
  companies  one row per film + production company
  collection_parts  one row per franchise + film in it (from the collection
                    endpoint), including films that are NOT on our list

Important: this step does NOT fix or drop anything. A budget of 0 stays 0.
Deciding what is a real problem belongs in the data checks (quality.py),
so every change to the data is visible in one place.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# Plain columns we keep from each film (everything except the nested lists).
FILM_COLUMNS = [
    "id", "title", "original_title", "release_date", "status", "runtime",
    "budget", "revenue", "vote_average", "vote_count", "popularity",
    "original_language", "imdb_id", "adult",
    "belongs_to_collection.id", "belongs_to_collection.name",
]


def load_payloads(raw_dir: Path, ids: pd.Series) -> list[dict]:
    """Read the saved JSON for exactly these ids.
    We go by the ledger's list, not by "every file in the folder", so an old
    file left over from an earlier list can never sneak into the analysis."""
    return [json.loads((raw_dir / f"{i}.json").read_text(encoding="utf-8")) for i in ids]


def _child_table(payloads: list[dict], path: list[str], keep: dict[str, str]) -> pd.DataFrame:
    """Flatten one nested list (like credits -> cast) into a table.
    json_normalize does the unpacking; 'meta' copies the film id onto each row.
    'keep' picks the columns we want and gives them clear names."""
    table = pd.json_normalize(payloads, record_path=path, meta=["id"], meta_prefix="film_")
    if table.empty:
        return pd.DataFrame(columns=["tmdb_id", *keep.values()])
    table = table.rename(columns={"film_id": "tmdb_id", **keep})
    return table[["tmdb_id", *keep.values()]]


def build_films(payloads: list[dict]) -> pd.DataFrame:
    """One row per film with its plain columns."""
    # json_normalize turns the collection box into two plain columns.
    films = pd.json_normalize(payloads)
    for col in FILM_COLUMNS:            # a film without a collection may lack these columns
        if col not in films:
            films[col] = pd.NA
    films = films[FILM_COLUMNS].rename(columns={
        "id": "tmdb_id",
        "belongs_to_collection.id": "collection_id",
        "belongs_to_collection.name": "collection_name",
    })
    # Dates: an empty or broken date becomes NaT (missing), it doesn't crash.
    films["release_date"] = pd.to_datetime(films["release_date"].replace("", pd.NA), errors="coerce")
    films["release_year"] = films["release_date"].dt.year.astype("Int64")
    films["collection_id"] = films["collection_id"].astype("Int64")
    return films


def build_tables(payloads: list[dict]) -> dict[str, pd.DataFrame]:
    films = build_films(payloads)
    genres = _child_table(payloads, ["genres"], {"id": "genre_id", "name": "genre"})
    cast = _child_table(payloads, ["credits", "cast"],
                        {"id": "person_id", "name": "name", "character": "character",
                         "order": "billing_order"})
    crew = _child_table(payloads, ["credits", "crew"],
                        {"id": "person_id", "name": "name", "department": "department", "job": "job"})
    companies = _child_table(payloads, ["production_companies"],
                             {"id": "company_id", "name": "company"})
    return {"films": films, "genres": genres, "cast": cast, "crew": crew, "companies": companies}


def check_tables(tables: dict[str, pd.DataFrame], expected_ids: pd.Series) -> None:
    """Prove the shaping kept every film exactly once. Stops the run if not."""
    films = tables["films"]
    if not films["tmdb_id"].is_unique:
        raise AssertionError("films table has a film more than once")
    if set(films["tmdb_id"]) != set(expected_ids):
        raise AssertionError("films table doesn't match the ledger's fetched films")
    for name, table in tables.items():
        if name != "films" and not table["tmdb_id"].isin(films["tmdb_id"]).all():
            raise AssertionError(f"{name} has rows for a film that isn't in films")


def write_tables(tables: dict[str, pd.DataFrame], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_parquet(out_dir / f"{name}.parquet", index=False)


def build_collection_parts(collections_dir: Path, collection_ids: pd.Series,
                           list_ids: pd.Series, as_of: pd.Timestamp) -> pd.DataFrame:
    """Flatten each franchise's full film list into one table.
    on_list: is this film one of our candidates?
    released: has it come out yet (as of the run date)? Unreleased or
    announced films can't be licensed, so the analysis leaves them out."""
    payloads = [json.loads((collections_dir / f"{int(c)}.json").read_text(encoding="utf-8"))
                for c in collection_ids]
    parts = pd.json_normalize(payloads, record_path="parts", meta=["id", "name"],
                              meta_prefix="collection_")
    parts = parts.rename(columns={"id": "tmdb_id"})
    parts = parts[["collection_id", "collection_name", "tmdb_id", "title", "release_date",
                   "vote_average", "vote_count"]]
    parts["release_date"] = pd.to_datetime(parts["release_date"].replace("", pd.NA), errors="coerce")
    parts["on_list"] = parts["tmdb_id"].isin(list_ids)
    parts["released"] = parts["release_date"].notna() & (parts["release_date"] <= as_of)
    return parts


def build_bundle_films(movies_dir: Path, parts: pd.DataFrame) -> pd.DataFrame:
    """Every released film of every franchise we touch, with money and ratings.
    This is what a studio would actually sell as the bundle."""
    released = parts.loc[parts["released"]]
    have = released["tmdb_id"].map(lambda i: (movies_dir / f"{i}.json").exists())
    films = build_films(load_payloads(movies_dir, released.loc[have, "tmdb_id"]))
    films = films.drop(columns=["collection_id", "collection_name"]).merge(
        released[["tmdb_id", "collection_id", "collection_name", "on_list"]],
        on="tmdb_id", how="left", validate="one_to_one")
    return films
