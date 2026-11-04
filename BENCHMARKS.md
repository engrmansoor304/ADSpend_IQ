# ADSpend IQ Benchmark Results

Each engine reads the same synthetic CSV and aggregates totals by platform.
Times are from one local run per dataset. Spark startup is measured separately.

| Records | Pandas (s) | Local MapReduce (s) | Spark (s) | Spark startup (s) |
|---:|---:|---:|---:|---:|
| 10,000 | 0.059 | 0.167 | 6.662 | 15.017 |
| 100,000 | 0.266 | 1.210 | 7.928 | 14.208 |
