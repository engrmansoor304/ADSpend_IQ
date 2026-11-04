from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import streamlit as st

from optimize_budget import BUDGET_PKR, DATA_DIR, recommend_budget
from sentiment_bridge import MIN_COMMENTS, load_counts


ROOT = Path(__file__).resolve().parent

st.set_page_config(page_title="ADSpend IQ", page_icon="📊", layout="wide")
st.title("ADSpend IQ")
st.caption("Digital advertising budget planner using simulated campaign data")

budget_tab, benchmark_tab, sentiment_tab = st.tabs(
    ["Budget Planner", "Benchmark Results", "CricketFanInsights Import"]
)

with budget_tab:
    budget = st.number_input(
        "Campaign budget (PKR)",
        min_value=1,
        value=BUDGET_PKR,
        step=50_000,
    )
    st.caption("Allocation uses 60% ROAS and 40% cost-per-conversion efficiency.")
    summary_path = DATA_DIR / "platform_summary.csv"

    if summary_path.is_file():
        try:
            allocation = recommend_budget(pd.read_csv(summary_path), int(budget))
        except (OSError, ValueError, KeyError) as error:
            st.error(f"Could not calculate the allocation: {error}")
        else:
            total = int(allocation["recommended_budget_PKR"].sum())
            st.metric("Total allocated", f"PKR {total:,}")
            st.bar_chart(allocation.set_index("platform")["recommended_budget_PKR"])
            st.dataframe(allocation, hide_index=True)
            st.download_button(
                "Download allocation CSV",
                allocation.to_csv(index=False),
                file_name="budget_recommendation.csv",
                mime="text/csv",
            )
    else:
        st.warning("Run analyze_ads.py to generate platform_summary.csv.")

with benchmark_tab:
    benchmark_path = ROOT / "BENCHMARKS.md"
    if benchmark_path.is_file():
        st.markdown(benchmark_path.read_text(encoding="utf-8-sig"))
    else:
        st.info("BENCHMARKS.md was not found.")

with sentiment_tab:
    st.caption("Use audience feedback to explore what kind of ad to test.")
    topic = st.text_input("Topic", value="Cricket").strip() or "Cricket"
    upload = st.file_uploader("Upload a CricketFanInsights sentiment summary", type="csv")

    if upload is not None:
        try:
            with TemporaryDirectory() as folder:
                path = Path(folder) / "sentiment_summary.csv"
                path.write_bytes(upload.getvalue())
                counts = load_counts(path)
        except (OSError, ValueError, TypeError, AttributeError) as error:
            st.error(f"Could not import the CSV: {error}")
        else:
            total = sum(counts.values())
            st.metric(f"Comments imported for {topic}", f"{total:,}")

            if total:
                breakdown = pd.DataFrame(
                    [
                        {
                            "Sentiment": label.title(),
                            "Comments": count,
                            "Share (%)": round(100 * count / total, 2),
                        }
                        for label, count in counts.most_common()
                    ]
                )
                st.bar_chart(breakdown.set_index("Sentiment")["Comments"])
                st.dataframe(breakdown, hide_index=True)

            if total < MIN_COMMENTS:
                st.warning("Insufficient feedback for an ad recommendation.")
            elif counts["positive"] > total / 2:
                st.success(
                    f"Creative test idea: Compare a {topic} spotlight with a general cricket ad."
                )
            else:
                st.info(
                    "No clear positive majority. Review the comments before choosing a creative."
                )
