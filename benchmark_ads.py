import argparse
import json
import platform
from pathlib import Path
from time import perf_counter

import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "data" / "generated" / "ads_10000.csv"
GROUP = "platform"
METRICS = ["impressions", "clicks", "spend", "conversions", "revenue"]
RESULT_COLUMNS = [GROUP, "records", *METRICS]
READ_OPTIONS = {"usecols": [GROUP, *METRICS], "encoding": "utf-8-sig"}


def aggregate_batch(data):
    return data.groupby(GROUP).agg(
        records=(GROUP, "size"),
        **{column: (column, "sum") for column in METRICS},
    )


def pandas_totals(path):
    data = pd.read_csv(path, **READ_OPTIONS)
    return aggregate_batch(data).reset_index()


def mapreduce_totals(path, chunk_size):
    # Map: aggregate one CSV chunk at a time.
    # Reduce: merge its platform totals into the running totals.
    totals = None
    for chunk in pd.read_csv(path, chunksize=chunk_size, **READ_OPTIONS):
        partial = aggregate_batch(chunk)
        if totals is None:
            totals = partial
        else:
            totals = pd.concat([totals, partial]).groupby(level=0).sum()

    if totals is None or totals.empty:
        raise ValueError("The CSV has no advertising records.")

    return totals.reset_index()


def spark_totals(spark, path):
    from pyspark.sql import functions as F

    # The schema follows the exact column order written by analyze_ads.py.
    schema = """
        date STRING, campaign STRING, platform STRING,
        impressions BIGINT, clicks BIGINT, spend DECIMAL(20,2),
        conversions BIGINT, revenue DECIMAL(20,2),
        age INT, gender STRING, city STRING, device STRING
    """
    data = (
        spark.read
        .option("header", True)
        .option("mode", "FAILFAST")
        .option("enforceSchema", False)
        .schema(schema)
        .csv(path.as_uri())
    )
    grouped = data.groupBy(GROUP).agg(
        F.count("*").alias("records"),
        *[F.sum(column).alias(column) for column in METRICS],
    )

    # collect() executes the query and brings back only the platform totals.
    return pd.DataFrame(
        [row.asDict() for row in grouped.collect()],
        columns=RESULT_COLUMNS,
    )


def normalize_totals(totals):
    result = totals[RESULT_COLUMNS].sort_values(GROUP).reset_index(drop=True)
    for column in ["records", "impressions", "clicks", "conversions"]:
        result[column] = result[column].astype("int64")
    for column in ["spend", "revenue"]:
        result[column] = result[column].astype("float64").round(2)
    return result


def timed_run(engine, operation, results, expected=None):
    start = perf_counter()
    raw_totals = operation()
    seconds = perf_counter() - start
    totals = normalize_totals(raw_totals)

    if totals.empty:
        raise ValueError("The CSV has no advertising records.")

    if expected is not None:
        pd.testing.assert_frame_equal(
            expected, totals, check_exact=True, obj=f"{engine} platform totals"
        )

    results.append({"engine": engine, "seconds": round(seconds, 6)})
    print(f"{engine}: {seconds:.3f}s")
    return totals


def main():
    parser = argparse.ArgumentParser(description="Compare ad CSV aggregations.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--chunk-size", type=int, default=2_000)
    parser.add_argument("--skip-spark", action="store_true")
    args = parser.parse_args()
    path = args.input.resolve()

    if args.chunk_size < 1:
        parser.error("--chunk-size must be greater than zero.")
    if not path.is_file():
        parser.error(f"CSV not found: {path}")

    timings = []
    baseline = timed_run("Pandas", lambda: pandas_totals(path), timings)
    timed_run(
        "Local MapReduce",
        lambda: mapreduce_totals(path, args.chunk_size),
        timings,
        baseline,
    )

    spark_startup_seconds = None
    spark_version = None
    if not args.skip_spark:
        from pyspark.sql import SparkSession

        start = perf_counter()
        spark = (
            SparkSession.builder
            .appName("ADSpend IQ Benchmark")
            .master("local[2]")
            .config("spark.ui.enabled", "false")
            .config("spark.sql.shuffle.partitions", "4")
            .getOrCreate()
        )
        spark_startup_seconds = round(perf_counter() - start, 6)

        try:
            spark.sparkContext.setLogLevel("ERROR")
            spark_version = spark.version
            timed_run("Spark", lambda: spark_totals(spark, path), timings, baseline)
        finally:
            spark.stop()

    report = {
        "dataset": path.name,
        "records": int(baseline["records"].sum()),
        "platforms": len(baseline),
        "operating_system": platform.platform(),
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "mapreduce_chunk_size": args.chunk_size,
        "spark_version": spark_version,
        "spark_mode": "local[2]" if spark_version else None,
        "spark_startup_seconds": spark_startup_seconds,
        "timings": timings,
    }
    mode = "local_only" if args.skip_spark else "all_engines"
    output = path.parent / f"benchmark_{path.stem}_{mode}.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"\nPASS: All {len(timings)} enabled engines agree.")
    print(f"Verified {report['records']:,} records across {report['platforms']} platforms.")
    print(f"Report saved to {output}")


if __name__ == "__main__":
    main()
