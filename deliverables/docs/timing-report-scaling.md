# Scaling test

Computation only, from data already in memory (no network, no disk reads). Copies of the real films with new ids.

| step | 112 films | 500 films | 5,000 films | 50,000 films |
|---|---|---|---|---|
| shape JSON into tables | 0.232 s | 1.019 s | 10.140 s | 109.239 s |
| build bundle tables | 0.008 s | 0.011 s | 0.058 s | 3.104 s |
| data checks | 0.034 s | 0.023 s | 0.057 s | 0.775 s |
| analysis | 0.035 s | 0.025 s | 0.030 s | 0.084 s |
| shortlist + talent | 0.036 s | 0.040 s | 0.131 s | 1.248 s |
| rows: films / crew | 112 / 24,932 | 500 / 111,781 | 5,000 / 1,111,999 | 50,000 / 11,130,536 |
