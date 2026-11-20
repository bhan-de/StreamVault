# ADR-0008: Keep TMDb popularity out of every KPI

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Bright Hanyabui

## Context

TMDb popularity reflects recent site activity and changes daily. *Iron Man* scores 379.6 against a median of about 17.

## Decision

Popularity is not used in any score or KPI. It's checked only as a data-quality flag.

## Alternatives considered

### Alternative A: Use popularity as "current buzz"

- **How it would work:** Add it to the combined score.
- **Why it is attractive:** Captures what's trending now.
- **Why rejected:** One spike dominates, and the ranking would change between Tuesday and Friday.

## Consequences

- **What this buys:** Stable, repeatable rankings.
- **What this costs:** No signal for current buzz.
- **What it costs the client if I am wrong:** We might miss a title that's hot right now.
- **What would make me revisit this:** A stable buzz measure (e.g. a 90-day average).

## What this survives

500 titles. Every rerun.
