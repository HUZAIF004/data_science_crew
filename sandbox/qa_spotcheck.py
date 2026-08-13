#!/usr/bin/env python3
"""QA Spot-check: Verify calculations in cleaned_data.csv against raw data."""
import pandas as pd

# Load raw and cleaned data
raw = pd.read_csv('data.csv')
cleaned = pd.read_csv('cleaned_data.csv')
summary = pd.read_csv('summary_stats.csv')

# 1) Spot-check 5 random rows by index (pick indices 0, 25, 50, 75, 100 from cleaned)
# Let's use the first 5 rows from the sorted cleaned data (which correspond to raw rows)
# Actually let's pick 5 specific order_ids

spot_check_ids = ['ORD-1045', 'ORD-1130', 'ORD-1055', 'ORD-1067', 'ORD-1186']

print("=== SPOT CHECK: Row-level Calculations ===")
print()

for oid in spot_check_ids:
    raw_row = raw[raw['order_id'] == oid].iloc[0]
    cleaned_row = cleaned[cleaned['order_id'] == oid].iloc[0]
    
    qty = raw_row['quantity']
    price = raw_row['unit_price']
    disc = raw_row['discount_pct']
    ship = raw_row['shipping_cost']
    
    # Hand calculation
    gross = round(qty * price, 2)
    disc_amt = round(qty * price * disc, 2)
    net_rev = round(gross - disc_amt, 2)
    net_prof = round(net_rev - ship, 2)
    margin = round((net_prof / net_rev) * 100, 2) if net_rev > 0 else 0.0
    
    # Compare
    print(f"Order: {oid}")
    print(f"  Qty={qty}, Price=${price}, Discount={disc*100}%, Shipping=${ship}")
    print(f"  Expected Gross Rev: ${gross}, Got: ${cleaned_row['gross_revenue']}")
    print(f"  Expected Disc Amt:  ${disc_amt}, Got: ${cleaned_row['discount_amount']}")
    print(f"  Expected Net Rev:   ${net_rev}, Got: ${cleaned_row['net_revenue']}")
    print(f"  Expected Net Profit: ${net_prof}, Got: ${cleaned_row['net_profit']}")
    print(f"  Expected Margin:    {margin}%, Got: {cleaned_row['profit_margin_pct']}%")
    
    errors = []
    if abs(gross - cleaned_row['gross_revenue']) > 0.02:
        errors.append(f"Gross revenue mismatch")
    if abs(disc_amt - cleaned_row['discount_amount']) > 0.02:
        errors.append(f"Discount amount mismatch")
    if abs(net_rev - cleaned_row['net_revenue']) > 0.02:
        errors.append(f"Net revenue mismatch")
    if abs(net_prof - cleaned_row['net_profit']) > 0.02:
        errors.append(f"Net profit mismatch")
    if abs(margin - cleaned_row['profit_margin_pct']) > 0.02:
        errors.append(f"Profit margin mismatch")
    
    if errors:
        print(f"  ❌ ERRORS: {', '.join(errors)}")
    else:
        print(f"  ✅ PASS")
    print()

# 2) Cross-check overall KPIs
print("=== OVERALL KPI CROSS-CHECK ===")
print()

overall = summary[summary['group_level'] == 'overall'].iloc[0]

# Recompute from cleaned data
total_orders = cleaned['order_id'].nunique()
total_units = cleaned['quantity'].sum()
total_gross = round(cleaned['gross_revenue'].sum(), 2)
total_disc = round(cleaned['discount_amount'].sum(), 2)
total_net_rev = round(cleaned['net_revenue'].sum(), 2)
total_ship = round(cleaned['shipping_cost'].sum(), 2)
total_profit = round(cleaned['net_profit'].sum(), 2)
aov = round(total_net_rev / total_orders, 2)
avg_margin = round(cleaned['profit_margin_pct'].mean(), 2)
avg_disc = round(cleaned['discount_pct'].mean(), 2)

checks = [
    ("Total Orders", total_orders, overall['total_orders']),
    ("Total Units Sold", total_units, overall['total_units_sold']),
    ("Total Gross Revenue", total_gross, overall['total_gross_revenue']),
    ("Total Discount Amount", total_disc, overall['total_discount_amount']),
    ("Total Net Revenue", total_net_rev, overall['total_net_revenue']),
    ("Total Shipping Cost", total_ship, overall['total_shipping_cost']),
    ("Total Net Profit", total_profit, overall['total_net_profit']),
    ("Avg Order Value", aov, overall['avg_order_value']),
    ("Avg Profit Margin %", avg_margin, overall['avg_profit_margin_pct']),
    ("Avg Discount %", avg_disc, overall['avg_discount_pct']),
]

all_pass = True
for name, expected, stored in checks:
    if isinstance(expected, float):
        match = abs(expected - stored) < 0.02
    else:
        match = expected == stored
    status = "✅" if match else "❌"
    if not match:
        all_pass = False
    print(f"  {status} {name}: Expected={expected}, Stored={stored}")

print()
if all_pass:
    print("✅ ALL OVERALL KPI CHECKS PASSED")
else:
    print("❌ SOME CHECKS FAILED")

# 3) Cross-check category sums against overall
print()
print("=== CATEGORY REVENUE CROSS-CHECK ===")
cat_net = cleaned.groupby('category')['net_revenue'].sum().round(2)
cat_stored = summary[summary['group_level']=='category'][['group_name', 'total_net_revenue']].set_index('group_name')['total_net_revenue']
for cat in sorted(cat_net.index):
    exp = cat_net[cat]
    stored = cat_stored[cat]
    match = abs(exp - stored) < 0.02
    print(f"  {'✅' if match else '❌'} {cat}: Expected={exp}, Stored={stored}")

cat_sum = round(cat_net.sum(), 2)
print(f"  Category sum: ${cat_sum} vs Overall Net Revenue: ${overall['total_net_revenue']}")
print(f"  Match: {'✅' if abs(cat_sum - overall['total_net_revenue']) < 0.02 else '❌'}")

# 4) Cross-check region sums
print()
print("=== REGION REVENUE CROSS-CHECK ===")
reg_net = cleaned.groupby('region')['net_revenue'].sum().round(2)
reg_stored = summary[summary['group_level']=='region'][['group_name', 'total_net_revenue']].set_index('group_name')['total_net_revenue']
for reg in sorted(reg_net.index):
    exp = reg_net[reg]
    stored = reg_stored[reg]
    match = abs(exp - stored) < 0.02
    print(f"  {'✅' if match else '❌'} {reg}: Expected={exp}, Stored={stored}")

reg_sum = round(reg_net.sum(), 2)
print(f"  Region sum: ${reg_sum} vs Overall Net Revenue: ${overall['total_net_revenue']}")
print(f"  Match: {'✅' if abs(reg_sum - overall['total_net_revenue']) < 0.02 else '❌'}")

# 5) Cross-check segment sums
print()
print("=== SEGMENT REVENUE CROSS-CHECK ===")
seg_net = cleaned.groupby('customer_segment')['net_revenue'].sum().round(2)
seg_stored = summary[summary['group_level']=='segment'][['group_name', 'total_net_revenue']].set_index('group_name')['total_net_revenue']
for seg in sorted(seg_net.index):
    exp = seg_net[seg]
    stored = seg_stored[seg]
    match = abs(exp - stored) < 0.02
    print(f"  {'✅' if match else '❌'} {seg}: Expected={exp}, Stored={stored}")

seg_sum = round(seg_net.sum(), 2)
print(f"  Segment sum: ${seg_sum} vs Overall Net Revenue: ${overall['total_net_revenue']}")
print(f"  Match: {'✅' if abs(seg_sum - overall['total_net_revenue']) < 0.02 else '❌'}")

# 6) Cross-check monthly sums
print()
print("=== MONTHLY REVENUE CROSS-CHECK ===")
cleaned['month_label'] = cleaned['order_date'].str[:7]
mon_net = cleaned.groupby('month_label')['net_revenue'].sum().round(2)
mon_stored = summary[summary['group_level']=='month'][['group_name', 'total_net_revenue']].set_index('group_name')['total_net_revenue']
for mon in sorted(mon_net.index):
    exp = mon_net[mon]
    stored = mon_stored[mon]
    match = abs(exp - stored) < 0.02
    print(f"  {'✅' if match else '❌'} {mon}: Expected={exp}, Stored={stored}")

mon_sum = round(mon_net.sum(), 2)
print(f"  Monthly sum: ${mon_sum} vs Overall Net Revenue: ${overall['total_net_revenue']}")
print(f"  Match: {'✅' if abs(mon_sum - overall['total_net_revenue']) < 0.02 else '❌'}")

print()
print("=== QA SPOT-CHECK COMPLETE ===")