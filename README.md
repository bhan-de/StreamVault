# StreamVault back-catalog licensing analysis

## The problem

StreamVault's VP has $14M to commit to back-catalog licensing at the board review. Studios sell franchises as all-or-nothing bundles and standalone hits one at a time. His team is split on which is the better buy, and nobody brings numbers. He needs:

- a recommendation (bundles or standalones), shown for **all years** and **2000 onward**;
- a shortlist of 3 franchises and 5 standalones, each with a reason;
- which directors and lead actors signal a title worth licensing;
- a deal note on the strongest franchise;
- a plain account of what couldn't be verified.

"Good" means: every id in the candidate list accounted for, numbers that reconcile, an analysis that reruns from a clean clone without edits, inside a stated time budget, and conclusions that say what they depend on.

**Read first:** [`docs/client-memo.md`](docs/client-memo.md) (one page) and [`docs/data-findings.md`](docs/data-findings.md).

## Setup (once per machine)

Needs **Python 3.12 or newer** and git.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.lock   # exact versions of every library
cp .env.example .env               # then put your TMDb API Read Access Token after TMDB_API_TOKEN=
```

## Run

```bash
python run.py     # checks your setup, fetches what isn't cached yet, then runs every step
pytest            # offline checks; no token or internet needed
python scripts/scale_test.py   # optional: times each step at 500 / 5,000 / 50,000 films
```

The first run fetches from TMDb (under a minute for this list, about 3 minutes for 500 titles). Later runs reuse the saved answers: no internet, about 2 seconds.

At the end of each run you get: the outcome of every line, franchise vs standalone for both windows, the top shortlist, spot-check result, **pipeline KPIs** and a **timing table** (computation vs network, against the 10-second budget).

## Next year's list

Replace `data/input/id_list.csv` and run `python run.py`. Nothing else changes. All settings (2000 cutoff, weak-film line, talent thresholds, request rate, spot-check seed) are in `config.toml`. To refresh TMDb data, delete `data/raw/`.

## What's where

| Path | What it holds |
|---|---|
| `run.py` | The one command: runs every step in order and times each one |
| `config.toml` | All settings |
| `src/streamvault/ids.py` | Step 1: reads the id list and labels every line (the ledger) |
| `src/streamvault/fetch.py`, `acquire.py` | Step 2: TMDb calls (cached, rate-limited, retried), IMDb id translation, franchise lists |
| `src/streamvault/shape.py` | Step 3: nested JSON into flat tables (films, genres, cast, crew, companies, franchise parts) |
| `src/streamvault/quality.py` | Step 4: data checks; flags and counts problems, deletes nothing |
| `src/streamvault/analysis.py` | Step 5: franchise vs standalone, both windows, every counting rule |
| `src/streamvault/shortlist.py` | Step 6: combined score, shortlist, talent signals |
| `src/streamvault/spotcheck.py` | Automatic and human spot checks |
| `src/streamvault/preflight.py`, `timing.py`, `config.py` | Pre-run checks, stopwatch, settings loader |
| `tests/` | Offline tests with small made-up files |
| `scripts/scale_test.py` | How each step grows with list size |
| `docs/client-memo.md` | One-page memo for the VP |
| `docs/data-findings.md` | Every data problem, ranked by risk, with reconciliation |
| `docs/decision-notes.md`, `docs/adr/` | Every judgement call (one ADR each) and what survives at 500 titles |
| `docs/improvement.md` | The improvement beyond the brief |
| `docs/spot-check-sheet.md`, `docs/timing-report*.md` | Written by each run |
| `docs/templates/` | The review templates these documents follow |

## Outputs (`data/processed/`, rebuilt by every run)

- `id_ledger.csv`: one row per line of the candidate list and what happened to it
- `comparison.csv`: franchise vs standalone KPIs for every window, rule and view
- `franchise_ranking_*.csv`, `standalone_ranking_*.csv`: the shortlist rankings, both windows
- `talent_directors.csv`, `talent_leads.csv`: talent signals
- `franchise_coverage.csv`, `bundle_scores.csv`: bundle completeness and value
- `quality_flags.csv`, `quality_summary.csv`: data checks
- `pipeline_kpis.csv`: health of the run
