#!/usr/bin/env python3
"""Quick check: which columns have negative values?"""
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')
df['gross_revenue'] = df['quantity'] * df['unit_price']
df['discount_amount'] = df['quantity'] * df['unit_price'] * df['discount_pct']
df['net_revenue'] = df['gross_revenue'] - df['discount_amount']
df['net_profit'] = df['net_revenue'] - df['shipping_cost']

print("Min net_revenue:", df['net_revenue'].min())
print("Min quantity:", df['quantity'].min())
print("Min unit_price:", df['unit_price'].min())
print("Min net_profit:", df['net_profit'].min())
print("Min shipping_cost:", df['shipping_cost'].min())

neg_profit = df[df['net_profit'] < 0]
print(f"\nRows with negative net_profit: {len(neg_profit)}")
if len(neg_profit) > 0:
    print(neg_profit[['order_id', 'net_revenue', 'shipping_cost', 'net_profit']].head(10))