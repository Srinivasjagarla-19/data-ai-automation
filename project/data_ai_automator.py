import argparse
import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional, Tuple

import pandas as pd
from dotenv import load_dotenv
from fpdf import FPDF
import matplotlib.pyplot as plt

try:
    from google import genai
except ImportError:  
    genai = None


# ---------------------- Configuration & Logging ----------------------

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DEFAULT_INPUT_PATH = "sample.csv"
CLEANED_OUTPUT_PATH = "cleaned_output.csv"
CHART_PATH = "top_products.png"
PDF_REPORT_PATH = "report.pdf"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging to stdout.

    Uses INFO as default and logs major pipeline milestones as required.
    """

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
    )


# ---------------------- Data Structures ----------------------

@dataclass
class ProcessingSummary:
    rows_before: int
    rows_after_cleaning: int
    rows_after_transform: int
    removed_duplicates: int
    filled_missing_numeric: int
    filled_missing_text: int
    removed_invalid_rows: int


# ---------------------- Utility Functions ----------------------


def detect_file_type(path: str) -> str:
    """Detect file type from extension.

    Supported: csv, xls/xlsx, json.
    """

    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return "csv"
    if ext in {".xls", ".xlsx"}:
        return "excel"
    if ext == ".json":
        return "json"
    raise ValueError(f"Unsupported file type: {ext}")


def load_dataset(path: str) -> pd.DataFrame:
    """Load dataset using pandas based on detected file type."""

    logging.info("File loaded: %s", path)
    ftype = detect_file_type(path)

    if ftype == "csv":
        df = pd.read_csv(path)
    elif ftype == "excel":
        df = pd.read_excel(path)
    elif ftype == "json":
        df = pd.read_json(path)
    else:
        raise ValueError(f"Unsupported file type: {ftype}")

    return df


def to_snake_case(name: str) -> str:
    """Convert a column name to snake_case in a simple, robust way."""

    import re

    name = name.strip()
    name = re.sub(r"[\s\-]+", "_", name)
    name = re.sub(r"[^0-9a-zA-Z_]+", "", name)
    name = re.sub(r"_+", "_", name)
    return name.lower()


# ---------------------- Cleaning ----------------------


def clean_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, ProcessingSummary]:
    """Apply required cleaning operations to the DataFrame.

    Steps:
    - Remove duplicates
    - Handle missing values (numeric -> median, text -> mode or "unknown")
    - Standardize formats (dates, numeric types, lowercase text)
    - Remove invalid entries (negative numeric values in obvious measure columns)
    - Rename columns to snake_case
    """

    logging.info("Cleaning started")

    rows_before = len(df)
    removed_duplicates = rows_before - len(df.drop_duplicates())
    df = df.drop_duplicates().copy()

    filled_missing_numeric = 0
    filled_missing_text = 0

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if df[col].isna().any():
                median_val = df[col].median()
                filled_missing_numeric += int(df[col].isna().sum())
                df[col] = df[col].fillna(median_val)
        else:
            if df[col].isna().any():
                mode_series = df[col].mode(dropna=True)
                fill_val = mode_series.iloc[0] if not mode_series.empty else "unknown"
                filled_missing_text += int(df[col].isna().sum())
                df[col] = df[col].fillna(fill_val)

    for col in df.columns:
        if any(keyword in col.lower() for keyword in ["date", "time", "timestamp"]):
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            except Exception:
                pass

        if pd.api.types.is_object_dtype(df[col]):
            df[col] = df[col].astype(str).str.lower()

        if not pd.api.types.is_numeric_dtype(df[col]):
            try:
                coerced = pd.to_numeric(df[col], errors="coerce")
                if coerced.notna().mean() > 0.7:
                    df[col] = coerced
            except Exception:
                pass

    removed_invalid_rows = 0
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if numeric_cols:
        mask_invalid = (df[numeric_cols] < 0).any(axis=1)
        removed_invalid_rows = int(mask_invalid.sum())
        df = df.loc[~mask_invalid].copy()

    df = df.rename(columns={c: to_snake_case(c) for c in df.columns})

    rows_after_cleaning = len(df)

    summary = ProcessingSummary(
        rows_before=rows_before,
        rows_after_cleaning=rows_after_cleaning,
        rows_after_transform=rows_after_cleaning,
        removed_duplicates=int(removed_duplicates),
        filled_missing_numeric=filled_missing_numeric,
        filled_missing_text=filled_missing_text,
        removed_invalid_rows=removed_invalid_rows,
    )

    logging.info("Cleaning complete")
    return df, summary


# ---------------------- Transformations ----------------------


def apply_transformations(df: pd.DataFrame, summary: ProcessingSummary) -> Tuple[pd.DataFrame, pd.DataFrame, ProcessingSummary]:
    """Apply required transformations.

    Transformations:
    - Create new calculated column (e.g., total = price * quantity)
    - Grouping & aggregation (e.g., total sales per product)
    - Filtering (remove unwanted rows)
    - Sorting
    - Type conversions as needed
    """

    logging.info("Transformations started")

    cols = set(df.columns)
    price_col = next((c for c in cols if c in {"price", "unit_price"}), None)
    qty_col = next((c for c in cols if c in {"quantity", "qty"}), None)

    if price_col and qty_col:
        df["total"] = pd.to_numeric(df[price_col], errors="coerce").fillna(0) * pd.to_numeric(
            df[qty_col], errors="coerce"
        ).fillna(0)
    else:
        df["total"] = 1

    group_col = None
    for candidate in ["product", "item", "category"]:
        if candidate in df.columns:
            group_col = candidate
            break

    if group_col is None:
        group_col = df.columns[0]

    grouped = (
        df.groupby(group_col)
        .agg(
            total_sales=("total", "sum"),
            avg_total=("total", "mean"),
            count_rows=("total", "count"),
        )
        .reset_index()
    )

    df = df[df["total"] > 0].copy()

    df = df.sort_values("total", ascending=False)

    for col in ["total_sales", "avg_total"]:
        if col in grouped.columns:
            grouped[col] = pd.to_numeric(grouped[col], errors="coerce")

    summary.rows_after_transform = len(df)

    logging.info("Transformations complete")
    return df, grouped, summary


# ---------------------- Visualization ----------------------


def generate_bar_chart(grouped: pd.DataFrame, chart_path: str = CHART_PATH, top_n: int = 10) -> Optional[str]:
    """Generate a bar chart of top products/categories by total sales."""

    if grouped.empty:
        logging.warning("Grouped data is empty; skipping chart generation")
        return None

    name_col = grouped.columns[0]

    top = grouped.sort_values("total_sales", ascending=False).head(top_n)

    plt.figure(figsize=(10, 6))
    plt.bar(top[name_col].astype(str), top["total_sales"])
    plt.xticks(rotation=45, ha="right")
    plt.xlabel(name_col.replace("_", " ").title())
    plt.ylabel("Total Sales")
    plt.title("Top Items by Total Sales")
    plt.tight_layout()

    plt.savefig(chart_path)
    plt.close()

    logging.info("Visualization saved to %s", chart_path)
    return chart_path


# ---------------------- AI Integration (Gemini) ----------------------


def create_gemini_client() -> Optional["genai.Client"]:
    """Create a Gemini client using API key from environment.

    Checks both GEMINI_API_KEY and GOOGLE_API_KEY for compatibility
    with AI Studio examples.
    """

    if genai is None:
        logging.error("Gemini SDK is not installed. Install 'google-genai' to enable AI features.")
        return None

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment. Check your .env file.")
        return None

    try:
        client = genai.Client(api_key=api_key)
        return client
    except Exception as exc:  # Broad, as SDK may change
        logging.error("Failed to create Gemini client: %s", exc)
        return None


def build_ai_prompt(df: pd.DataFrame, grouped: pd.DataFrame) -> str:
    """Construct a rich prompt including dataset summary and grouped stats."""

    head_text = df.head(5).to_markdown(index=False)
    describe_text = df.describe(include="all").to_markdown()
    grouped_text = grouped.head(20).to_markdown(index=False)

    prompt = f"""
You are a data analyst. I will provide a dataset and some aggregated statistics.
Generate a concise professional report that includes:
- A high-level dataset summary
- Key patterns or insights
- Any anomalies or data quality issues you notice
- Business recommendations based on the grouped/aggregated data

Dataset head (first rows):
{head_text}

Dataset describe() summary:
{describe_text}

Grouped / aggregated data (top groups):
{grouped_text}
"""

    return prompt


def generate_ai_analysis(df: pd.DataFrame, grouped: pd.DataFrame) -> str:
    """Call Gemini to generate an analysis report.

    Returns plain-text analysis. On error, returns a descriptive message.
    """

    logging.info("AI processing started")

    client = create_gemini_client()
    if client is None:
        return "AI analysis unavailable: Gemini client not initialized. Check installation and API key (GEMINI_API_KEY/GOOGLE_API_KEY)."

    prompt = build_ai_prompt(df, grouped)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = getattr(response, "text", None)
        if callable(text):
            content = text()
        else:
            content = str(response)
        return content.strip()
    except Exception as exc:  # pragma: no cover - unpredictable errors
        message = str(exc).lower()
        if "api key" in message or "permission" in message:
            logging.error("Gemini authentication error: %s", exc)
            return "AI authentication error: invalid or missing API key."
        if "rate" in message or "quota" in message or "resource exhausted" in message:
            logging.error("Gemini rate limit: %s", exc)
            return "AI rate limit or quota reached. Please retry later."
        if "network" in message or "connection" in message or "timed out" in message:
            logging.error("Gemini connection error: %s", exc)
            return "AI connection error: check your internet connection."
        logging.error("Unexpected error from Gemini: %s", exc)
        return f"AI analysis failed: {exc}"


# ---------------------- PDF Report Export ----------------------


def export_pdf_report(
    summary: ProcessingSummary,
    grouped: pd.DataFrame,
    ai_report: str,
    chart_path: Optional[str] = None,
    output_path: str = PDF_REPORT_PATH,
) -> str:
    """Export a simple PDF report using FPDF.

    Includes cleaning summary, transformation summary, AI analysis, and optional chart.
    """

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Data Processing & AI Report", ln=True)

    pdf.set_font("Arial", size=12)
    pdf.ln(4)
    pdf.cell(0, 8, "Cleaning Summary", ln=True)

    pdf.set_font("Arial", size=10)
    lines = [
        f"Rows before: {summary.rows_before}",
        f"Rows after cleaning: {summary.rows_after_cleaning}",
        f"Rows after transformations: {summary.rows_after_transform}",
        f"Removed duplicates: {summary.removed_duplicates}",
        f"Filled missing numeric: {summary.filled_missing_numeric}",
        f"Filled missing text: {summary.filled_missing_text}",
        f"Removed invalid rows: {summary.removed_invalid_rows}",
    ]
    for line in lines:
        pdf.cell(0, 6, line, ln=True)

    pdf.ln(4)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, "Transformations Summary", ln=True)

    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, "Created 'total' column, grouped and aggregated data, filtered invalid/zero totals, and sorted by total.")

    pdf.ln(4)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, "Top Grouped Data (Preview)", ln=True)

    pdf.set_font("Arial", size=8)
    if not grouped.empty:
        preview = grouped.head(10).to_string(index=False)
        pdf.multi_cell(0, 4, preview)
    else:
        pdf.multi_cell(0, 4, "No grouped data available.")

    pdf.ln(4)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, "AI Analysis", ln=True)

    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 5, ai_report or "No AI analysis available.")

    if chart_path and os.path.exists(chart_path):
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Visualization", ln=True)
        pdf.image(chart_path, x=10, y=30, w=180)

    pdf.output(output_path)
    logging.info("PDF report exported to %s", output_path)
    return output_path


# ---------------------- Pipeline Orchestration ----------------------


def run_full_pipeline(input_path: str = DEFAULT_INPUT_PATH) -> Tuple[pd.DataFrame, pd.DataFrame, ProcessingSummary, str, Optional[str]]:
    """Run the full automated pipeline: load, clean, transform, AI, visualize, PDF."""

    logging.info("Starting full pipeline")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df_raw = load_dataset(input_path)
    df_clean, summary = clean_dataset(df_raw)

    df_clean.to_csv(CLEANED_OUTPUT_PATH, index=False)
    logging.info("Cleaned data saved to %s", CLEANED_OUTPUT_PATH)

    df_transformed, grouped, summary = apply_transformations(df_clean, summary)

    chart_path = generate_bar_chart(grouped, CHART_PATH)

    ai_report = generate_ai_analysis(df_transformed, grouped)

    export_pdf_report(summary, grouped, ai_report, chart_path=chart_path, output_path=PDF_REPORT_PATH)

    logging.info("Pipeline finished successfully")

    return df_transformed, grouped, summary, ai_report, chart_path


# ---------------------- CLI Interface ----------------------


def cli_menu() -> None:
    """Simple text-based CLI menu as requested."""

    while True:
        print("\nData AI Automator - Menu")
        print("1. Process Data (clean + transform + AI + PDF)")
        print("2. Generate AI Report only (requires existing cleaned_output.csv)")
        print("3. Export PDF only (requires existing cleaned_output.csv)")
        print("4. Exit")

        choice = input("Select an option (1-4): ").strip()

        if choice == "1":
            try:
                run_full_pipeline(DEFAULT_INPUT_PATH)
            except Exception as exc:
                logging.error("Error during full pipeline: %s", exc)
        elif choice == "2":
            try:
                if not os.path.exists(CLEANED_OUTPUT_PATH):
                    print(f"{CLEANED_OUTPUT_PATH} not found. Run option 1 first.")
                    continue
                df_clean = pd.read_csv(CLEANED_OUTPUT_PATH)
                _, grouped, summary = apply_transformations(df_clean, ProcessingSummary(
                    rows_before=len(df_clean),
                    rows_after_cleaning=len(df_clean),
                    rows_after_transform=len(df_clean),
                    removed_duplicates=0,
                    filled_missing_numeric=0,
                    filled_missing_text=0,
                    removed_invalid_rows=0,
                ))
                ai_report = generate_ai_analysis(df_clean, grouped)
                print("\nAI Report:\n")
                print(ai_report)
            except Exception as exc:
                logging.error("Error generating AI report: %s", exc)
        elif choice == "3":
            try:
                if not os.path.exists(CLEANED_OUTPUT_PATH):
                    print(f"{CLEANED_OUTPUT_PATH} not found. Run option 1 first.")
                    continue
                df_clean = pd.read_csv(CLEANED_OUTPUT_PATH)
                df_transformed, grouped, summary = apply_transformations(df_clean, ProcessingSummary(
                    rows_before=len(df_clean),
                    rows_after_cleaning=len(df_clean),
                    rows_after_transform=len(df_clean),
                    removed_duplicates=0,
                    filled_missing_numeric=0,
                    filled_missing_text=0,
                    removed_invalid_rows=0,
                ))
                ai_report = generate_ai_analysis(df_transformed, grouped)
                export_pdf_report(summary, grouped, ai_report, chart_path=CHART_PATH, output_path=PDF_REPORT_PATH)
            except Exception as exc:
                logging.error("Error exporting PDF: %s", exc)
        elif choice == "4":
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please select 1-4.")


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Supports automatic end-to-end mode.
    """

    parser = argparse.ArgumentParser(description="Data processing and AI automation script")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=DEFAULT_INPUT_PATH,
        help="Input file path (CSV, Excel, JSON)",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Run full pipeline automatically without showing the menu.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> None:
    load_dotenv()
    setup_logging()

    args = parse_args(argv)

    if args.auto:
        try:
            run_full_pipeline(args.input)
        except Exception as exc:
            logging.error("Automatic pipeline failed: %s", exc)
            sys.exit(1)
    else:
        cli_menu()


if __name__ == "__main__":
    main()
