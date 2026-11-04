from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path(__file__).resolve().parent / "data" / "generated"
BUDGET_PKR = 1_000_000
ROAS_WEIGHT = 0.60
MIN_CONVERSIONS = 100


def recommend_budget(summary, budget):
    results = summary[["platform", "spend", "conversions", "revenue"]].copy()
    results = results.sort_values("platform").reset_index(drop=True)

    results["ROAS"] = results["revenue"] / results["spend"].where(
        results["spend"] > 0
    )
    results["CPA_PKR"] = results["spend"] / results["conversions"].where(
        results["conversions"] > 0
    )

    # Require enough conversion history and valid performance metrics.
    eligible = (
        results["conversions"].ge(MIN_CONVERSIONS)
        & results["ROAS"].gt(0)
        & results["CPA_PKR"].gt(0)
        & np.isfinite(results["ROAS"])
        & np.isfinite(results["CPA_PKR"])
    )
    if not eligible.any():
        raise ValueError("No platform has enough valid performance data.")

    roas = results.loc[eligible, "ROAS"]
    efficiency = 1 / results.loc[eligible, "CPA_PKR"]
    shares = (
        ROAS_WEIGHT * roas / roas.sum()
        + (1 - ROAS_WEIGHT) * efficiency / efficiency.sum()
    )

    # Assign whole rupees, then distribute the remainder by fractional share.
    exact = shares * budget
    allocation = np.floor(exact).astype("int64")
    remaining = budget - int(allocation.sum())
    priority = (exact - allocation).sort_values(ascending=False, kind="stable")
    allocation.loc[priority.index[:remaining]] += 1

    results["eligible"] = eligible
    results["recommended_budget_PKR"] = 0
    results.loc[eligible, "recommended_budget_PKR"] = allocation
    results["budget_share_pct"] = 100 * results["recommended_budget_PKR"] / budget

    if results["recommended_budget_PKR"].sum() != budget:
        raise RuntimeError("Recommended allocations do not match the budget.")

    columns = [
        "platform", "conversions", "ROAS", "CPA_PKR", "eligible",
        "recommended_budget_PKR", "budget_share_pct",
    ]
    return results[columns].sort_values(
        "recommended_budget_PKR", ascending=False, kind="stable"
    ).round(2)


def main():
    source = DATA_DIR / "platform_summary.csv"
    if not source.is_file():
        raise SystemExit("Run analyze_ads.py first to generate platform_summary.csv.")

    recommendation = recommend_budget(pd.read_csv(source), BUDGET_PKR)
    output = DATA_DIR / "budget_recommendation.csv"
    recommendation.to_csv(output, index=False)

    print(recommendation.to_string(index=False))
    print(f"\nTotal allocated: PKR {recommendation['recommended_budget_PKR'].sum():,}")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
