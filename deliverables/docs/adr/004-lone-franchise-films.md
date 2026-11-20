# ADR-0005: Count a lone franchise film as a franchise in the main view, and report the other rule

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Bright Hanyabui

## Context

Nine franchises have exactly one film on the list (*Jaws*, *The Lion King*, *Blade Runner*, …). How they're counted nearly erases the franchise lead on return.

## Decision

The main view counts them as franchise, bringing their full bundle with them. Every run also computes the standalone rule, and the memo states the difference.

## Alternatives considered

### Alternative A: Count them as standalones

- **How it would work:** Treat each lone film as a single-title purchase and ignore its sequels.
- **Why it is attractive:** Matches how they appear on the list.
- **Why rejected as the main view:** The full franchise lists show their sequels exist (e.g. three *Jaws* sequels), so a studio would most likely sell the bundle.

## Consequences

- **What this buys:** The main view matches how studios sell.
- **What this costs:** The return comparison is fragile: 5.1× vs 3.8× under this rule, 5.1× vs 5.0× under the other.
- **What it costs the client if I am wrong:** The franchise return advantage is overstated. The combined-score conclusion (standalones ahead) holds either way.
- **What would make me revisit this:** A studio offering one of these films alone.

## What this survives

500 titles. Both rules are computed automatically, every run.
