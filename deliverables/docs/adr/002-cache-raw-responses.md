# ADR-0002: Cache every TMDb response and time only the computation

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Bright Hanyabui

## Context

 Adjoa reruns the analysis every quarter, sometimes live in a meeting. Network speed varies run to run, so timing it says nothing about the code.

## Decision

Every response (200 and 404) is stored forever in a local SQLite cache (`requests-cache`), and each film is also saved as its own JSON file. The time budget covers only the computation (clean, join, aggregate, write) from cached data, excluding acquisition.

## Alternatives considered

### Alternative A: Fetch live every run

- **How it would work:** No cache. Every run calls TMDb.
- **Why it is attractive:** Always the latest ratings.
- **Why rejected:** Slow, depends on the network in the meeting room, and numbers shift between runs for reasons unrelated to the code.

### Alternative B: Expire the cache after N days

- **How it would work:** Responses refresh automatically.
- **Why it is attractive:** Fresher data without manual steps.
- **Why rejected:** A rerun could silently change numbers mid-quarter. Refreshing should be a deliberate act (delete `data/raw/`).

## Consequences

- **What this buys:** A rerun takes under 2 seconds with 0 network calls and identical results.
- **What this costs:** Data is as of the first fetch. Fresh data needs the cache deleted.
- **What it costs the client if I am wrong:** Slightly out-of-date ratings, which are slow-moving for older films.
- **What would make me revisit this:** A need for daily-fresh data.

## What this survives

500 titles. Laptop reruns offline. The token is stripped from the cache, so the cache file is safe to keep.
