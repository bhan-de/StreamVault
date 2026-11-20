# Timing report (written by run.py)

Run date: 2026-11-20. Budget: computation under 10 s.

**What the measurement covers:** clean, join, aggregate and write, from cached responses, excluding acquisition. Rows marked 'no' (pre-flight, fetching) are shown but not counted, because they depend on the network, not on our code.

```
stage                      seconds  in budget?
-----------------------------------------------
preflight                   0.0454  no (network/setup)
load id list + ledger       0.0345  yes
acquire (TMDb or cache)     4.6688  no (network/setup)
ledger outcomes + write     0.0787  yes
shape JSON into tables      2.7442  yes
data checks                 0.1219  yes
analysis                    0.3432  yes
shortlist + talent          1.4762  yes
spot checks                 0.0365  yes
-----------------------------------------------
computation total           4.8352
```
