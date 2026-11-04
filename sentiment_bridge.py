import argparse
import csv
from collections import Counter
from pathlib import Path


MIN_COMMENTS = 30  # Demo rule for when to suggest a creative test.


def load_counts(path):
    counts = Counter()
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not {"sentiment", "comments"}.issubset(reader.fieldnames or []):
            raise ValueError("Expected sentiment and comments columns.")

        for row in reader:
            label = row["sentiment"].strip().casefold()
            count = int(row["comments"])
            if not label or count < 0:
                raise ValueError("Each row needs a sentiment and a nonnegative count.")
            counts[label] += count

    return counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--topic", required=True)
    args = parser.parse_args()

    try:
        counts = load_counts(args.csv_path)
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f"Import failed: {error}\n")

    total = sum(counts.values())
    positive = counts["positive"]

    print(f"Topic: {args.topic}")
    print(f"Comments imported: {total:,}")
    for label, count in counts.most_common():
        share = 100 * count / total if total else 0
        print(f"  {label}: {count:,} ({share:.1f}%)")

    if total < MIN_COMMENTS:
        print("Insufficient feedback for an ad recommendation.")
    elif positive > total / 2:
        print(f"Creative test idea: Compare a {args.topic} spotlight with a general cricket ad.")
    else:
        print("No clear positive majority. Review the comments before choosing a creative.")


if __name__ == "__main__":
    main()
