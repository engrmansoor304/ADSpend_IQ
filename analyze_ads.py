from pathlib import Path

import numpy as np
import pandas as pd


ROW_COUNT = 10_000
SEED = 42
OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "generated"

# Platform assumptions for the simulation: CTR, conversion rate, CPC in PKR.
PLATFORM_SETTINGS = {
    "Facebook": (0.025, 0.036, 28),
    "Instagram": (0.030, 0.033, 30),
    "Google Ads": (0.035, 0.050, 42),
    "TikTok": (0.029, 0.025, 22),
    "YouTube": (0.018, 0.028, 25),
}


def generate_data(row_count, seed=SEED):
    rng = np.random.default_rng(seed)
    platforms = rng.choice(list(PLATFORM_SETTINGS), size=row_count)
    rates = np.array([PLATFORM_SETTINGS[name] for name in platforms])
    impressions = rng.integers(500, 15_001, size=row_count)
    clicks = rng.binomial(impressions, rates[:, 0])
    conversions = rng.binomial(clicks, rates[:, 1])
    spend = (clicks * rates[:, 2] * rng.uniform(0.8, 1.2, row_count)).round(2)
    revenue = (conversions * rng.integers(700, 2_501, row_count)).round(2)
    dates = pd.Timestamp("2026-08-01") + pd.to_timedelta(
        rng.integers(0, 90, row_count), unit="D"
    )

    return pd.DataFrame({
        "date": dates,
        "campaign": rng.choice(
            ["Match Highlights", "Player Spotlight", "Cricket Gear"],
            row_count,
        ),
        "platform": platforms,
        "impressions": impressions,
        "clicks": clicks,
        "spend": spend,
        "conversions": conversions,
        "revenue": revenue,
        "age": rng.integers(18, 66, row_count),
        "gender": rng.choice(["Female", "Male", "Unspecified"], row_count),
        "city": rng.choice(["Lahore", "Karachi", "Islamabad"], row_count),
        "device": rng.choice(["Mobile", "Desktop", "Tablet"], row_count),
    })


def safe_ratio(numerator, denominator):
    return numerator.div(denominator.where(denominator.ne(0)))


def summarize(data, group_columns):
    totals = data.groupby(group_columns, as_index=False)[
        ["impressions", "clicks", "spend", "conversions", "revenue"]
    ].sum()

    totals["CTR_pct"] = 100 * safe_ratio(totals["clicks"], totals["impressions"])
    totals["CPC_PKR"] = safe_ratio(totals["spend"], totals["clicks"])
    totals["CPA_PKR"] = safe_ratio(totals["spend"], totals["conversions"])
    totals["CVR_pct"] = 100 * safe_ratio(totals["conversions"], totals["clicks"])
    totals["ROAS"] = safe_ratio(totals["revenue"], totals["spend"])

    return totals.sort_values("ROAS", ascending=False).round(2)


def main():
    ads = generate_data(ROW_COUNT)
    assert len(ads) == ROW_COUNT
    assert ads["clicks"].le(ads["impressions"]).all()
    assert ads["conversions"].le(ads["clicks"]).all()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ads.to_csv(OUTPUT_DIR / "ads_10000.csv", index=False)

    for label, columns in [
        ("platform", ["platform"]),
        ("campaign", ["platform", "campaign"]),
    ]:
        summary = summarize(ads, columns)
        summary.to_csv(OUTPUT_DIR / f"{label}_summary.csv", index=False)
        print(f"\n{label.title()} performance")
        print(summary.to_string(index=False))

    print(f"\nGenerated {len(ads):,} synthetic records in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
