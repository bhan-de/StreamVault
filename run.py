"""StreamVault licensing analysis: one command, top to bottom.

    python run.py     # downloads from TMDb the first time, then reuses saved answers
"""
import sys

# Check the Python version first, so an old Python gets a clear message, not a crash.
MIN_PYTHON = (3, 12)
if sys.version_info < MIN_PYTHON:
    sys.exit(f"This project needs Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer; "
             f"you are running {sys.version.split()[0]}. Install a newer Python and rebuild the .venv.")

from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from streamvault.acquire import (fetch_all, fetch_bundle_extras, fetch_collections,  # noqa: E402
                                 missing_bundle_ids, outcome_ledger, resolve_imdb_ids)  # noqa: E402
from streamvault.analysis import bundle_scores, compare_groups, film_pool  # noqa: E402
from streamvault.config import load_config, project_path          # noqa: E402
from streamvault.fetch import TMDbClient, get_token                 # noqa: E402
from streamvault.ids import build_id_ledger, reconcile               # noqa: E402
from streamvault.preflight import PreflightError, run_preflight      # noqa: E402
from streamvault.quality import check_films, franchise_coverage, list_level_facts, summarise  # noqa: E402
from streamvault.shape import (build_bundle_films, build_collection_parts, build_tables, check_tables,  # noqa: E402
                               load_payloads, write_tables)  # noqa: E402
from streamvault.shortlist import (film_scores, group_combined_scores, rank_franchises,  # noqa: E402
                                   rank_standalones, talent_signals)
from streamvault.spotcheck import automatic_check, human_sheet, pick_sample  # noqa: E402
from streamvault.timing import StageTimer                            # noqa: E402


def main() -> int:
    cfg = load_config()
    timer = StageTimer()

    with timer.stage("preflight", timed=False):
        try:
            run_preflight(cfg, need_token=True)
        except PreflightError as err:
            print(err)
            return 1

    with timer.stage("load id list + ledger"):
        ledger = build_id_ledger(project_path(cfg["input"]["id_list"]), cfg["input"]["id_column"])
        reconcile(ledger)

    # Downloading depends on the internet, so it doesn't count toward the time budget.
    api = cfg["api"]
    raw_dir = project_path(cfg["paths"]["raw_movies"])
    with timer.stage("acquire (TMDb or cache)", timed=False):
        client = TMDbClient(api["base_url"], get_token(api["token_env_vars"]),
                            project_path(cfg["paths"]["cache"]),
                            api["max_requests_per_second"], api["max_retries"])
        ledger = resolve_imdb_ids(ledger, client)
        fetched = fetch_all(ledger, client, raw_dir)
        ok_ids = fetched.loc[fetched["http_status"] == 200, "tmdb_id"]
        collections_dir = project_path(cfg["paths"]["raw_collections"])
        coll_fetch = fetch_collections(ok_ids, client, raw_dir, collections_dir)
        got = coll_fetch.loc[coll_fetch["http_status"] == 200, "collection_id"]
        as_of = pd.Timestamp(cfg["analysis"].get("as_of_date") or pd.Timestamp.today()).normalize()
        extras = fetch_bundle_extras(missing_bundle_ids(collections_dir, got, ok_ids, as_of),
                                     client, raw_dir)

    with timer.stage("ledger outcomes + write"):
        ledger = outcome_ledger(ledger, fetched)
        counts = ledger["outcome"].value_counts()
        assert counts.sum() == len(ledger), "every line must have exactly one outcome"
        out_dir = project_path(cfg["paths"]["processed"])
        out_dir.mkdir(parents=True, exist_ok=True)
        ledger.to_parquet(out_dir / "id_ledger.parquet", index=False)
        ledger.to_csv(out_dir / "id_ledger.csv", index=False)   # a copy you can open in Excel

    # Step 3: nested JSON -> flat tables. Reads local files only, so it counts toward the budget.
    with timer.stage("shape JSON into tables"):
        fetched_ids = ledger.loc[ledger["outcome"] == "fetched", "tmdb_id"].astype(int)
        tables = build_tables(load_payloads(raw_dir, fetched_ids))
        check_tables(tables, fetched_ids)
        tables["collection_parts"] = build_collection_parts(collections_dir, got, fetched_ids, as_of)
        tables["bundle_films"] = build_bundle_films(raw_dir, tables["collection_parts"])
        write_tables(tables, out_dir)

    # Step 4: data checks. They flag and count problems; they don't delete anything.
    with timer.stage("data checks"):
        flags = check_films(tables, cfg["analysis"]["modern_cutoff_year"])
        check_summary = summarise(flags, len(tables["films"]))
        facts = list_level_facts(tables["films"], ledger)
        flags.to_csv(out_dir / "quality_flags.csv", index=False)
        check_summary.to_csv(out_dir / "quality_summary.csv", index=False)
        franchise_coverage(tables["collection_parts"]).to_csv(out_dir / "franchise_coverage.csv", index=False)

    # Step 5: franchise vs standalone. Run under both single-film rules and both
    # views, so we can show whether the answer changes (it must be said loudly if so).
    with timer.stage("analysis"):
        a = cfg["analysis"]
        comparisons = []
        for rule in ("franchise", "standalone"):
            for view in ("full_bundle", "list_only"):
                pool = film_pool(tables, rule, view)
                comparisons.append(compare_groups(pool, a["weak_rating"], a["modern_cutoff_year"])
                                   .assign(single_film_rule=rule, view=view))
                comparisons[-1] = comparisons[-1].merge(
                    group_combined_scores(pool, a["modern_cutoff_year"]), on=["window", "group"],
                    how="left", validate="one_to_one")
        comparison = pd.concat(comparisons, ignore_index=True)
        bundles = bundle_scores(film_pool(tables, "franchise", "full_bundle"), a["weak_rating"])
        comparison.to_csv(out_dir / "comparison.csv", index=False)
        bundles.to_csv(out_dir / "bundle_scores.csv", index=False)

    # Step 6: shortlist and talent, on the main view (lone films = franchise, full bundles).
    with timer.stage("shortlist + talent"):
        pool = film_pool(tables, "franchise", "full_bundle")
        cutoff = a["modern_cutoff_year"]
        for label, year in (("all_years", None), (f"from_{cutoff}", cutoff)):
            rank_franchises(pool, a["weak_rating"], year).to_csv(
                out_dir / f"franchise_ranking_{label}.csv", index=False)
            rank_standalones(pool, year).to_csv(out_dir / f"standalone_ranking_{label}.csv", index=False)
        # Credits for every film in the pool, including franchise films not on the list.
        pool_credits = build_tables(load_payloads(raw_dir, pool["tmdb_id"]))
        scores = film_scores(pool)
        tl = cfg["talent"]
        crew_p, cast_p = pool_credits["crew"], pool_credits["cast"]
        directors_t = talent_signals(scores, crew_p.loc[crew_p["job"] == "Director"],
                                     tl["min_films"], tl["min_independent_titles"])
        leads_t = talent_signals(scores, cast_p.loc[cast_p["billing_order"] < tl["lead_billing_positions"]],
                                 tl["min_films"], tl["min_independent_titles"])
        directors_t.to_csv(out_dir / "talent_directors.csv", index=False)
        leads_t.to_csv(out_dir / "talent_leads.csv", index=False)

    # Spot checks: same random films every run; stop if our table disagrees with TMDb's raw data.
    with timer.stage("spot checks"):
        sc = cfg["spot_check"]
        sample = pick_sample(tables["films"], sc["sample_size"], sc["seed"])
        mismatches = automatic_check(sample, raw_dir)
        if not mismatches.empty:
            raise AssertionError(f"Spot check failed:\n{mismatches}")
        crew, cast = tables["crew"], tables["cast"]
        directors = (crew.loc[crew["job"] == "Director"].groupby("tmdb_id")["name"]
                     .agg(lambda s: " & ".join(s)))
        leads = cast.loc[cast["billing_order"] == 0].set_index("tmdb_id")["name"]
        docs_dir = project_path("docs")
        docs_dir.mkdir(exist_ok=True)
        sheet = ("# Human spot check\n\nSame random films every run (seed in config.toml). "
                 "Open each TMDb page and tick Matches? if title, year, budget, revenue, "
                 "director and lead actor agree.\n\n" + human_sheet(sample, directors, leads) + "\n")
        (docs_dir / "spot-check-sheet.md").write_text(sheet, encoding="utf-8")

    print(f"Candidate list: {len(ledger)} data lines")
    print(counts.to_string())
    print("Tables: " + ", ".join(f"{k} {len(v):,} rows" for k, v in tables.items()))
    print("\nData checks (films affected):")
    print(check_summary[["check", "films_affected"]].to_string(index=False))
    print("List facts: " + ", ".join(f"{k}={v}" for k, v in facts.items()))
    main_view = comparison.query("single_film_rule == 'franchise' and view == 'full_bundle'")
    print("\nFranchise vs standalone (main view):")
    print(main_view.drop(columns=["single_film_rule", "view"]).to_string(index=False))
    top_f = pd.read_csv(out_dir / "franchise_ranking_all_years.csv").head(3)["collection_name"].tolist()
    top_s = pd.read_csv(out_dir / "standalone_ranking_all_years.csv").head(5)["title"].tolist()
    print("Top 3 franchises (all years): " + "; ".join(top_f))
    print("Top 5 standalones (all years): " + "; ".join(top_s))
    print(f"Spot check: {len(sample)} random films compared with raw TMDb data, 0 mismatches")
    print(f"Run date used for 'released yet': {as_of.date()}  |  extra franchise films fetched: "
          f"{(extras['http_status'] == 200).sum()} of {len(extras)}")
    print(f"Network calls this run: {client.network_calls}  (0 means everything came from cache)")
    print()
    print(timer.table())

    # Pipeline KPIs: the health of this run, for employee A. Saved with each run.
    seconds = timer.computation_seconds()
    pipeline_kpis = {
        "run_date": str(as_of.date()),
        "lines_in_candidate_list": len(ledger),
        "films_analysed": int((ledger["outcome"] == "fetched").sum()),
        "share_of_lines_analysed": round(float((ledger["outcome"] == "fetched").mean()), 3),
        "fetch_errors": int((ledger["outcome"] == "fetch_error").sum()),
        "not_found_on_tmdb": int((ledger["outcome"] == "not_found_on_tmdb").sum()),
        "films_with_money_data": f"{int(pool['roi'].notna().sum())} of {len(pool)}",
        "spot_check_mismatches": len(mismatches),
        "network_calls": client.network_calls,
        "computation_seconds": round(seconds, 2),
        "within_time_budget": seconds <= cfg["budget"]["rerun_seconds"],
    }
    pd.Series(pipeline_kpis).to_csv(out_dir / "pipeline_kpis.csv", header=["value"])
    print("\nPipeline KPIs:")
    for k, v in pipeline_kpis.items():
        print(f"  {k}: {v}")

    # Timing report with the measurement boundary stated, as agreed.
    project_path("docs").mkdir(exist_ok=True)
    report = ("# Timing report (written by run.py)\n\n"
        f"Run date: {as_of.date()}. Budget: computation under {cfg['budget']['rerun_seconds']} s.\n\n"
        "**What the measurement covers:** clean, join, aggregate and write, from cached "
        "responses, excluding acquisition. Rows marked 'no' (pre-flight, fetching) are shown "
        "but not counted, because they depend on the network, not on our code.\n\n"
        "```\n" + timer.table() + "\n```\n")
    (project_path("docs") / "timing-report.md").write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
