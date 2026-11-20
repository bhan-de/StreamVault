# Decision notes

Every judgement call made where the brief left something open. Each one has a full record in `docs/adr/` 

| ADR | Decision | If wrong, what it costs Kwame | What the answer looks like under the rejected alternative |
|---|---|---|---|
| [001](adr/001-account-for-every-line.md) | Ledger with one outcome per line; translate IMDb ids | A merged "duplicate" could hide a candidate | Blank line lost silently; standalones counted 19 instead of 16, median return 3.2× instead of 3.8× |
| [002](adr/002-cache-raw-responses.md) | Cache every response; time only the computation | Slightly stale ratings | Same results, slower and less repeatable runs |
| [003](adr/003-judge-franchises-on-full-bundle.md) | Judge franchises on all released films | Franchises slightly undervalued if studios sell partial bundles | Franchises look better: 5.6× return and 10% weak entries, instead of 5.1× and 20% |
| [004](adr/004-lone-franchise-films.md) | Lone franchise films count as franchise | Franchise return lead overstated | Return gap almost vanishes (5.1× vs 5.0×); combined score still favours standalones (0.63 vs 0.47) |
| [005](adr/005-combined-score.md) | Combined score: return + rating, equal weight | Balance between audience size and quality is a judgement | Return only: franchises lead. Rating only: standalones lead by more |
| [006](adr/006-return-and-missing-money.md) | Return = revenue ÷ budget; zero budget = not applicable | One bundle (*Lion King*) rests on one film | With zeros counted, *Lion King* and *Ice Age* bundles sink unfairly |
| [007](adr/007-exclude-popularity.md) | No TMDb popularity in KPIs | Might miss a currently trending title | *Iron Man* would dominate; rankings change daily |


Smaller calls, recorded here only:

- **Weak entry = rated under 6.5** on TMDb's 10-point scale. This is a judgement: 10 of the 112 listed films fall below it, against 17 of the 39 franchise films missing from the list. Configurable (`weak_rating`).
- **"Released" is judged on the run date** and recorded with each run. Seven announced films (e.g. *Shrek 5*, *Avengers: Doomsday*) are excluded because they can't be licensed yet.
- **Medians, not means,** for group comparisons, because a few extreme returns (*Star Wars* 70×) would dominate an average.
- **Ids with leading zeros** (none this year) are flagged as invalid, not guessed.

## What survives when Adjoa reruns this next year with 500 titles

**Survives unchanged, no edits needed:**
- Swap in the new `data/input/id_list.csv` and run `python run.py`. Every step reruns automatically.
- The ledger accounts for every line, whatever mix of blanks, repeats and IMDb ids the new list has.
- New franchises and their missing entries are found automatically from each film's data.
- Both windows, both lone-film rules and both bundle views are computed on every run.
- The spot check rechecks 8 random films against the raw data, and a human sheet is regenerated.
- Pipeline KPIs (share of lines analysed, fetch errors, money coverage, time vs budget) print at the end of every run.
- Timing: about 1 s of computation at 500 titles, against a 10 s budget. The first fetch takes about 3 minutes, and reruns are offline.

**Needs a human eye each time:**
- The data findings narrative and the memo. The numbers update, but the words must be rechecked.
- The "not found" ids in the ledger. Someone should ask the source what they were meant to be.
- The human spot-check sheet (tick the 8 films).
- Settings in `config.toml` (weak line, cutoff year, talent thresholds) if the business view changes.

**Would break or need work:**
- A list in the tens of thousands: shaping grows linearly and would exceed the budget around 5,000 titles. The known fix is to keep only directors and top-billed cast while shaping.
- TMDb changing its response format: the automatic spot check and tests would catch it and stop the run.
- A new laptop without Python 3.12+: the run stops with a plain message saying what to install.
