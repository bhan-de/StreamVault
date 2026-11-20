# Data findings — StreamVault back-catalog licensing

## Summary

Kwame asked one question: franchise bundles or standalone hits? He has $14M to commit. The data has to support that answer, a shortlist (3 franchises, 5 standalones), a read on talent, and a deal note.

The candidate list (127 lines) holds 112 real, distinct films. The other 15 lines are blanks, invalid values, repeats or ids TMDb doesn't recognise. The film data itself is mostly clean. **The serious problems are in what the list leaves out and how "franchise" gets defined, not in messy values.** Three findings move the recommendation:

1. **The list hides the weak half of most franchises.** 19 of 32 franchises are only partly on the list, and the 39 missing films are rated much lower. Judged on the list alone, franchises look better than what a studio would actually sell.
2. **Nine "franchises" have only one film on the list.** Whether those count as franchise or standalone nearly erases the franchise advantage on box office return.
3. **The list contains only hits.** No film lost money, and the standalone group is small (16 films, 8 since 2000). Every average flatters both sides, standalones most of all.

Under the agreed combined score (box office return and audience rating ranked equally), standalones come out ahead in every view we tested. Only a few complete, consistently strong franchises hold their own.

All figures come from `python run.py` and are reproducible (run date 2026-11-20).

## Reconciliation

| Stage | Rows | Delta | Reason |
|---|---|---|---|
| Lines in id_list.csv | 127 | | Matches the brief's 127 |
| Non-blank lines | 126 | −1 | Line 69 is empty. A plain `pd.read_csv` skips it silently and reports 126 |
| Valid-format ids | 124 | −2 | `-1` (line 30) and `N/A` (line 111). `tt0468569` (line 95) is an IMDb id: translated, not dropped |
| Distinct films | 117 | −7 | 6 ids appear more than once (155, 1891, 278, 550, 603, 680). The translated IMDb id is TMDb 155, a third copy of *The Dark Knight* |
| Found on TMDb | 112 | −5 | 8471293, 8471294, 9412887, 9412888, 7733901 return "not found" (404) |
| Films table after shaping | 112 | 0 | Join checked one-to-one; no film dropped or duplicated |
| Analysis pool (main view) | 151 | +39 | Released films of our franchises that are not on the list, added so each bundle is judged whole. Used for pricing bundles only, never as candidates |
| Films with usable money data | 148 | −3 | Three direct-to-video sequels have no box office (budget 0). Kept for ratings, left out of return |
| Main-view groups | 135 franchise + 16 standalone | = 151 | Every film in exactly one group (checked in code) |

Every one of the 127 lines has exactly one outcome in `data/processed/id_ledger.csv`: 112 fetched, 7 duplicate, 5 not found, 2 invalid, 1 blank.

## Findings, ranked by risk

Risk = how far the finding can move Kwame's recommendation or shortlist, times how much of it we could not fix.

### F-01: Franchises are only partly on the list, and the missing films are the weak ones — Severity: High

- **What it is:** A franchise is sold all or nothing, but the list shows only some entries for 19 of the 32 franchises it touches.
- **How I detected it:** I fetched each franchise's full film list from TMDb's collection endpoint and compared it with the list. Check `franchise_incomplete_on_list` in `quality.py`; output `franchise_coverage.csv`.
- **Scale:** 48 of 112 list films sit in incomplete franchises. 39 released films are missing; they average a rating of **6.58**, against **7.46** for the entries on the list. Examples: *Jaws* (7.7) is on the list, while its three sequels average 4.9. *A Good Day to Die Hard*, *Terminator Genisys* and *Terminator: Dark Fate* are missing.
- **Effect on the client's number:** Judged on the list alone, franchises show a median return of 5.6× and 10% weak entries. Judged on the full bundles, it's **5.1× and 20% weak entries**. The share of weak entries doubles.
- **What I did about it:** I judge every franchise on all its released films (39 extra fetches, used for pricing only). Both views are kept in `comparison.csv` so the effect stays visible.
- **Residual risk:** TMDb's collection lists are community-maintained. A studio's actual bundle may include or exclude films differently (spin-offs, TV films). Bundle contents must be confirmed with each studio.

### F-02: Nine "franchises" have one film on the list — Severity: High

- **What it is:** TMDb puts *Jaws*, *The Lion King*, *Blade Runner*, *The Silence of the Lambs* and 5 others in collections, but only one film of each is a candidate.
- **How I detected it:** Check `single_film_collection` (collection size on the list = 1).
- **Scale:** 9 films (8% of the list), mostly strong, famous titles.
- **Effect on the client's number:** In the main view they count as franchise and bring their sequels with them. Franchise return is 5.1× vs 3.8× for standalones (all years). If they count as standalones, the gap almost disappears: **5.1× vs 5.0×**, and **4.6× vs 4.5×** from 2000. On the combined score, standalones still lead either way (0.67 vs 0.48 in the main view; 0.63 vs 0.47 under the alternative).
- **What I did about it:** Both rules run on every run. The main view treats them as franchise, because a studio would sell the bundle (ADR-0005).
- **Residual risk:** If a studio would sell *Jaws* alone, it belongs in the standalone pool, which would then look stronger on return.

### F-03: The list contains only hits — Severity: High (cannot be fixed from this data)

- **What it is:** The list is a selection of famous successes, not a sample of what StreamVault could license.
- **How I detected it:** List-level facts in `quality.py`: no film earned less than its budget, the fewest votes on any film is 4,138, the lowest rating is 5.75, and the newest film is from 2019.
- **Scale:** All 112 films. The standalone group is 16 films (8 from 2000 on), all considered classics (*Shawshank*, *Pulp Fiction*, *Schindler's List*).
- **Effect on the client's number:** Averages look better than a real buying pool would. Standalones' "0% weak entries" partly reflects how the list was put together, not something standalones guarantee.
- **What I did about it:** Medians instead of means. Weak entries shown as an explicit flag. The caveat goes in the memo.
- **Residual risk:** A small standalone group means one or two films can shift its medians. The recommendation is directionally robust (it holds in all 8 views) but its size is uncertain.

### F-04: 41 films were released before 2000 — Severity: Medium-High

- **What it is:** Box office from decades ago is in old dollars and was reported differently (Finance's concern).
- **How I detected it:** Check `pre_cutoff_release`.
- **Scale:** 41 of 112 list films (37%). Two shortlisted franchises (*Godfather*, *Back to the Future*) are entirely pre-2000, as are 3 of the 5 all-years standalones.
- **Effect on the client's number:** The direction of the comparison doesn't change between windows, but the shortlist does. From 2000 on: franchises *Lord of the Rings*, *Avengers*, *Harry Potter*; standalones *Spirited Away*, *Interstellar*, *Inception*, *Memento*, *The Prestige*.
- **What I did about it:** I use return (revenue ÷ budget), a ratio of two numbers from the same year, so inflation largely cancels out. Every result is shown for both windows.
- **Residual risk:** The ratio doesn't fix differences in how revenue was reported back then (e.g. re-releases folded in: *Star Wars* shows 70× return).

### F-05: Repeated, invalid and unknown ids in the candidate list — Severity: Medium

- **What it is:** 15 of 127 lines can't be used as distinct films.
- **How I detected it:** The id ledger (`ids.py`) reads raw lines, labels each one, and checks that the counts add up; TMDb's answers fill in the rest.
- **Scale:** 7 repeats, 5 not found, 2 invalid, 1 blank. One repeat came through an IMDb id, a sign that the three source lists used different id systems.
- **Effect on the client's number:** Half of the repeated films are standalones (*Pulp Fiction*, *Shawshank*, *Fight Club*). Counted twice, the standalone group grows from 16 to 19 and its median return falls from 3.8× to 3.2×. The 5 unknown ids are titles we can't evaluate at all.
- **What I did about it:** Each film is fetched and counted once. Repeats point to their first line, and the 5 unknown ids are listed by line number.
- **Residual risk:** We can't tell what the 5 unknown ids were meant to be. They come in near-pairs (8471293/8471294, 9412887/9412888), which suggests typing errors or placeholders. Up to 5 candidates may be missing from the evaluation.

### F-06: Direct-to-video sequels have no box office figures — Severity: Medium

- **What it is:** *The Lion King 1½*, *The Lion King II* and *The Ice Age Adventures of Buck Wild* never played in cinemas, so their budget is 0 (and the revenue shows $1,465 or $0).
- **How I detected it:** I reviewed the money figures of the 39 extra franchise films.
- **Scale:** 3 of 151 pool films.
- **Effect on the client's number:** Treated as "earned nothing", they'd drag their bundles down. Treated as real data, the return would be undefined. The *Lion King* bundle's 17× return rests on its one cinema film.
- **What I did about it:** Budget or revenue of 0 counts as "not applicable": left out of return, kept for ratings. Bundles are flagged `money_data_incomplete`.
- **Residual risk:** Streaming value of these sequels is unknown. The bundle ranking flags *Lion King* rather than trusting its return.

### F-07: Talent records are tangled up with franchises — Severity: Medium (talent read only)

- **What it is:** The most frequent names are franchise regulars. Daniel Radcliffe has 8 films, all *Harry Potter*.
- **How I detected it:** Counted each person's films and the number of *different* franchises or standalones among them.
- **Scale:** Of the leads with 5+ films, several have only one independent title (Radcliffe, Tom Cruise, Rupert Grint, Mark Hamill, Bruce Willis).
- **Effect on the client's number:** Without a fix, the talent list would mostly repeat the franchise list.
- **What I did about it:** A person counts as a signal only with 3+ scored films across 2+ independent titles (ADR-0009).
- **Residual risk:** Even then the evidence is thin (3–8 films per person). These are track records, not proof that the person drives success.

### F-08: "Top-billed" isn't always the lead actor — Severity: Low-Medium

- **What it is:** For *The Smurfs*, TMDb's first-billed cast member is Katy Perry (a voice role). Most people would name Neil Patrick Harris.
- **How I detected it:** The human spot-check sheet (`docs/spot-check-sheet.md`) shows the lead for 8 random films.
- **Scale:** Seen in 1 of 8 sampled films. The full extent is unknown.
- **Effect on the client's number:** It can credit or blame the wrong actor in the talent read.
- **What I did about it:** "Lead" means one of the top two billed (`lead_billing_positions` in config).
- **Residual risk:** Some animated and ensemble films still credit voice cast first.

### F-09: Budgets are estimates — Severity: Low

- **What it is:** 107 of 112 budgets are exact millions, and 9 revenues are exact hundred-thousands.
- **How I detected it:** Checks `budget_is_round_estimate` and `revenue_is_round_estimate`.
- **Effect on the client's number:** Return figures are approximate. Differences of a few tenths (e.g. 4.4× vs 4.5×) shouldn't be read as meaningful.
- **What I did about it:** Medians and rank-based scores, which aren't sensitive to small errors.
- **Residual risk:** Low.

### F-10: TMDb popularity is a "trending today" number — Severity: Low

- **What it is:** *Iron Man* scores 379.6 on popularity against a median of about 17. The score reflects recent site activity and changes daily.
- **How I detected it:** Check `popularity_spike` (over 4× the median).
- **Effect on the client's number:** None, because it's excluded from every KPI (ADR-0008). Had it been used, one film would dominate.
- **Residual risk:** None.

## Looked wrong, is not wrong

| Apparent problem | Why it looks wrong | Why it is actually fine |
|---|---|---|
| *The Shawshank Redemption* returned only 1.1× its budget | A top-rated film with almost no box office return | It's real: it famously underperformed in cinemas and found its audience later. That's why the score uses rating as well as return |
| 9 films have two or more directors (*The Matrix*, *Shrek*, *Avengers: Endgame*) | Looks like duplicate rows | They are genuine co-directors. The talent code counts each film once per person |
| An actor listed twice in *Terminator Salvation* | Looks like a duplicate | Linda Hamilton has two uncredited voice credits. Counted once |
| Very large ids (8471293, 9412887…) | Looked like junk at first | I didn't drop them on suspicion. TMDb was asked, and only its "not found" answer settled it |
| *Star Wars* 70× and *Jaws* 67× returns | Look like errors | Low 1970s budgets and decades of re-releases. Real, and one reason the 2000-onward window exists |
| *Toy Story 5* counted as released | Looks like a future film | Released before the run date (2026-11-20). "Released" is judged on the run date, which each run records |
| Data has no film after 2019 on the list | Looks like a stale list | It's how the list was assembled. The franchise lists do include newer films |

## Could not verify

- **Licence prices.** No price data was provided, so the deal note can only rank value *relative* to other options, not in dollars.
- **Streaming performance.** Box office and TMDb ratings are proxies. How these films perform on a streaming service is not in the data.
- **What studios actually include in each bundle.** We used TMDb's franchise lists, which may differ from the studio's.
- **The 5 unknown ids.** What they were meant to be can't be recovered from the list.
- **Accuracy of TMDb's money figures.** They're community-edited estimates, and older figures may include re-releases.
- **How the list was assembled.** We can't tell which of the three sources each id came from, so we can't say which source caused the repeats and bad ids.
- **Future values.** Ratings and vote counts change. The cache freezes this run's data, and a fresh fetch next quarter will give slightly different numbers.
