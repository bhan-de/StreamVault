# ADR-0003: Account for every line of the candidate list in a ledger

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Bright Hanyabui

## Context

The list was assembled from three sources over four years. It has a blank line, invalid values, repeats and an IMDb-format id. The rubric requires every id to be accounted for and totals to reconcile.

## Decision

We read the raw lines ourselves (not `pd.read_csv`, which skips blanks) and give each line one outcome: fetched, duplicate (pointing to the first line), invalid, blank, or not found. IMDb ids are translated through TMDb's `/find` endpoint. Ids with leading zeros are flagged as invalid rather than guessed. The run stops if the outcomes don't add up to the line count.

## Alternatives considered

### Alternative A: Read with pandas and drop bad rows

- **How it would work:** `read_csv`, `dropna`, `drop_duplicates`.
- **Why it is attractive:** Three lines of code.
- **Why rejected:** The blank line disappears without a trace (126 rows instead of 127), and nobody can say where titles went.

### Alternative B: Drop the IMDb id

- **How it would work:** Treat `tt0468569` as invalid.
- **Why it is attractive:** No extra lookup.
- **Why rejected:** It might be a real candidate. Here it turned out to be a third copy of *The Dark Knight*, which itself is a finding.

## Consequences

- **What this buys:** A line-by-line audit trail (`id_ledger.csv`) that Finance can check.
- **What this costs:** One extra API call per IMDb id.
- **What it costs the client if I am wrong:** If a "duplicate" was really two different titles typed the same, one candidate is missed. The ledger shows which lines to check.
- **What would make me revisit this:** Next year's list using a new id format.

## What this survives

500 titles with any mix of blanks, repeats and IMDb ids. Fully automatic.
