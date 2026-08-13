#!/usr/bin/env python3
"""data_pipeline.py - ETL pipeline for e-commerce sales data.

Reads data.csv, cleans/transforms it, and outputs:
  - cleaned_data.csv (200 rows, 19 columns)
  - summary_stats.csv  (24 rows, 12 columns)
"""

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# 1. Load & Parse
# ---------------------------------------------------------------------------
df = pd.read_csv('data.csv')

# R1: Parse order_date
df['order_date'] = pd.to_datetime(df['order_date'])

# ---------------------------------------------------------------------------
# 2. Clean & Compute derived columns
# ---------------------------------------------------------------------------
# R2: Gross Revenue
df['gross_revenue'] = df['quantity'] * df['unit_price']

# R3: Discount Amount
df['discount_amount'] = df['quantity'] * df['unit_price'] * df['discount_pct']

# R4: Net Revenue
df['net_revenue'] = df['gross_revenue'] - df['discount_amount']

# R5: Net Profit (contribution margin)
df['net_profit'] = df['net_revenue'] - df['shipping_cost']

# R6: Profit Margin %
# Avoid division by zero (net_revenue should always be > 0 per data quality)
df['profit_margin_pct'] = np.where(
    df['net_revenue'] > 0,
    (df['net_profit'] / df['net_revenue']) * 100,
    0.0
)

# R7: Extract Month/Year
df['year'] = df['order_date'].dt.year
df['month'] = df['order_date'].dt.month
df['month_name'] = df['order_date'].dt.strftime('%b')

# ---------------------------------------------------------------------------
# 3. Reorder columns to match the exact specification in Section 4.2
# ---------------------------------------------------------------------------
cleaned_columns = [
    'order_id',
    'order_date',
    'year',
    'month',
    'month_name',
    'customer_segment',
    'region',
    'category',
    'product_name',
    'quantity',
    'unit_price',
    'discount_pct',
    'shipping_cost',
    'payment_method',
    'gross_revenue',
    'discount_amount',
    'net_revenue',
    'net_profit',
    'profit_margin_pct',
]

cleaned_df = df[cleaned_columns].copy()

# R10: Sort by order_date then order_id
cleaned_df = cleaned_df.sort_values(['order_date', 'order_id']).reset_index(drop=True)

# R11: Round floats to 2 decimal places
float_cols = cleaned_df.select_dtypes(include=['float64']).columns
cleaned_df[float_cols] = cleaned_df[float_cols].round(2)

# ---------------------------------------------------------------------------
# 4. Validation assertions
# - Design says R9 ensures quantities and prices are positive
# - net_profit can be legitimately negative when shipping_cost > net_revenue
# ---------------------------------------------------------------------------
assert len(cleaned_df) == 200, f"Row count mismatch: {len(cleaned_df)}"
assert cleaned_df.isnull().sum().sum() == 0, "Null values found"
assert (cleaned_df['quantity'] > 0).all(), "Non-positive quantity found"
assert (cleaned_df['unit_price'] > 0).all(), "Non-positive unit_price found"
assert (cleaned_df['net_revenue'] >= 0).all(), "Negative net_revenue found"
# Note: net_profit can be legitimately negative when shipping_cost > net_revenue
# This is a valid business scenario, not a data quality issue

# ---------------------------------------------------------------------------
# 5. Output cleaned_data.csv
# ---------------------------------------------------------------------------
cleaned_df.to_csv('cleaned_data.csv', index=False)
print(f"✓ cleaned_data.csv written ({len(cleaned_df)} rows, {len(cleaned_df.columns)} columns)")

# ---------------------------------------------------------------------------
# 6. Compute summary_stats.csv
# ---------------------------------------------------------------------------

def build_summary(grp_df, group_level, group_name):
    """Build a single summary row from a grouped DataFrame."""
    total_orders = int(grp_df['order_id'].nunique())
    total_units_sold = int(grp_df['quantity'].sum())
    total_gross_revenue = round(float(grp_df['gross_revenue'].sum()), 2)
    total_discount_amount = round(float(grp_df['discount_amount'].sum()), 2)
    total_net_revenue = round(float(grp_df['net_revenue'].sum()), 2)
    total_shipping_cost = round(float(grp_df['shipping_cost'].sum()), 2)
    total_net_profit = round(float(grp_df['net_profit'].sum()), 2)
    avg_order_value = round(total_net_revenue / total_orders, 2) if total_orders > 0 else 0.0
    avg_profit_margin_pct = round(float(grp_df['profit_margin_pct'].mean()), 2)
    avg_discount_pct = round(float(grp_df['discount_pct'].mean()), 2)

    return {
        'group_level': group_level,
        'group_name': group_name,
        'total_orders': total_orders,
        'total_units_sold': total_units_sold,
        'total_gross_revenue': total_gross_revenue,
        'total_discount_amount': total_discount_amount,
        'total_net_revenue': total_net_revenue,
        'total_shipping_cost': total_shipping_cost,
        'total_net_profit': total_net_profit,
        'avg_order_value': avg_order_value,
        'avg_profit_margin_pct': avg_profit_margin_pct,
        'avg_discount_pct': avg_discount_pct,
    }

summary_rows = []

# 6a. Overall
summary_rows.append(build_summary(cleaned_df, 'overall', 'All'))

# 6b. Category
for cat in sorted(cleaned_df['category'].unique()):
    grp = cleaned_df[cleaned_df['category'] == cat]
    summary_rows.append(build_summary(grp, 'category', cat))

# 6c. Region
for region in sorted(cleaned_df['region'].unique()):
    grp = cleaned_df[cleaned_df['region'] == region]
    summary_rows.append(build_summary(grp, 'region', region))

# 6d. Segment
for seg in sorted(cleaned_df['customer_segment'].unique()):
    grp = cleaned_df[cleaned_df['customer_segment'] == seg]
    summary_rows.append(build_summary(grp, 'segment', seg))

# 6e. Month (format as YYYY-MM)
cleaned_df['year_month'] = cleaned_df['order_date'].dt.strftime('%Y-%m')
for ym in sorted(cleaned_df['year_month'].unique()):
    grp = cleaned_df[cleaned_df['year_month'] == ym]
    summary_rows.append(build_summary(grp, 'month', ym))

summary_df = pd.DataFrame(summary_rows)

# Sort: group_level alphabetically, then group_name alphabetically
summary_df = summary_df.sort_values(['group_level', 'group_name']).reset_index(drop=True)

# Ensure integer types for count columns
summary_df['total_orders'] = summary_df['total_orders'].astype(int)
summary_df['total_units_sold'] = summary_df['total_units_sold'].astype(int)

# Round all float columns
float_summary_cols = summary_df.select_dtypes(include=['float64']).columns
summary_df[float_summary_cols] = summary_df[float_summary_cols].round(2)

# Validation
assert len(summary_df) == 24, f"Expected 24 summary rows, got {len(summary_df)}"

# ---------------------------------------------------------------------------
# 7. Output summary_stats.csv
# ---------------------------------------------------------------------------
summary_df.to_csv('summary_stats.csv', index=False)
print(f"✓ summary_stats.csv written ({len(summary_df)} rows, {len(summary_df.columns)} columns)")

# ---------------------------------------------------------------------------
# 8. Print summary for verification
# ---------------------------------------------------------------------------
print("\n=== Overall KPIs ===")
overall = summary_df[summary_df['group_level'] == 'overall'].iloc[0]
print(f"Total Orders:        {overall['total_orders']}")
print(f"Total Units Sold:    {overall['total_units_sold']}")
print(f"Total Gross Revenue: ${overall['total_gross_revenue']:,.2f}")
print(f"Total Net Revenue:   ${overall['total_net_revenue']:,.2f}")
print(f"Total Shipping Cost: ${overall['total_shipping_cost']:,.2f}")
print(f"Total Net Profit:    ${overall['total_net_profit']:,.2f}")
print(f"Avg Order Value:     ${overall['avg_order_value']:,.2f}")
print(f"Avg Profit Margin:   {overall['avg_profit_margin_pct']:.2f}%")
print(f"Avg Discount:        {overall['avg_discount_pct']*100:.2f}%")

print("\n✓ Pipeline completed successfully!")