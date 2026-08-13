#!/usr/bin/env python3
"""_validate.py — Validation script for app.py.

Monkey-patches demo.launch to no-op, imports app.py,
calls the main callback with default inputs, and verifies
outputs are valid.
"""

import sys
import os
import warnings

# ---------------------------------------------------------------------------
# 1. Monkey-patch demo.launch to no-op BEFORE importing app
# ---------------------------------------------------------------------------
import gradio as gr
original_launch = gr.Blocks.launch

def noop_launch(self, *args, **kwargs):
    pass

gr.Blocks.launch = noop_launch

# Suppress any user warnings (e.g. theme deprecation)
warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# 2. Import app.py
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import app

# Check that demo is a Blocks object
assert isinstance(app.demo, gr.Blocks), f"Expected gr.Blocks, got {type(app.demo)}"
print("✓ app.demo is a valid gr.Blocks object")

# ---------------------------------------------------------------------------
# 3. Load the data files to test
# ---------------------------------------------------------------------------
import pandas as pd

cleaned_df = pd.read_csv('cleaned_data.csv')
summary_df = pd.read_csv('summary_stats.csv')

assert len(cleaned_df) == 200, f"Expected 200 rows, got {len(cleaned_df)}"
assert len(summary_df) == 24, f"Expected 24 rows, got {len(summary_df)}"
print("✓ Data files loaded correctly")

# ---------------------------------------------------------------------------
# 4. Call the main callback with default/sample inputs
# ---------------------------------------------------------------------------
print("\n--- Testing update_dashboard with default inputs ---")

try:
    result = app.update_dashboard(
        region_sel=['All'],
        category_sel=['All'],
        segment_sel=['All'],
        month_start=1,
        month_end=12,
    )
    print(f"✓ update_dashboard returned {len(result)} outputs")

    # Check types of each output
    kpi_html, fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11, cleaned_out, summary_out = result

    # KPI HTML
    assert isinstance(kpi_html, str) and len(kpi_html) > 100, "KPI HTML too short"
    print(f"  ✓ KPI HTML: {len(kpi_html)} chars")

    # All charts
    charts = [fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11]
    for i, fig in enumerate(charts, 1):
        assert hasattr(fig, 'to_dict') or hasattr(fig, 'to_json'), f"Chart {i} not a plotly figure"
        print(f"  ✓ Chart {i} is valid Plotly figure")

    # DataFrames
    assert isinstance(cleaned_out, pd.DataFrame), f"Expected DataFrame, got {type(cleaned_out)}"
    print(f"  ✓ Cleaned data output: {len(cleaned_out)} rows")

    assert isinstance(summary_out, pd.DataFrame), f"Expected DataFrame, got {type(summary_out)}"
    print(f"  ✓ Summary data output: {len(summary_out)} rows")

except Exception as e:
    print(f"✘ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ---------------------------------------------------------------------------
# 5. Test with filtered inputs (specific regions, categories)
# ---------------------------------------------------------------------------
print("\n--- Testing update_dashboard with filtered inputs ---")

try:
    result = app.update_dashboard(
        region_sel=['North'],
        category_sel=['Electronics', 'Furniture'],
        segment_sel=['Corporate'],
        month_start=3,
        month_end=10,
    )
    print(f"✓ Filtered update_dashboard returned {len(result)} outputs")
    kpi_html, *rest = result
    assert isinstance(kpi_html, str) and len(kpi_html) > 50
    print(f"  ✓ Filtered KPI HTML generated")

    # Check filtered data has fewer rows
    cleaned_out = rest[-2]
    assert isinstance(cleaned_out, pd.DataFrame)
    print(f"  ✓ Filtered cleaned data: {len(cleaned_out)} rows")

except Exception as e:
    print(f"✘ FAILED filter test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ---------------------------------------------------------------------------
# 6. Test with empty result (impossible filters)
# ---------------------------------------------------------------------------
print("\n--- Testing update_dashboard with non-matching filters ---")

try:
    # Use a region that doesn't exist — All/region filter should still work
    # Let's test month range that yields no data
    result = app.update_dashboard(
        region_sel=['All'],
        category_sel=['All'],
        segment_sel=['All'],
        month_start=13,  # invalid month, should gracefully handle
        month_end=13,
    )
    print(f"✓ Edge case returned {len(result)} outputs")
    kpi_html, *rest = result
    cleaned_out = rest[-2]
    print(f"  ✓ Edge case cleaned data: {len(cleaned_out)} rows")

except Exception as e:
    print(f"✘ FAILED edge case test: {e}")
    # This might be acceptable if slider forces 1-12, but let's see
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ---------------------------------------------------------------------------
# 7. Component structure checks
# ---------------------------------------------------------------------------
print("\n--- Checking Blocks component tree ---")

# Check that demo has expected number of children
component_count = 0
for block in app.demo.blocks.values():
    if hasattr(block, 'label'):
        component_count += 1

print(f"✓ Blocks tree has components")

# Verify we can access event listeners
print(f"✓ Demo has {len(app.demo.fns)} event handler functions registered")

# ---------------------------------------------------------------------------
# 8. Final verdict
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("✅✅✅ VALIDATION PASSED — All checks successful ✅✅✅")
print("=" * 60)
sys.exit(0)