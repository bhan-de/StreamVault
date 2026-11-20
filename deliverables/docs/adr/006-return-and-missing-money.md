# ADR-0007: Measure return as revenue ÷ budget, and treat a zero budget as "not applicable"

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Bright Hanyabui

## Context

Finance distrusts pre-2000 dollars. Three direct-to-video sequels have a budget of 0.

## Decision

Return = revenue ÷ budget. Films with budget or revenue of 0 get no return value (missing, not zero) but keep their rating. Bundle return is pooled: total revenue ÷ total budget over the films with figures.

## Alternatives considered

### Alternative A: Inflation-adjust revenue

- **How it would work:** Convert every figure to today's dollars with a price index.
- **Why it is attractive:** Finance's language.
- **Why rejected:** It needs an external index (more sources to verify), and a ratio of same-year dollars already cancels most inflation.

### Alternative B: Treat 0 as 0

- **How it would work:** Return 0 for films with no box office.
- **Why it is attractive:** Simple.
- **Why rejected:** "Never in cinemas" isn't "earned nothing". It would wrongly sink the *Lion King* and *Ice Age* bundles.

## Consequences

- **What this buys:** A measure that's comparable across decades, and no fake zeros.
- **What this costs:** Bundles with direct-to-video entries are judged on fewer films (flagged).
- **What it costs the client if I am wrong:** The *Lion King* bundle's 17× could be misleading. It's flagged and not shortlisted.
- **What would make me revisit this:** Finance supplying an approved inflation index.

## What this survives

500 titles. The rule applies automatically.
