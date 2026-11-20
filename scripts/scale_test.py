"""How does each step grow? Time the computation steps on copies of the real data.

We copy the real films many times (giving each copy new ids, and each copied
franchise a new id) to reach a bigger list, then time each step. The copied
films are fake for analysis purposes but realistic for timing, because they
have the same shape as real TMDb answers (same nested lists, same sizes).

Network time is NOT measured here: fetching grows one call per film, and the
cache takes it out of reruns.

Run:  python scripts/scale_test.py            (writes docs/timing-report-scaling.md)
"""
from __future__ import annotations

import copy
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from streamvault.analysis import bundle_scores, compare_groups, film_pool   # noqa: E402
from streamvault.config import load_config, project_path                    # noqa: E402
from streamvault.quality import check_films                                 # noqa: E402
from streamvault.shape import build_films, build_tables, load_payloads      # noqa: E402
from streamvault.shortlist import film_scores, rank_franchises, talent_signals  # noqa: E402

OFFSET = 10_000_000          # new ids for copies: id + k * OFFSET
TARGETS = [500, 5_000, 50_000]


def copies(payloads: list[dict], n_films: int) -> list[dict]:
    """Make n_films payloads by copying the real ones with fresh ids."""
    out = []
    k = 0
    while len(out) < n_films:
        for p in payloads:
            if len(out) == n_films:
                break
            q = copy.copy(p)                      # shallow copy: nested lists are shared, fine for reading
            q["id"] = p["id"] + k * OFFSET
            if p.get("belongs_to_collection"):
                q["belongs_to_collection"] = {**p["belongs_to_collection"],
                                              "id": p["belongs_to_collection"]["id"] + k * OFFSET}
            out.append(q)
        k += 1
    return out


def time_steps(list_payloads: list[dict], bundle_payloads: list[dict], cfg: dict) -> dict:
    a, tl = cfg["analysis"], cfg["talent"]
    t = {}
    start = time.perf_counter()
    tables = build_tables(list_payloads)
    t["shape JSON into tables"] = time.perf_counter() - start

    start = time.perf_counter()
    films_b = build_films(bundle_payloads)
    list_ids = set(tables["films"]["tmdb_id"])
    films_b["on_list"] = films_b["tmdb_id"].isin(list_ids)
    tables["bundle_films"] = films_b
    tables["collection_parts"] = films_b.assign(released=True)[
        ["collection_id", "collection_name", "tmdb_id", "title", "release_date",
         "vote_average", "vote_count", "on_list", "released"]]
    t["build bundle tables"] = time.perf_counter() - start

    start = time.perf_counter()
    check_films(tables, a["modern_cutoff_year"])
    t["data checks"] = time.perf_counter() - start

    start = time.perf_counter()
    pool = film_pool(tables, "franchise", "full_bundle")
    compare_groups(pool, a["weak_rating"], a["modern_cutoff_year"])
    bundle_scores(pool, a["weak_rating"])
    t["analysis"] = time.perf_counter() - start

    start = time.perf_counter()
    rank_franchises(pool, a["weak_rating"])
    scores = film_scores(pool)
    crew = tables["crew"]
    talent_signals(scores, crew.loc[crew["job"] == "Director"], tl["min_films"], tl["min_independent_titles"])
    t["shortlist + talent"] = time.perf_counter() - start
    t["rows: films / crew"] = f"{len(tables['films']):,} / {len(tables['crew']):,}"
    return t


def to_markdown(table: pd.DataFrame) -> str:
    """Small Markdown table writer (avoids adding another library)."""
    head = "| step | " + " | ".join(table.columns) + " |"
    rule = "|---|" + "---|" * len(table.columns)
    rows = ["| " + idx + " | " + " | ".join(str(v) for v in row) + " |" for idx, row in table.iterrows()]
    return "\n".join([head, rule, *rows])


def main() -> None:
    cfg = load_config()
    movies = project_path(cfg["paths"]["raw_movies"])
    films = pd.read_parquet(project_path(cfg["paths"]["processed"]) / "films.parquet")
    bundle = pd.read_parquet(project_path(cfg["paths"]["processed"]) / "bundle_films.parquet")
    real_list = load_payloads(movies, films["tmdb_id"])
    real_extra = load_payloads(movies, bundle.loc[~bundle["on_list"], "tmdb_id"])
    for p in real_extra:          # extras need their franchise id (bundle table has it)
        cid = bundle.set_index("tmdb_id").loc[p["id"], "collection_id"]
        p.setdefault("belongs_to_collection", {"id": int(cid), "name": ""})

    results = {}
    for n in [len(real_list)] + TARGETS:
        factor = n / len(real_list)
        lst = copies(real_list, n)
        extra = copies(real_extra, round(len(real_extra) * factor))
        results[n] = time_steps(lst, lst + extra, cfg)
        print(f"{n:>6} films done", flush=True)

    table = pd.DataFrame(results)
    table.columns = [f"{c:,} films" for c in table.columns]
    for col in table.columns:
        table[col] = [f"{v:.3f} s" if isinstance(v, float) else v for v in table[col]]
    md = ("# Scaling test\n\nComputation only, from data already in memory "
          "(no network, no disk reads). Copies of the real films with new ids.\n\n"
          + to_markdown(table) + "\n")
    (ROOT / "docs" / "timing-report-scaling.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
