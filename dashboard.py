from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import streamlit as st

from optimize_budget import BUDGET_PKR, DATA_DIR, recommend_budget
from sentiment_bridge import MIN_COMMENTS, load_counts


ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="ADSpend IQ", page_icon="📊", layout="wide")

st.title("ADSpend IQ")
st.markdown("**Digital Advertising Budget Optimizer**")
st.caption("Compare platform performance, plan your budget, and explore cricket audience feedback.")

with st.sidebar:
    st.header("Campaign settings")
    budget = st.number_input(
        "Campaign budget (PKR)",
        min_value=1,
        max_value=1_000_000_000,
        value=BUDGET_PKR,
        step=50_000,
    )
    st.divider()
    st.markdown("**Allocation model**")
    st.caption("60% return on ad spend · 40% cost-per-conversion efficiency")
    st.info("Advertising performance in this dashboard is simulated.")

planner, benchmarks, audience = st.tabs(
    ["Budget Planner", "Big Data Benchmarks", "Audience Insights"]
)

with planner:
    st.subheader("Recommended platform allocation")
    summary_path = DATA_DIR / "platform_summary.csv"

    try:
        allocation = recommend_budget(pd.read_csv(summary_path), int(budget))
    except FileNotFoundError:
        st.warning("Run `analyze_ads.py` to generate the platform summary.")
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        st.error(f"Could not calculate the allocation: {error}")
    else:
        top = allocation.iloc[0]
        total = int(allocation["recommended_budget_PKR"].sum())
        left, middle, right = st.columns(3)

        left.metric("Total allocated", f"PKR {total:,}")
        middle.metric("Top platform", str(top["platform"]))
        right.metric("Top platform allocation", f"PKR {int(top['recommended_budget_PKR']):,}")

        st.bar_chart(
            allocation.set_index("platform")["recommended_budget_PKR"],
            y_label="Recommended budget (PKR)",
            color="#2563EB",
        )

        st.dataframe(
            allocation,
            hide_index=True,
            column_config={
                "platform": "Platform",
                "conversions": st.column_config.NumberColumn("Conversions", format="%d"),
                "ROAS": st.column_config.NumberColumn("ROAS", format="%.2fx"),
                "CPA_PKR": st.column_config.NumberColumn("CPA (PKR)", format="%.2f"),
                "eligible": "Eligible",
                "recommended_budget_PKR": st.column_config.NumberColumn(
                    "Recommended budget (PKR)", format="%d"
                ),
                "budget_share_pct": st.column_config.NumberColumn(
                    "Budget share", format="%.2f%%"
                ),
            },
        )
        st.download_button(
            "Download budget plan",
            allocation.to_csv(index=False),
            file_name="budget_recommendation.csv",
            mime="text/csv",
        )

with benchmarks:
    st.subheader("Processing time by dataset size")
    st.caption(
        "Each engine read the same synthetic CSV and calculated platform totals. "
        "These are single local runs. Spark startup is shown separately in the table."
    )
    benchmark_path = ROOT / "BENCHMARKS.md"

    if not benchmark_path.is_file():
        st.info("Add BENCHMARKS.md to display the measured results.")
    else:
        rows = []
        for line in benchmark_path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip().startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) != 5 or not cells[0].replace(",", "").isdigit():
                continue
            records = int(cells[0].replace(",", ""))
            pandas_time, mapreduce_time, spark_time, startup = map(float, cells[1:])
            rows.append(
                {
                    "Records": records,
                    "Pandas": pandas_time,
                    "Local MapReduce": mapreduce_time,
                    "Spark": spark_time,
                    "Spark startup": startup,
                }
            )

        if rows:
            results = pd.DataFrame(rows).sort_values("Records")
            st.metric("Largest verified dataset", f"{results['Records'].max():,} rows")
            st.line_chart(
                results,
                x="Records",
                y=["Pandas", "Local MapReduce", "Spark"],
                y_label="Processing time (seconds)",
            )
            st.dataframe(results, hide_index=True)
        else:
            st.info("No benchmark rows were found in BENCHMARKS.md.")

with audience:
    st.subheader("CricketFanInsights")
    st.caption("Import a sentiment summary to explore which ad idea to test.")
    topic = st.text_input("Audience topic", value="Cricket").strip() or "Cricket"
    upload = st.file_uploader("Upload a sentiment summary CSV", type=["csv"])

    if upload is None:
        st.info("Export a Sentiment Summary CSV from CricketFanInsights to begin.")
    else:
        try:
            with TemporaryDirectory() as folder:
                path = Path(folder) / "sentiment_summary.csv"
                path.write_bytes(upload.getvalue())
                counts = load_counts(path)
        except (OSError, ValueError, TypeError, AttributeError) as error:
            st.error(f"Could not import the summary: {error}")
        else:
            total = sum(counts.values())
            positive_share = 100 * counts["positive"] / total if total else 0
            left, right = st.columns(2)
            left.metric(f"Comments imported · {topic}", f"{total:,}")
            right.metric("Labeled positive", f"{positive_share:.1f}%")

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
                st.bar_chart(
                    breakdown.set_index("Sentiment")["Comments"],
                    color="#0F766E",
                )
                st.dataframe(breakdown, hide_index=True)

            if total < MIN_COMMENTS:
                st.warning(
                    f"Insufficient feedback for an ad recommendation. "
                    f"The demo requires at least {MIN_COMMENTS} comments."
                )
            elif counts["positive"] > total / 2:
                st.success(
                    f"Creative test idea: Compare a {topic} spotlight "
                    "with a general cricket ad."
                )
            else:
                st.info(
                    "No clear positive majority. "
                    "Review the comments before choosing a creative."
                )