# ADSpend IQ

A Big Data Analytics project that recommends how to allocate a simulated
PKR 1,000,000 advertising budget across Facebook, Instagram, Google Ads,
TikTok, and YouTube.

## Planned work

- Generate synthetic advertising data and calculate campaign metrics.
- Compare Pandas, local MapReduce, and Spark at different dataset sizes.
- Display benchmark results and budget recommendations in Streamlit.

## Connection to Project 1

ADSpend IQ will import a sentiment summary CSV from CricketFanInsights
to suggest ad creative ideas. The budget recommendation will use
simulated advertising performance.

Project 1: https://github.com/engrmansoor304/CricketFanInsights

## Dashboard screenshots

### Budget Planner
![Budget allocation across five advertising platforms](docs/screenshots/budget-planner.png)

### Big Data Benchmarks
![Pandas, local MapReduce, and Spark benchmark results](docs/screenshots/benchmarks.png)

### Audience Insights
![CricketFanInsights sentiment summary imported into ADSpend IQ](docs/screenshots/audience-insights.png)

## Windows Quick Start

Make sure Python and Git are installed. Open PowerShell and run:

```powershell
git clone https://github.com/engrmansoor304/ADSpend_IQ.git
cd .\ADSpend_IQ
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\.venv\Scripts\python.exe .\analyze_ads.py
.\.venv\Scripts\python.exe -m streamlit run .\dashboard.py --server.port 8503
```

Open [ADSpend IQ](http://localhost:8503) in your browser. The demo generates
10,000 synthetic ad records and uses the platform summary to recommend
how to split a PKR 1,000,000 budget across five advertising platforms.

See [BENCHMARKS.md](BENCHMARKS.md) for the saved results up to 10 million
rows. To try Audience Insights, upload a sentiment summary CSV exported
from CricketFanInsights.
