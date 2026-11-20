"""Step 2 (continued): fix IMDb ids, download each film once, and write down
what happened to every line of the list."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .fetch import TMDbClient, save_payload
from .ids import DUPLICATE, IMDB_ID, TO_FETCH

IMDB_NOT_FOUND = "imdb_id_not_on_tmdb"


def resolve_imdb_ids(ledger: pd.DataFrame, client: TMDbClient) -> pd.DataFrame:
    """Turn IMDb-style ids into TMDb ids, then check if they repeat a film we
    already have. There are only one or two such lines, so a simple loop is fine."""
    ledger = ledger.copy()
    ledger["id_source"] = pd.Series("tmdb", index=ledger.index, dtype="string")
    ledger.loc[ledger["tmdb_id"].isna(), "id_source"] = pd.NA
    for idx in ledger.index[ledger["status"] == IMDB_ID]:
        imdb = ledger.at[idx, "raw_value"].strip()
        matches = client.find_imdb(imdb)
        ledger.at[idx, "id_source"] = f"translated_from_{imdb}"
        if len(matches) != 1:
            ledger.at[idx, "status"] = IMDB_NOT_FOUND
            continue
        new_id = matches[0]
        ledger.at[idx, "tmdb_id"] = new_id
        earlier = ledger.loc[(ledger["tmdb_id"] == new_id) & (ledger["status"] == TO_FETCH), "line_no"]
        if len(earlier):
            ledger.at[idx, "status"] = DUPLICATE
            ledger.at[idx, "duplicate_of_line"] = int(earlier.min())
        else:
            ledger.at[idx, "status"] = TO_FETCH
    return ledger


def fetch_all(ledger: pd.DataFrame, client: TMDbClient, raw_dir: Path) -> pd.DataFrame:
    """Download every film marked to_fetch. Gives back one row per film."""
    ids = ledger.loc[ledger["status"] == TO_FETCH, "tmdb_id"].astype(int)
    assert ids.is_unique, "to_fetch ids must be unique before fetching"
    rows = []
    for tmdb_id in ids:                      # one call per film; this part can't be vectorised
        result, payload = client.movie(tmdb_id)
        returned_id = payload.get("id") if payload else None
        if payload is not None:
            save_payload(raw_dir, tmdb_id, payload)
        rows.append({**result.__dict__, "returned_id": returned_id})
    return pd.DataFrame(rows)


def outcome_ledger(ledger: pd.DataFrame, fetched: pd.DataFrame) -> pd.DataFrame:
    """Add the download results to the list, so every line gets one final outcome."""
    merged = ledger.merge(
        fetched[["tmdb_id", "http_status", "from_cache", "error", "returned_id"]]
               .astype({"tmdb_id": "Int64"}),
        on="tmdb_id", how="left", validate="many_to_one", indicator=True)
    # Only the first copy of a film gets a download result. Repeats stay blank.
    not_fetched = merged["status"] != TO_FETCH
    merged.loc[not_fetched, ["http_status", "from_cache", "error", "returned_id"]] = pd.NA

    outcome = merged["status"].astype("string")
    is_fetch = merged["status"] == TO_FETCH
    outcome[is_fetch & (merged["http_status"] == 200)] = "fetched"
    outcome[is_fetch & (merged["http_status"] == 404)] = "not_found_on_tmdb"
    outcome[is_fetch & ~merged["http_status"].isin([200, 404])] = "fetch_error"
    merged["outcome"] = outcome
    merged["id_mismatch"] = merged["returned_id"].notna() & (merged["returned_id"] != merged["tmdb_id"])
    return merged.drop(columns="_merge")


def fetch_collections(fetched_ids: pd.Series, client: TMDbClient, movies_dir: Path,
                      collections_dir: Path) -> pd.DataFrame:
    """For every franchise that a fetched film belongs to, download the full
    list of films in it. This tells us which entries are NOT on our list.
    Gives back one row per franchise with the HTTP answer code."""
    ids = set()
    for tmdb_id in fetched_ids:          # read the collection id from each saved film
        box = json.loads((movies_dir / f"{tmdb_id}.json").read_text(encoding="utf-8")).get("belongs_to_collection")
        if box:
            ids.add(box["id"])
    rows = []
    for cid in sorted(ids):              # one call per franchise
        status, payload = client.collection(cid)
        if payload is not None:
            save_payload(collections_dir, cid, payload)
        rows.append({"collection_id": cid, "http_status": status})
    return pd.DataFrame(rows, columns=["collection_id", "http_status"])


def missing_bundle_ids(collections_dir: Path, collection_ids: pd.Series,
                       list_ids: pd.Series, as_of: pd.Timestamp) -> list[int]:
    """Released films that belong to one of our franchises but are NOT on the
    candidate list. We need their numbers to price the whole bundle."""
    missing = set()
    for cid in collection_ids:
        parts = json.loads((collections_dir / f"{int(cid)}.json").read_text(encoding="utf-8"))["parts"]
        for part in parts:
            date = pd.to_datetime(part.get("release_date") or None, errors="coerce")
            if pd.notna(date) and date <= as_of and part["id"] not in set(list_ids):
                missing.add(part["id"])
    return sorted(missing)


def fetch_bundle_extras(ids: list[int], client: TMDbClient, movies_dir: Path) -> pd.DataFrame:
    """Download the extra franchise films. They are used to price bundles only,
    never as candidates. Gives back one row per film with the answer code."""
    rows = []
    for tmdb_id in ids:
        result, payload = client.movie(tmdb_id)
        if payload is not None:
            save_payload(movies_dir, tmdb_id, payload)
        rows.append({"tmdb_id": tmdb_id, "http_status": result.http_status})
    return pd.DataFrame(rows, columns=["tmdb_id", "http_status"])
