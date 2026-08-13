# Data Analytics System Design Document

## 1. Executive Summary & Architecture Overview

### 1.1 Executive Summary

This document defines the analytical architecture for processing and visualizing the raw e-commerce sales dataset (`data.csv`). The dataset contains **200 order records** spanning **January 1, 2024 through December 28, 2024**, with **no missing values** across any of the 11 columns. The architecture delivers a complete pipeline from raw data ingestion through interactive dashboard visualization, producing cleaned analytical datasets, summary statistics, and a Gradio-based business intelligence dashboard with executive KPI cards and Plotly charts.

### 1.2 Architecture Overview

The system follows a three-phase pipeline:

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────────┐
│   Raw Data       │     │   Data Pipeline       │     │   BI Dashboard          │
│   data.csv       │────▶│   (data_pipeline.py)  │────▶│   (app.py)              │
│   (200 rows)     │     │                       │     │   Gradio 6 + Plotly    │
└─────────────────┘     │ Outputs:              │     │                         │
                         │ • cleaned_data.csv    │     │ Tabs:                   │
                         │ • summary_stats.csv   │     │ • Executive Dashboard   │
                         └──────────────────────┘     │ • Regional Analytics    │
                                                      │ • Product Performance   │
                                                      │ • Summary Data View     │
                                                      └─────────────────────────┘
```

**Validation Layer:** `_validate.py` — QA reporter validates calculation consistency across pipeline outputs.

---

## 2. Column Schema of `data.csv` (from Inspection)

| Column Name        | Data Type (Python)   | Sample Values                          | Non-Null | Unique Values | Notes                        |
|--------------------|----------------------|----------------------------------------|----------|---------------|------------------------------|
| `order_id`         | `str` (object)       | ORD-1001, ORD-1002, …                 | 200      | 200           | Primary key; unique per row  |
| `order_date`       | `str` (object)       | 2024-05-20, 2024-02-17, …             | 200      | 158           | ISO format; needs parse      |
| `customer_segment` | `str` (object)       | Small Business, Consumer, Corporate    | 200      | 3             | Categorical                  |
| `region`           | `str` (object)       | North, South, West, East               | 200      | 4             | Categorical                  |
| `category`         | `str` (object)       | Electronics, Furniture, Office Supplies, Apparel | 200 | 4         | Categorical                  |
| `product_name`     | `str` (object)       | Wireless Ergonomic Mouse, …            | 200      | 16            | Categorical                  |
| `quantity`         | `int64`              | 1, 2, 3, …, 10                        | 200      | 7             | Range: [1, 10]              |
| `unit_price`       | `float64`            | 29.99, 19.99, 9.99, …                 | 200      | 16            | Range: [9.99, 449.99]       |
| `discount_pct`     | `float64`            | 0.05, 0.20, 0.0, 0.15, 0.10          | 200      | 5             | Range: [0.0, 0.20]          |
| `shipping_cost`    | `float64`            | 23.40, 20.04, 23.96, …                | 200      | 194           | Range: [5.06, 29.92]        |
| `payment_method`   | `str` (object)       | Crypto, Bank Transfer, Credit Card, PayPal | 200 | 4           | Categorical                  |

**Total rows:** 200  
**Missing values:** None (0 nulls in any column)  
**Date range:** 2024-01-01 through 2024-12-28 (not spanning a full calendar year; missing Dec 29–31)

---

## 3. Key KPI Definitions & Mathematical Formulas

All monetary values are in USD.

### 3.1 Core Financial KPIs

| KPI | Definition | Formula | Example Calculation |
|-----|-----------|---------|-------------------|
| **Total Revenue (Gross)** | Sum of gross revenue (before discount) across all orders | `Σ (quantity × unit_price)` | — |
| **Total Discount Amount** | Sum of discounts applied across all line items | `Σ (quantity × unit_price × discount_pct)` | — |
| **Net Revenue** | Revenue after discounts (actual money collected for product) | `Σ (quantity × unit_price × (1 - discount_pct))` | — |
| **Total Orders** | Count of unique order IDs | `COUNT(DISTINCT order_id)` | 200 |
| **Total Units Sold** | Sum of all quantities ordered | `Σ quantity` | — |
| **Average Order Value (AOV)** | Net Revenue per order | `Net Revenue / Total Orders` | — |
| **Total Shipping Cost** | Sum of all shipping costs | `Σ shipping_cost` | — |
| **Net Profit Contribution** | Net Revenue minus Shipping Cost (proxy margin) | `Net Revenue - Total Shipping Cost` | — |
| **Profit Margin %** | Net Profit Contribution as a percentage of Net Revenue | `(Net Revenue - Shipping Cost) / Net Revenue × 100` | — |

### 3.2 Detailed Per-Row Formulas

```
Gross Revenue           = quantity × unit_price
Discount Amount         = quantity × unit_price × discount_pct
Net Revenue             = quantity × unit_price × (1 - discount_pct)
Net Profit (contribution) = Net Revenue - shipping_cost
Profit Margin %         = (Net Profit / Net Revenue) × 100
```

### 3.3 Derivative KPIs for Dashboard

| KPI | Formula |
|-----|---------|
| Revenue per Category | `SUM(Net Revenue) GROUP BY category` |
| Revenue per Region | `SUM(Net Revenue) GROUP BY region` |
| Monthly Revenue Trend | `SUM(Net Revenue) GROUP BY month` |
| Orders per Customer Segment | `COUNT(DISTINCT order_id) GROUP BY customer_segment` |
| Average Discount % | `AVG(discount_pct)` (overall) |
| Top Products by Revenue | `SUM(Net Revenue) GROUP BY product_name ORDER BY revenue DESC` |
| Avg Quantity per Order | `SUM(quantity) / COUNT(DISTINCT order_id)` |

---

## 4. Data Cleaning Rules & Output Specifications

### 4.1 Data Cleaning Rules

The data is already relatively clean (no nulls), but the pipeline must apply the following transformations:

| # | Rule | Description | Implementation |
|---|------|-------------|----------------|
| R1 | **Parse Date** | Convert `order_date` from string to `datetime` | `pd.to_datetime(df['order_date'])` |
| R2 | **Compute Gross Revenue** | Pre-discount revenue per row | `quantity × unit_price` |
| R3 | **Compute Discount Amount** | Discount value per row | `quantity × unit_price × discount_pct` |
| R4 | **Compute Net Revenue** | Revenue after discount per row | `gross_revenue - discount_amount` |
| R5 | **Compute Net Profit** | Net Revenue minus Shipping Cost | `net_revenue - shipping_cost` |
| R6 | **Compute Profit Margin %** | Profitability ratio per row | `(net_profit / net_revenue) × 100` |
| R7 | **Extract Month/Year** | Derive temporal columns | `order_date.dt.month`, `order_date.dt.year`, `order_date.dt.strftime('%b')` |
| R8 | **Verify No Nulls** | Assert zero nulls after processing | `assert df.isnull().sum().sum() == 0` |
| R9 | **Verify No Negative Values** | Ensure all quantities and prices positive | `assert (df['quantity'] > 0).all()` |
| R10 | **Sort** | Sort by order_date then order_id | `df.sort_values(['order_date', 'order_id'])` |
| R11 | **Round** | Round floats to 2 decimal places | `df.round(2)` |

### 4.2 Output: `cleaned_data.csv` — Column Specifications

| Column Name | Source / Derivation | Data Type | Description |
|-------------|-------------------|-----------|-------------|
| `order_id` | Raw | `str` | Unique order identifier |
| `order_date` | R1 — parsed | `datetime` (YYYY-MM-DD) | Order date as datetime |
| `year` | R7 — extracted | `int` | Calendar year (2024) |
| `month` | R7 — extracted | `int` | Calendar month (1–12) |
| `month_name` | R7 — derived | `str` | Month abbreviation (Jan, Feb, … Dec) |
| `customer_segment` | Raw | `str` | Consumer / Corporate / Small Business |
| `region` | Raw | `str` | North / South / East / West |
| `category` | Raw | `str` | Apparel / Electronics / Furniture / Office Supplies |
| `product_name` | Raw | `str` | Product name |
| `quantity` | Raw | `int` | Units ordered |
| `unit_price` | Raw | `float` | Price per unit |
| `discount_pct` | Raw | `float` | Discount as decimal (0.00–0.20) |
| `shipping_cost` | Raw | `float` | Shipping cost |
| `payment_method` | Raw | `str` | Crypto / Bank Transfer / Credit Card / PayPal |
| `gross_revenue` | R2 — computed | `float` | `quantity × unit_price` |
| `discount_amount` | R3 — computed | `float` | `quantity × unit_price × discount_pct` |
| `net_revenue` | R4 — computed | `float` | `gross_revenue - discount_amount` |
| `net_profit` | R5 — computed | `float` | `net_revenue - shipping_cost` |
| `profit_margin_pct` | R6 — computed | `float` | `(net_profit / net_revenue) × 100` |

**Expected row count:** 200  
**Expected columns:** 19  

### 4.3 Output: `summary_stats.csv` — Column Specifications

Wide format with one row per aggregation group.

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `group_level` | `str` | Aggregation level: `overall`, `category`, `region`, `segment`, `month` |
| `group_name` | `str` | Specific group value (e.g., `Electronics`, `North`, `Consumer`, `2024-05`, or `All`) |
| `total_orders` | `int` | Count of unique order IDs |
| `total_units_sold` | `int` | Sum of quantity |
| `total_gross_revenue` | `float` | Sum of gross_revenue |
| `total_discount_amount` | `float` | Sum of discount_amount |
| `total_net_revenue` | `float` | Sum of net_revenue |
| `total_shipping_cost` | `float` | Sum of shipping_cost |
| `total_net_profit` | `float` | Sum of net_profit |
| `avg_order_value` | `float` | `total_net_revenue / total_orders` |
| `avg_profit_margin_pct` | `float` | Average of profit_margin_pct across rows in group |
| `avg_discount_pct` | `float` | Average of discount_pct across rows in group |

**Aggregation levels required (24 total rows):**

| Level | Rows | group_name examples |
|-------|------|-------------------|
| `overall` | 1 | `All` |
| `category` | 4 | `Apparel`, `Electronics`, `Furniture`, `Office Supplies` |
| `region` | 4 | `East`, `North`, `South`, `West` |
| `segment` | 3 | `Consumer`, `Corporate`, `Small Business` |
| `month` | 12 | `2024-01`, `2024-02`, …, `2024-12` |

**Sort order:** By `group_level` (alphabetical), then by `group_name` (alphabetical) within each level.

---

## 5. Dashboard Layout Recommendations

### 5.1 Overall Structure — Tabbed Navigation

The dashboard uses **Gradio 6 (`gr.Blocks`)** with `gr.themes.Soft()` and **4 tabs**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Executive Dashboard] [Regional Analytics] [Product Performance] [Summary] │
├─────────────────────────────────────────────────────────────────────────────┤
│                              (Tab Content)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Global Filters** (placed above tabs or in collapsible panel):

| Filter | Widget Type | Options | Default |
|--------|-------------|---------|---------|
| **Region** | `gr.CheckboxGroup` or multi-select `gr.Dropdown` | North, South, East, West | All selected |
| **Category** | `gr.CheckboxGroup` or multi-select `gr.Dropdown` | Apparel, Electronics, Furniture, Office Supplies | All selected |
| **Customer Segment** | `gr.CheckboxGroup` or multi-select `gr.Dropdown` | Consumer, Corporate, Small Business | All selected |
| **Date Range** | Two `gr.Number` or `gr.Slider` (month range) | 1–12 | 1–12 (full year) |

All charts and KPI cards reactively update via `gr.on(...).then(...)` or `filter_input.change(...)`.

### 5.2 Tab 1: Executive Dashboard (Executive Overview)

**KPI Metric Cards (top row — 4 cards, each using `gr.HTML` with styled divs):**

| Card | Data Source | Format |
|------|-------------|--------|
| **Total Net Revenue** | `summary_stats` where `group_level='overall'` → `total_net_revenue` | `$XX,XXX.XX` |
| **Total Orders** | Same → `total_orders` | `XXX` |
| **Average Order Value** | Same → `avg_order_value` | `$XXX.XX` |
| **Profit Margin %** | Same → `avg_profit_margin_pct` | `XX.X%` |

**Charts (below KPI cards, arranged in a 2×2 or 1+2 grid):**

| Chart | Type (Plotly Express) | Data Source | Specification |
|-------|-----------------------|-------------|---------------|
| **Monthly Net Revenue Trend** | `px.line` | summary_stats filtered to `group_level='month'` | x=`group_name` (YYYY-MM), y=`total_net_revenue`, markers, smooth line, title: "Monthly Net Revenue Trend (2024)" |
| **Revenue by Category** | `px.pie` | summary_stats filtered to `group_level='category'` | values=`total_net_revenue`, names=`group_name`, title: "Revenue Distribution by Category", consistent colors |
| **Orders by Customer Segment** | `px.bar` | summary_stats filtered to `group_level='segment'` | x=`group_name`, y=`total_orders`, color=`group_name`, title: "Orders by Customer Segment" |
| **Avg Order Value by Segment** | `px.bar` | summary_stats filtered to `group_level='segment'` | x=`group_name`, y=`avg_order_value`, title: "AOV by Customer Segment" |

### 5.3 Tab 2: Regional Analytics

**Charts:**

| Chart | Type | Specification |
|-------|------|--------------|
| **Net Revenue by Region** | `px.bar` | x=`group_name` (region), y=`total_net_revenue`, color=`group_name`, title: "Net Revenue by Region" |
| **Regional Revenue Share** | `px.pie` (donut, hole=0.4) | names=`group_name`, values=`total_net_revenue`, title: "Regional Revenue Share" |
| **Average Order Value by Region** | `px.bar` | x=`group_name`, y=`avg_order_value`, color=`group_name`, title: "AOV by Region" |
| **Region × Category Heatmap** | `px.imshow` or `px.density_heatmap` | Pivot of cleaned_data: index=region, columns=category, values=SUM(net_revenue), title: "Revenue Heatmap: Region × Category", text_auto=True |

### 5.4 Tab 3: Product Performance

**Charts:**

| Chart | Type | Specification |
|-------|------|--------------|
| **Top Products by Revenue** | `px.bar` (horizontal) | Cleaned data grouped by `product_name`, SUM(net_revenue), top 10, y=`product_name`, x=`total_net_revenue`, sorted descending |
| **Revenue by Product Category** | `px.bar` (stacked) | x=`category`, y=`net_revenue` sum, color=`product_name`, title: "Product Breakdown by Category" |
| **Units Sold by Product** | `px.bar` | x=`product_name`, y=SUM(`quantity`), sorted descending, title: "Total Units Sold per Product" |

### 5.5 Tab 4: Summary Data View

**Components:**

| Component | Gradio Widget | Data |
|-----------|--------------|------|
| **Cleaned Data Table** | `gr.DataFrame` | Full `cleaned_data.csv` (interactive, searchable) |
| **Download Button** | `gr.DownloadButton` | Downloads `cleaned_data.csv` |
| **Summary Stats Table** | `gr.DataFrame` | Full `summary_stats.csv` |
| **Download Summary** | `gr.DownloadButton` | Downloads `summary_stats.csv` |

---

## 6. Detailed Team Assignments

### 6.1 Data Engineer (`data_engineer`) — File: `data_pipeline.py`

**Objective:** Build and execute a Python script that loads, cleans, transforms, and validates the raw data, producing exactly two output CSV files: `cleaned_data.csv` and `summary_stats.csv`.

**Input:** `data.csv` (as described in Section 2)

**Behavioral Requirements:**

1. **Load & Parse:**
   - Use `pandas.read_csv()` to load `data.csv`.
   - Parse `order_date` as datetime using `pd.to_datetime()`.
   - Sort the DataFrame by `order_date` ascending, then `order_id` ascending.

2. **Clean & Compute:**
   - Apply all data cleaning rules from Section 4.1 (R1–R11).
   - Compute all derived columns as defined in Section 4.2.

3. **Output `cleaned_data.csv`:**
   - Must contain all 19 columns specified in Section 4.2 in that order.
   - Write with `index=False`.
   - Round all float columns to 2 decimal places.

4. **Compute & Output `summary_stats.csv`:**
   - Compute all aggregation levels (overall, category, region, segment, month) as specified in Section 4.3.
   - Columns must match Section 4.3 exactly.
   - Sort by `group_level` alphabetically, then by `group_name` alphabetically within each level.
   - Round all float columns to 2 decimal places.
   - Write with `index=False`.

5. **Validation Assertions (inline in script):**
   ```python
   assert len(cleaned_df) == 200, "Row count mismatch"
   assert cleaned_df.isnull().sum().sum() == 0, "Null values found"
   assert (cleaned_df[['quantity', 'unit_price', 'net_revenue', 'net_profit']] >= 0).all().all(), "Negative values found"
   assert len(summary_df) == 24, f"Expected 24 summary rows, got {len(summary_df)}"
   ```

6. **Deliverables:** A single file `data_pipeline.py` that runs via `uv run data_pipeline.py` and produces both CSVs in the sandbox directory.

### 6.2 Dashboard Engineer (`dashboard_engineer`) — Files: `app.py`, `_validate.py`

**Objective:** Build an interactive Gradio 6 dashboard (`app.py`) that reads `cleaned_data.csv` and `summary_stats.csv`, renders the KPI cards, charts, and filters as described in Section 5. Also produce a validation script `_validate.py`.

**Inputs:** `cleaned_data.csv`, `summary_stats.csv`

**Behavioral Requirements for `app.py`:**

1. **Gradio App:**
   - Use `gr.Blocks()` with `gr.themes.Soft()`.
   - Implement tabbed navigation with 4 tabs exactly as specified in Section 5.
   - Use `gr.HTML` for styled KPI metric cards with large font values.
   - All charts are interactive Plotly Express figures using `gr.Plot()`.

2. **Dynamic Filter Reactivity:**
   - Load `cleaned_data.csv` and `summary_stats.csv` into global `gr.State()` variables.
   - Implement filter dropdowns/checkboxes for region, category, customer segment, and date range.
   - Use `filter_input.change(...)` or `gr.on(triggers=[...], fn=update_dashboard, outputs=[...])` to recompute all charts and KPIs on filter change.
   - Filter logic: apply filters to the cleaned_data DataFrame before computing aggregations for charts; for summary_stats-level charts, either pre-filter or re-aggregate from filtered cleaned_data.

3. **Charts:**
   - Use `plotly.express` for all charts.
   - Apply consistent categorical color palettes (see Appendix B).
   - All charts must have titles and axis labels.
   - Charts must be responsive within their container.

4. **Data Tables (Tab 4):**
   - `gr.DataFrame(value=cleaned_data)` for the full cleaned dataset.
   - `gr.DataFrame(value=summary_stats)` for the summary stats.
   - `gr.DownloadButton(label="Download Cleaned Data", value="cleaned_data.csv")`.
   - `gr.DownloadButton(label="Download Summary Stats", value="summary_stats.csv")`.

**Behavioral Requirements for `_validate.py`:**

1. Load `cleaned_data.csv` and `summary_stats.csv`.
2. Recompute all KPIs from `cleaned_data.csv` using pandas groupby operations.
3. Compare recomputed values against `summary_stats.csv` values with a tolerance of 0.02.
4. Print detailed pass/fail for each KPI at each aggregation level.
5. Exit with code 0 on pass, code 1 on fail.

Example validation logic:
```python
# Recompute overall net revenue from cleaned data
recomputed = cleaned_df['net_revenue'].sum()
stored = summary_df.loc[summary_df['group_name']=='All', 'total_net_revenue'].values[0]
assert abs(recomputed - stored) < 0.02, f"Mismatch: {recomputed} vs {stored}"
```

**Deliverables:**
- `app.py` — The Gradio 6 dashboard application.
- `_validate.py` — The validation/QA script.

### 6.3 QA Reporter (`qa_reporter`) — File: `executive_summary.md`

**Objective:** Audit the entire pipeline for data consistency, calculation accuracy, and business logic correctness. Produce an executive business report.

**Inputs:** `data.csv`, `cleaned_data.csv`, `summary_stats.csv`, review of `data_pipeline.py`, `app.py`, and `_validate.py`.

**Behavioral Requirements:**

1. **Run Validation:**
   - Execute `uv run _validate.py` and capture its output.
   - Verify all assertions pass.

2. **Manual QA Checks (spot-check):**
   - Hand-calculate 5 random rows from `data.csv` to verify the derived columns (net_revenue, net_profit, profit_margin_pct) match `cleaned_data.csv`.
   - Hand-calculate overall Total Orders, Total Net Revenue, AOV, and Profit Margin % to cross-check against `summary_stats.csv`.
   - Document any discrepancies found (if any).

3. **Produce `executive_summary.md`:**
   - A comprehensive business report written in markdown with the following structure:

```markdown
# Executive Business Summary — E-Commerce Sales Analysis (2024)

## 1. Data Quality Assessment
- Total records: 200
- Missing values: None
- Data quality score: 100% (no issues found)
- QA Verification: PASS (all KPIs validated, spot-checks confirmed)

## 2. Executive KPIs at a Glance
| KPI | Value |
|-----|-------|
| Total Net Revenue | $XX,XXX.XX |
| Total Orders | 200 |
| Average Order Value (AOV) | $XXX.XX |
| Average Profit Margin | XX.X% |
| Total Units Sold | XXX |
| Total Shipping Cost | $X,XXX.XX |

## 3. Category Performance
[Table from summary_stats.csv — category level with calculated analysis]
[Insight: which categories drive revenue vs. margin]

## 4. Regional Performance
[Table from summary_stats.csv — region level]
[Analysis: best and worst performing regions]

## 5. Customer Segment Insights
[Table from summary_stats.csv — segment level]
[Analysis: which segment has highest AOV, most orders, best margins]

## 6. Monthly Trends
[Table from summary_stats.csv — month level]
[Analysis: seasonal patterns, growth/decline trends, peak months]

## 7. Product-Level Insights
[Top 5 products by revenue]
[Top 5 products by quantity sold]

## 8. Key Findings & Recommendations
- At least 3 actionable business recommendations based on the data.
- Examples: inventory strategy, regional marketing focus, discount optimization.

## 9. QA Validation Report
- Validation script output (copy/pasted)
- Spot-check results (row IDs checked, expected vs actual)
- Final verdict: ✔ PASS / ✘ FAIL
```

4. **Deliverables:** `executive_summary.md` — saved to the sandbox directory.

---

## Appendix A: File Manifest

| File Name | Produced By | Depends On | Description |
|-----------|------------|------------|-------------|
| `data.csv` | (provided) | — | Raw e-commerce data (200 rows, 11 cols) |
| `design.md` | **data_strategist** | `data.csv` | This document — full design specification |
| `data_pipeline.py` | **data_engineer** | `data.csv` | ETL pipeline script |
| `cleaned_data.csv` | `data_pipeline.py` | `data.csv` | Cleaned dataset (200 rows, 19 cols) |
| `summary_stats.csv` | `data_pipeline.py` | `data.csv` | Aggregated KPIs (24 rows, 12 cols) |
| `app.py` | **dashboard_engineer** | `cleaned_data.csv`, `summary_stats.csv` | Gradio 6 dashboard |
| `_validate.py` | **dashboard_engineer** | `cleaned_data.csv`, `summary_stats.csv` | Validation/QA script |
| `executive_summary.md` | **qa_reporter** | All of the above | Business report |

## Appendix B: Consistent Color Palette

| Category | Color Hex | |
|----------|-----------|-|
| Apparel | `#66c2a5` | 🟢 |
| Electronics | `#fc8d62` | 🟠 |
| Furniture | `#8da0cb` | 🔵 |
| Office Supplies | `#e78ac3` | 🟣 |

| Region | Color Hex | |
|--------|-----------|-|
| North | `#a6d854` | 🟢 |
| South | `#ffd92f` | 🟡 |
| East | `#e5c494` | 🟤 |
| West | `#b3b3b3` | ⚪ |

| Segment | Color Hex | |
|---------|-----------|-|
| Consumer | `#8dd3c7` | 🟢 |
| Corporate | `#ffffb3` | 🟡 |
| Small Business | `#bebada` | 🟣 |

## Appendix C: Success Criteria Checklist

- [ ] `data_pipeline.py` runs without errors and produces `cleaned_data.csv` (200 rows, 19 columns) and `summary_stats.csv` (24 rows, 12 columns).
- [ ] `cleaned_data.csv` has no null values and no negative monetary values.
- [ ] `app.py` launches a Gradio 6 interface with 4 tabs, 4 dynamic filters, 4 KPI cards, and 10+ Plotly charts.
- [ ] All charts are interactive (hover, zoom, pan) with proper titles and axis labels.
- [ ] Dynamic filters correctly update all charts and KPI cards.
- [ ] `_validate.py` passes all assertion checks and prints "PASS".
- [ ] `executive_summary.md` is a complete, insightful business report with data tables and at least 3 actionable recommendations.
- [ ] All monetary values are rounded to 2 decimal places.
- [ ] All datetime values are properly parsed as pandas datetime.
- [ ] No missing values in any output file.