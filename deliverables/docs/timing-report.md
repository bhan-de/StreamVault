# Timing report (written by run.py)

Run date: 2026-11-20. Budget: computation under 10 s.

**What the measurement covers:** clean, join, aggregate and write, from cached responses, excluding acquisition. Rows marked 'no' (pre-flight, fetching) are shown but not counted, because they depend on the network, not on our code.

```
stage                      seconds  in budget?
-----------------------------------------------
preflight                   0.0068  no (network/setup)
load id list + ledger       0.0185  yes
acquire (TMDb or cache)     0.5754  no (network/setup)
ledger outcomes + write     0.0219  yes
shape JSON into tables      0.5033  yes
data checks                 0.0538  yes
analysis                    0.1307  yes
shortlist + talent          0.5054  yes
spot checks                 0.0111  yes
-----------------------------------------------
computation total           1.2447
```
