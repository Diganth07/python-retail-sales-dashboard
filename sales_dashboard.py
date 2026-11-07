"""Create a retail sales dashboard image from a CSV file."""

import argparse
import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

REQUIRED_COLUMNS = {"date", "product", "category", "quantity", "unit_price", "region"}


def load_sales(path: Path) -> list[dict]:
    rows = []
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
            raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")
        for line, row in enumerate(reader, start=2):
            try:
                row["parsed_date"] = date.fromisoformat(row["date"])
                row["quantity"] = int(row["quantity"])
                row["unit_price"] = float(row["unit_price"])
                if row["quantity"] < 0 or row["unit_price"] < 0:
                    raise ValueError("quantity and unit_price must not be negative")
                row["revenue"] = row["quantity"] * row["unit_price"]
                rows.append(row)
            except (TypeError, ValueError) as error:
                raise ValueError(f"Invalid data on CSV line {line}: {error}") from error
    if not rows:
        raise ValueError("CSV has no sales rows")
    return rows


def create_dashboard(rows: list[dict], output: Path) -> None:
    monthly = defaultdict(float)
    categories = defaultdict(float)
    regions = defaultdict(float)
    for row in rows:
        monthly[row["parsed_date"].strftime("%Y-%m")] += row["revenue"]
        categories[row["category"]] += row["revenue"]
        regions[row["region"]] += row["revenue"]

    revenue = sum(row["revenue"] for row in rows)
    quantity = sum(row["quantity"] for row in rows)
    average = revenue / len(rows)
    color = "#5368e8"
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.patch.set_facecolor("#f5f7fb")
    fig.suptitle("RETAIL SALES DASHBOARD", fontsize=18, fontweight="bold", color="#17233c", y=.98)

    fig.text(.17, .88, f"TOTAL REVENUE\n${revenue:,.2f}", ha="center", va="center",
             fontsize=13, fontweight="bold", color="#263991")
    fig.text(.50, .88, f"UNITS SOLD\n{quantity:,}", ha="center", va="center",
             fontsize=13, fontweight="bold", color="#263991")
    fig.text(.83, .88, f"AVERAGE ORDER\n${average:,.2f}", ha="center", va="center",
             fontsize=13, fontweight="bold", color="#263991")

    ax = axes[0, 0]
    months = sorted(monthly)
    ax.plot(months, [monthly[key] for key in months], marker="o", color=color, linewidth=2)
    ax.set_title("Revenue by Month")
    ax.tick_params(axis="x", rotation=35)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"${value:,.0f}"))

    ax = axes[0, 1]
    category_items = sorted(categories.items(), key=lambda item: item[1])
    ax.barh([item[0] for item in category_items], [item[1] for item in category_items], color=color)
    ax.set_title("Revenue by Category")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"${value:,.0f}"))

    ax = axes[1, 0]
    region_items = sorted(regions.items(), key=lambda item: item[1], reverse=True)
    ax.pie([item[1] for item in region_items], labels=[item[0] for item in region_items],
           autopct="%1.0f%%", colors=plt.cm.Blues([.45 + .5 * i / max(1, len(region_items) - 1)
                                                  for i in range(len(region_items))]),
           startangle=90)
    ax.set_title("Revenue Share by Region")

    ax = axes[1, 1]
    ax.bar([item[0] for item in category_items],
           [sum(row["quantity"] for row in rows if row["category"] == item[0]) for item in category_items],
           color="#7c8af0")
    ax.set_title("Units Sold by Category")
    ax.tick_params(axis="x", rotation=25)

    for ax in (axes[0, 0], axes[0, 1], axes[1, 1]):
        ax.set_facecolor("white")
        ax.grid(axis="y", alpha=.2)
        ax.set_axisbelow(True)
    fig.tight_layout(rect=(0, 0, 1, .82))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a retail sales dashboard from a CSV.")
    parser.add_argument("csv_file", nargs="?", type=Path, default=Path("sales_data.csv"))
    parser.add_argument("-o", "--output", type=Path, default=Path("sales_dashboard.png"))
    args = parser.parse_args()
    try:
        rows = load_sales(args.csv_file)
        create_dashboard(rows, args.output)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"Dashboard saved to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
