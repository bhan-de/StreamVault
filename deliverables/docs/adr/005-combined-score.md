# ADR-0006: Rank on a combined score of return and rating, with weak entries as a separate flag

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Bright Hanyabui

## Context

Franchises win on box office return, while standalones win on audience rating and have no weak entries. Picking one measure picks a side in the team's argument.

## Decision

Each candidate's score is the average of its percentile on return and its percentile on rating (0 to 1). Franchises are ranked against franchises, standalones against standalones. Weak entries (rated under 6.5) are shown next to each bundle, not mixed into the score.

## Alternatives considered

### Alternative A: Return leads

- **How it would work:** Rank on revenue ÷ budget.
- **Why it is attractive:** Box office is a hard number about audience size.
- **Why rejected:** It favours old, cheap films and ignores what viewers think. *Jaws* would rank 2nd despite three sequels averaging 4.9.

### Alternative B: Rating leads

- **How it would work:** Rank on TMDb rating.
- **Why it is attractive:** Closer to whether viewers enjoy a film.
- **Why rejected:** It ignores audience size. A beloved niche film would beat a broad hit.

## Consequences

- **What this buys:** A balanced score, and weak entries kept visible for negotiators.
- **What this costs:** Percentiles show rank, not size: "best" can be only slightly better.
- **What it costs the client if I am wrong:** Under return alone, franchises lead (5.1× vs 3.8×). Under rating alone, standalones lead by more (8.4 vs 7.3). The memo shows all three.
- **What would make me revisit this:** Real streaming viewing data, which should replace both proxies.

## What this survives

500 titles. Percentiles adjust to any list size. The weak line is configurable.
