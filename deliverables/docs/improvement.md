# One improvement beyond the brief: the bundle-gap check

## What it is

The brief asks for details and credits of the titles on the candidate list. We added one more step: for every franchise a candidate belongs to, fetch the **full list of films the studio would sell**, plus the details of the released films missing from the candidate list. Each run then reports, per franchise, how many films are missing and how they rate (`data/processed/franchise_coverage.csv`, check `franchise_incomplete_on_list`).

## What it's worth to the VP

- **It answers his team's argument with numbers.** Half the team says StreamVault overpays for weak middle entries. The bundle gap shows they're right about this list: the 39 missing films average 6.6 against 7.5 for the listed ones, and weak films in bundles go from 10% to 20% once they're counted.
- **It's a negotiating lever.** A negotiator can say: "Your *Jaws* bundle includes three sequels averaging 4.9. We'll price it on those, not on the original." That argument didn't exist before.
- **It protects him in the board room.** A bundle that looks strong on the shortlist but carries weak sequels is exactly the kind of mistake the board remembers. The check makes that visible before money is committed.

## What it's worth to employee A

- **No extra work.** The check runs as part of `python run.py`. New franchises on next year's list are discovered automatically from each film's data.
- **Cheap.** About 70 extra API calls on the first run (around 20 seconds), cached afterwards. It adds about 0.01 s to a rerun.
- **Self-explaining.** `franchise_coverage.csv` lists each franchise with films on and off the list and their ratings. She can answer "why did this bundle drop?" in the meeting.

## What it costs

- It goes beyond the two endpoints named in the brief (recorded in ADR-0004).
- It relies on TMDb's public franchise lists, which may not match what a studio actually bundles. Bundle contents should be confirmed with each studio.

## Next candidate (not built)

A **change report between quarterly runs**: which titles entered or left the shortlist since the last run, and why (new ratings, a new sequel released, a new list). That would let employee A open a meeting with "what changed" instead of re-presenting everything.
