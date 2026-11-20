# ADR-0004: Judge each franchise on all its released films, not just the listed ones

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Bright Hanyabui

## Context

Studios sell a franchise all or nothing. 19 of the 32 franchises on the list are incomplete, and the missing films are rated lower (6.58 vs 7.46).

## Decision

We fetch each franchise's full film list (TMDb collection endpoint, 32 calls) and the details of its 39 released films that aren't on the list. Franchises are scored on everything a studio would sell. The extra films price bundles; they are never candidates.

## Alternatives considered

### Alternative A: Judge franchises on listed films only

- **How it would work:** Use the 96 franchise films on the list.
- **Why it is attractive:** Stays within the brief's "titles you use" and needs no extra calls.
- **Why rejected:** It hides half the weak entries (10% weak instead of 20%) and overstates franchise return (5.6× instead of 5.1×). It's kept as a comparison view so the effect stays visible.

## Consequences

- **What this buys:** Bundles judged as bought, which answers the "weak middle entries" argument with data.
- **What this costs:** 71 extra calls on the first run (about 20 seconds). Goes beyond the two endpoints the brief names.
- **What it costs the client if I am wrong:** If studios sell partial bundles, franchises are slightly undervalued here. The list-only view shows the upper bound.
- **What would make me revisit this:** Studios confirming which films each bundle actually contains.

## What this survives

500 titles. New franchises are discovered automatically from each film's data.
