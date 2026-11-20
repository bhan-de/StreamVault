# Memo to Kwame

**From:** Bright Hanyabui, data engineering
**Date:** 20 November 2026
**Subject:** Back-catalog licensing: bundles or standalones, and where to put the $14M

## What I found

Your candidate list holds **112 real films**, not 127: 7 are repeats, 5 don't exist in the film database, and 3 lines are blank or invalid. Of the 32 franchises it touches, **19 appear only partly**, and the films left off are clearly weaker (average audience rating 6.6 vs 7.5 for those on the list). A studio sells the whole bundle, so I judged each franchise on every film you would actually receive.

On that basis:

| | Franchise films | Standalone films |
|---|---|---|
| Box office return (revenue ÷ budget), all years | **5.1×** | 3.8× |
| Box office return, 2000 onward | **4.5×** | 3.8× |
| Audience rating (out of 10), all years / 2000 onward | 7.3 / 7.3 | **8.4 / 8.2** |
| Share of weak films (rated under 6.5), all years / 2000 onward | 20% / 22% | **0% / 0%** |

Franchises earn more at the box office. **Standalones are better liked and carry no duds.** Weighing the two equally, standalones come out ahead in every way I tested, in both time windows.

## What I built

| What you asked for | Status | Evidence |
|---|---|---|
| A recommendation you can defend | Done | Holds in all eight views tested (two time windows × four ways of counting) |
| Shortlist: 3 franchises, 5 standalones | Done | Below, with a reason for each |
| Directors and actors as a signal | Done, with caution | Below |
| Deal note on the strongest franchise | Done | Below |
| What I couldn't verify | Done | Last section |
| Repeatable by your analyst | Done | One command, about 2 seconds on a rerun, works offline |

## What I recommend

**Make standalone hits the default, and buy a franchise only when every film in it holds up.** Bundles do bring a bigger audience, but one film in five in them is weak, and you pay for those too. When judging any bundle, including the five-film one passed on last quarter, ask first: how many of its films are weak?

**Franchises:** **1. The Lord of the Rings**: the best on both measures, all three films strong. **2. The Godfather**: high ratings and a 6.6× return, but all pre-2000. **3. Avengers**: 7.1× return across four films with no weak entry.

**Standalones:** **Schindler's List**, **Spirited Away**, **Pulp Fiction**, **The Good, the Bad and the Ugly**, **Interstellar**, each rated above 8.4 with a return between 4.5× and 32×.

**The 2000-onward view changes the shortlist (not the recommendation):** *Godfather* and three of the five standalones are older titles. Counting only films from 2000 on, the franchises become **Lord of the Rings, Avengers, Harry Potter**, and the standalones **Spirited Away, Interstellar, Inception, Memento, The Prestige**. **Lord of the Rings, Avengers, Spirited Away and Interstellar make both lists. Lead with those if Finance challenges the older titles.**

**Talent:** directors Christopher Nolan (strongest evidence: 7 films across 5 separate titles), Steven Spielberg, Robert Zemeckis, James Cameron and Quentin Tarantino; lead actors Tom Hanks, Harrison Ford, Al Pacino, Ian McKellen and Robert Downey Jr. Treat these as good track records on this list, not guarantees.

**Deal note: The Lord of the Rings.** This is the one bundle worth paying a premium for. For every dollar spent making the three films, they took in $11.00 at the box office. The typical bundle on your list took in $4.40 and the typical standalone $3.80. On that evidence, paying up to about two and a half times the per-film rate of an ordinary bundle is supported. Beyond that you would be paying for hope rather than record. All three films are post-2000, so Finance's objection doesn't apply. **The number that drove my view: 8.4, the rating of its weakest film. That's the highest floor of any franchise on the list, and it means no weak middle entry to overpay for.**

## What I could not stand behind

- **Prices.** I had no licence prices, so every value above is relative. The "2.5 times" is a ceiling based on past performance, not a quote.
- **Streaming performance.** I used box office and audience ratings as stand-ins. How these films actually perform on a streaming service isn't in the data.
- **The franchise advantage at the box office is fragile.** Nine franchises have only one film on your list (e.g. *Jaws*, *The Lion King*). If studios would sell those alone, the box office gap between franchises and standalones all but disappears (5.1× vs 5.0×).
- **Your list contains only hits.** No film on it lost money, and there are only 16 standalones. Real buying options will include weaker titles, so expect lower numbers than these.
- **Bundle contents.** I used public franchise lists. Confirm with each studio exactly which films are included.
- **Five ids** in your list don't match any film. If they were meant to be candidates, they haven't been evaluated.
