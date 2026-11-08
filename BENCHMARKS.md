# ADSpend IQ Benchmark Results

Each engine reads the same synthetic CSV and aggregates totals by platform.
Times are from one local run per dataset. Spark startup is measured separately.

| Records | Pandas (s) | Local MapReduce (s) | Spark (s) | Spark startup (s) |
|---:|---:|---:|---:|---:|
| 10,000 | 0.059 | 0.167 | 6.662 | 15.017 |
| 100,000 | 0.266 | 1.210 | 7.928 | 14.208 |
| 1,000,000 | 1.233 | 16.342 | 15.628 | 15.997 |
| 10,000,000 | 10.673 | 69.845 | 24.533 | 9.924 |

## Interpretation

All three engines produced matching platform totals at each tested dataset
size. At 10 million rows, Pandas took 10.673 seconds, Spark took 24.533
seconds, and local MapReduce took 69.845 seconds. Spark startup took an
additional 9.924 seconds and is reported separately.

Pandas was fastest on this machine for the tested workload. Each timing is
from one local run per dataset size. The MapReduce implementation is a
local simulation, so these timings describe this setup and workload.
