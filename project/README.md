# Python Automation Script With Data Processing + AI API Integration

## Overview

This project is a self-contained Python automation tool that:

- **Automatically detects input file type** (CSV, Excel, JSON).
- **Cleans and transforms a dataset** using `pandas`.
- **Generates insights with an AI model** (Gemini by default, structure is compatible with other backends like OpenAI / HuggingFace).
- **Creates a bar chart visualization** (top products by sales) using `matplotlib`.
- **Exports a PDF report** containing cleaning details, transformations summary, grouped data preview, AI analysis, and the chart.
- **Provides both a CLI menu and an automatic mode** using command-line arguments.

Main entry point: `data_ai_automator.py`.

---

## Project Structure

```text
project/
├── data_ai_automator.py
├── requirements.txt
├── .env              # (ignored in Git; contains GEMINI_API_KEY)
├── README.md
└── sample.csv        # demo dataset
```

---

## Dataset Used (`sample.csv`)

The sample dataset simulates simple sales transactions with the following columns:

- **order_id** – Unique identifier of the order.
- **date** – Order date.
- **customer_name** – Name of the customer.
- **product** – Product name (e.g., Notebook, Laptop, Pen).
- **category** – Product category (Stationery, Electronics, Furniture, etc.).
- **price** – Unit price of the product.
- **quantity** – Quantity purchased.
- **city** – Customer city.

The script is generic enough to work with other datasets as long as they are CSV/Excel/JSON tables. If `price`/`quantity` are not present, a fallback logic still runs using a default `total` column.

---

## Cleaning Steps (PART A)

Cleaning is implemented in the `clean_dataset` function and includes **at least four** operations:

1. **Remove duplicates**
   - Uses `DataFrame.drop_duplicates()` to remove duplicated rows.

2. **Handle missing values**
   - **Numeric columns**: Missing values are replaced with the **median** of that column.
   - **Text columns**: Missing values are replaced with the **mode** (most frequent value) or the string `"unknown"` if no mode exists.

3. **Standardize formats**
   - **Dates**: Columns whose names contain `date`, `time`, or `timestamp` are parsed to `datetime` using `pandas.to_datetime` (errors coerced to NaT).
   - **Text**: Object-type columns are converted to lowercase using `.astype(str).str.lower()`.
   - **Numeric-like text**: Columns where the majority of values look numeric are converted using `to_numeric`.

4. **Remove invalid entries**
   - For all numeric columns, rows with **negative values** are treated as invalid and removed.

5. **Rename columns to snake_case**
   - Column names are normalized by `to_snake_case` (spaces/hyphens to underscores, special characters removed, lowercased).

A `ProcessingSummary` dataclass captures key metrics:

- Rows before cleaning.
- Rows after cleaning.
- Rows after transformations.
- Number of removed duplicates.
- Number of missing numeric values filled.
- Number of missing text values filled.
- Number of invalid rows removed.

---

## Transformation Steps (PART A)

Transformations are implemented in `apply_transformations` and include **at least three** steps:

1. **New calculated column** – `total`
   - If columns resembling `price`/`unit_price` and `quantity`/`qty` are found, `total = price * quantity`.
   - Otherwise, a default `total = 1` is used so later aggregation still works.

2. **Grouping & aggregation**
   - Groups data by:
     - `product`, or
     - `item`, or
     - `category`, or
     - falls back to the **first column**.
   - Aggregates:
     - `total_sales` = sum of `total`.
     - `avg_total` = mean of `total`.
     - `count_rows` = count of rows.

3. **Filtering**
   - Filters to keep **only rows with positive `total`**.

4. **Sorting**
   - Sorts rows by `total` in descending order.

5. **Type conversions**
   - Ensures `total_sales` and `avg_total` in the grouped DataFrame are numeric.

The cleaned and transformed dataset is saved to **`cleaned_output.csv`** in the project root.

---

## AI Integration (PART B)

### Default Provider: Gemini

- The project uses **Gemini** (via `google-generativeai`) as the default AI backend.
- It is structured so other backends (e.g., **OpenAI**, **HuggingFace**) can be added or swapped by replacing the client initialization and the `generate_ai_analysis` function.

### API Key & Environment

- Store your Gemini API key in `.env`:

  ```env
  GEMINI_API_KEY=your_gemini_api_key_here
  ```

- The script loads environment variables using **`python-dotenv`** (`load_dotenv()`).

### Prompt Contents

The AI prompt built in `build_ai_prompt` includes:

- **Dataset summary**: `df.describe(include="all")`.
- **First few rows**: `df.head()` converted to Markdown.
- **Important columns / schema**: Implicitly part of `describe` and `head`.
- **Grouped / aggregated data**: Top groups from the grouped DataFrame converted to Markdown.

The AI is asked to provide:

- A high-level dataset summary.
- Key patterns or insights.
- Anomalies or quality issues.
- Business recommendations.

### Error Handling

The AI integration includes defensive logic for:

- **Invalid / missing API key**
  - If `GEMINI_API_KEY` is absent or invalid, AI is skipped and a clear message is returned.
- **No internet / connection errors**
  - Detects common network/connection error messages and returns a user-friendly message.
- **Rate limits / quota**
  - Detects rate-limit or quota-related messages and suggests retrying later.

Any unexpected exceptions are logged and turned into a human-readable message.

---

## Visualization (Bonus)

- Implemented in `generate_bar_chart`.
- Creates a **matplotlib bar chart** of the **top N products/categories by `total_sales`**.
- Saves chart to `top_products.png` in the project folder.
- The chart is referenced and embedded in the generated PDF (if available).

---

## PDF Report Export (Bonus)

- Implemented in `export_pdf_report` using **FPDF (fpdf2)**.
- The PDF includes:
  - **Cleaning summary** (rows before/after, duplicates removed, missing values filled, invalid rows removed).
  - **Transformations summary** (description of created `total` column, grouping, filtering, sorting).
  - **Preview of grouped data** (first 10 rows rendered as text).
  - **AI analysis text**.
  - **Visualization page** with `top_products.png`, if the image exists.
- Output file: `report.pdf`.

---

## Logging (Bonus)

- Uses the built-in **`logging`** module instead of print for pipeline steps.
- Configured via `setup_logging` with messages like:
  - `File loaded`
  - `Cleaning started`
  - `Cleaning complete`
  - `Transformations complete`
  - `AI processing started`
  - `PDF report exported`
  - Plus error logs when something fails.

Logs are written to **stdout** by default.

---

## CLI Menu (Bonus)

The script provides a simple text-based **CLI menu** via `cli_menu()` when run without `--auto`:

- **Option 1: Process Data**  
  Runs the full pipeline: load → clean → transform → visualize → AI → PDF.

- **Option 2: Generate AI Report**  
  Uses existing `cleaned_output.csv` to re-run transformations and generate only the AI report, printing it to the terminal.

- **Option 3: Export PDF**  
  Uses existing `cleaned_output.csv` to run transformations and AI again and regenerate the PDF report.

- **Option 4: Exit**

When called with `--auto`, the script bypasses the menu and runs the full pipeline directly.

---

## Installation & Setup

1. **Create and activate a virtual environment** (recommended):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

2. **Install dependencies** from `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the `.env` file**:

   - Open `project/.env` and set:

     ```env
     GEMINI_API_KEY=your_gemini_api_key_here
     ```

---

## How to Run

From the `project/` directory:

### 1. Interactive CLI Menu

```bash
python data_ai_automator.py
```

You will see a menu like:

```text
Data AI Automator - Menu
1. Process Data (clean + transform + AI + PDF)
2. Generate AI Report only (requires existing cleaned_output.csv)
3. Export PDF only (requires existing cleaned_output.csv)
4. Exit
```

### 2. Automatic End-to-End Run

```bash
python data_ai_automator.py --auto --input sample.csv
```

This will:

- Load `sample.csv`.
- Clean and transform the data.
- Save `cleaned_output.csv`.
- Generate `top_products.png`.
- Call the AI model to generate an analysis.
- Export `report.pdf`.

You can also specify a different input file:

```bash
python data_ai_automator.py --auto --input path/to/your_file.xlsx
```

Supported types: **CSV**, **Excel (`.xls`, `.xlsx`)**, **JSON**.

---

## Example Outputs

After a successful automatic run, you should see these files in `project/`:

- **`cleaned_output.csv`** – Cleaned and transformed dataset.
- **`top_products.png`** – Bar chart of top products/categories by total sales.
- **`report.pdf`** – PDF with cleaning summary, grouped data preview, AI analysis, and chart.

---

## Example Terminal Logs

A typical log sequence might look like:

```text
2025-01-01 10:00:00,123 - INFO - Starting full pipeline
2025-01-01 10:00:00,456 - INFO - File loaded: sample.csv
2025-01-01 10:00:00,789 - INFO - Cleaning started
2025-01-01 10:00:01,012 - INFO - Cleaning complete
2025-01-01 10:00:01,345 - INFO - Cleaned data saved to cleaned_output.csv
2025-01-01 10:00:01,678 - INFO - Transformations started
2025-01-01 10:00:02,001 - INFO - Transformations complete
2025-01-01 10:00:02,345 - INFO - Visualization saved to top_products.png
2025-01-01 10:00:02,678 - INFO - AI processing started
2025-01-01 10:00:03,012 - INFO - PDF report exported to report.pdf
2025-01-01 10:00:03,345 - INFO - Pipeline finished successfully
```

On errors (e.g., missing API key or network failure), you will see corresponding `ERROR` log messages.

---

## Code Explanation (High Level)

- **`setup_logging`** – Configures the `logging` module.
- **`detect_file_type`** – Infers file type from extension.
- **`load_dataset`** – Loads CSV/Excel/JSON using `pandas`.
- **`to_snake_case`** – Normalizes column names.
- **`clean_dataset`** – Encapsulates all cleaning logic and returns a `ProcessingSummary`.
- **`apply_transformations`** – Adds calculated `total` column, groups/aggregates, filters, sorts.
- **`generate_bar_chart`** – Creates a bar chart of top groups by total sales.
- **`configure_gemini`** – Configures Gemini using `GEMINI_API_KEY` from `.env`.
- **`build_ai_prompt`** – Creates the multi-part prompt for the AI model.
- **`generate_ai_analysis`** – Calls Gemini API and returns analysis text with error handling.
- **`export_pdf_report`** – Assembles and writes the PDF report with FPDF.
- **`run_full_pipeline`** – Orchestrates the whole process and returns key outputs.
- **`cli_menu`** – Implements the text-based interactive menu.
- **`parse_args` / `main`** – Handle command-line arguments and decide whether to run in automatic or menu mode.

---

## Challenges & Learnings

- **File format handling**: Designing a loader that works uniformly for CSV, Excel, and JSON requires clear detection and robust error messages for unsupported formats.
- **Generic cleaning & transformation**: The script must handle arbitrary datasets while still performing meaningful cleaning and transformations, which is why it relies on column name heuristics (e.g., `price`, `quantity`, `product`, `category`).
- **AI robustness**: Real-world AI calls can fail due to missing keys, rate limits, or connectivity issues. Centralizing client initialization and catching OpenAI-specific errors leads to a more resilient tool.
- **PDF generation**: Combining text (summaries, grouped data, AI analysis) with images (charts) requires layout control, which FPDF provides in a lightweight way.
- **Automation UX**: Providing both an interactive menu and a non-interactive `--auto` mode makes the script suitable for quick manual use and for scheduled/automated runs.

This project is ready to be used as a **template** for more advanced data-processing + AI workflows (e.g., switching to Gemini or HuggingFace, adding more visualizations, or integrating with other systems).
