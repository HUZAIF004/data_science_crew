#!/usr/bin/env python3
"""Get top products for the report."""
import pandas as pd

cleaned = pd.read_csv('cleaned_data.csv')

# Top 5 products by net revenue
prod_rev = cleaned.groupby('product_name')['net_revenue'].sum().sort_values(ascending=False).round(2)
print("=== TOP 5 PRODUCTS BY NET REVENUE ===")
for i, (name, rev) in enumerate(prod_rev.head(5).items(), 1):
    print(f"{i}. {name}: ${rev:,.2f}")

# Top 5 products by quantity sold
prod_qty = cleaned.groupby('product_name')['quantity'].sum().sort_values(ascending=False)
print("\n=== TOP 5 PRODUCTS BY UNITS SOLD ===")
for i, (name, qty) in enumerate(prod_qty.head(5).items(), 1):
    print(f"{i}. {name}: {qty} units")

# Bottom margins
print("\n=== CATEGORIES WITH NEGATIVE MARGIN ORDERS ===")
for cat in ['Apparel', 'Electronics', 'Furniture', 'Office Supplies']:
    cat_data = cleaned[cleaned['category'] == cat]
    neg_orders = (cat_data['net_profit'] < 0).sum()
    total_orders = len(cat_data)
    print(f"{cat}: {neg_orders}/{total_orders} orders with negative profit")

# Monthly growth
print("\n=== MONTH-OVER-MONTH NET REVENUE ===")
cleaned['month_label'] = cleaned['order_date'].str[:7]
monthly = cleaned.groupby('month_label')['net_revenue'].sum().round(2)
monthly = monthly.sort_index()
prev = None
for mon, rev in monthly.items():
    if prev is not None:
        change = ((rev - prev) / prev) * 100
        print(f"{mon}: ${rev:,.2f} (change from prev: {change:+.1f}%)")
    else:
        print(f"{mon}: ${rev:,.2f} (baseline)")
    prev = rev

# Average discount by category
print("\n=== AVG DISCOUNT BY CATEGORY ===")
for cat in sorted(cleaned['category'].unique()):
    avg_d = cleaned[cleaned['category'] == cat]['discount_pct'].mean() * 100
    print(f"{cat}: {avg_d:.1f}%")