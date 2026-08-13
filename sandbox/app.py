#!/usr/bin/env python3
"""app.py — Premium Gradio 6 E-Commerce Dashboard (Dark Theme).

Reads cleaned_data.csv & summary_stats.csv and renders an enterprise-grade
BI dashboard with KPI cards, Plotly charts, filters, and data tables.
"""

import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
BASE = Path(__file__).parent

cleaned_df = pd.read_csv(BASE / 'cleaned_data.csv')
summary_df = pd.read_csv(BASE / 'summary_stats.csv')

# Ensure date parsing
cleaned_df['order_date'] = pd.to_datetime(cleaned_df['order_date'])

# Build unique filter options from data
regions = sorted(cleaned_df['region'].unique().tolist())
categories = sorted(cleaned_df['category'].unique().tolist())
segments = sorted(cleaned_df['customer_segment'].unique().tolist())
months = sorted(cleaned_df['month'].unique().tolist())
month_names = {
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
}

# Consistent colour palettes (from Appendix B)
CATEGORY_COLORS = {
    'Apparel': '#66c2a5',
    'Electronics': '#fc8d62',
    'Furniture': '#8da0cb',
    'Office Supplies': '#e78ac3',
}
REGION_COLORS = {
    'North': '#a6d854',
    'South': '#ffd92f',
    'East': '#e5c494',
    'West': '#b3b3b3',
}
SEGMENT_COLORS = {
    'Consumer': '#8dd3c7',
    'Corporate': '#ffffb3',
    'Small Business': '#bebada',
}

# ---------------------------------------------------------------------------
# 2. Custom CSS — full dark theme
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
/* Global dark background */
:root, body, .gradio-container, .main, .wrap {
    background-color: #0f0f1a !important;
    color: #e0e0e0 !important;
}
.gradio-container { max-width: 1400px !important; margin: 0 auto !important; padding: 16px !important; }

/* Tab navigation */
.tabs, .tab-nav {
    background: transparent !important;
    border: none !important;
}
.tab-nav button {
    background: #1e1e2f !important;
    color: #a0a0c0 !important;
    border: 1px solid #2a2a40 !important;
    border-radius: 8px 8px 0 0 !important;
    font-weight: 600 !important;
    padding: 10px 22px !important;
    margin-right: 4px !important;
    transition: all 0.2s ease !important;
}
.tab-nav button.selected {
    background: linear-gradient(135deg, #4a2c8a, #6c3fc9) !important;
    color: #ffffff !important;
    border-color: #6c3fc9 !important;
    box-shadow: 0 2px 12px rgba(108, 63, 201, 0.3) !important;
}
.tab-nav button:hover:not(.selected) {
    background: #2a2a40 !important;
    color: #c0c0e0 !important;
}

/* Tab content panels */
.tabs > .tabitem {
    background: #1a1a2e !important;
    border: 1px solid #2a2a40 !important;
    border-radius: 0 8px 8px 8px !important;
    padding: 20px !important;
}

/* Filter row container */
#filters-row {
    background: #1e1e2f !important;
    border: 1px solid #2a2a40 !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    margin-bottom: 20px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
}

/* Dropdowns / selectors inside filters */
select, input, textarea, .dropdown, .dropdown-items, .form, .input-wrap {
    background-color: #252540 !important;
    color: #e0e0f0 !important;
    border-color: #3a3a55 !important;
    border-radius: 8px !important;
}
select:focus, input:focus {
    border-color: #6c3fc9 !important;
    box-shadow: 0 0 0 2px rgba(108, 63, 201, 0.2) !important;
}

/* Slider styling */
.slider, input[type="range"] {
    accent-color: #6c3fc9 !important;
}
.slider-container label {
    color: #c0c0e0 !important;
    font-weight: 500 !important;
}

/* Labels */
label, .label-text {
    color: #c0c0e0 !important;
    font-weight: 500 !important;
}

/* DataFrames */
.dataframe-wrap, table, .table-wrap {
    background: #1e1e2f !important;
    color: #e0e0f0 !important;
    border-color: #2a2a40 !important;
}
.dataframe-wrap th {
    background: #2a2a45 !important;
    color: #c0c0f0 !important;
    font-weight: 600 !important;
}
.dataframe-wrap td {
    background: #1e1e2f !important;
    color: #d0d0e0 !important;
    border-color: #2a2a40 !important;
}

/* Buttons */
button, .btn, .download-btn {
    background: linear-gradient(135deg, #4a2c8a, #6c3fc9) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 8px 20px !important;
    transition: all 0.2s ease !important;
}
button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(108, 63, 201, 0.4) !important;
}

/* KPI cards container */
.kpi-row {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    margin-bottom: 24px;
}

/* Chart containers */
.plotly-wrap, .chart-container {
    background: transparent !important;
    border: none !important;
}
.js-plotly-plot, .plot-container {
    background: transparent !important;
}

/* Scrollbar dark */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #1a1a2e; }
::-webkit-scrollbar-thumb { background: #3a3a55; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #5a5a7a; }

/* Headings */
h1, h2, h3, h4, h5, h6 {
    color: #e8e8ff !important;
}
"""

# ---------------------------------------------------------------------------
# 3. Core filtering & aggregation logic
# ---------------------------------------------------------------------------
def filter_data(
    cleaned: pd.DataFrame,
    summary: pd.DataFrame,
    region_sel: list,
    category_sel: list,
    segment_sel: list,
    month_start: int,
    month_end: int,
):
    """Apply filters and return (filtered_cleaned, overall_kpis_dict)."""
    # Filter cleaned data
    mask = pd.Series(True, index=cleaned.index)
    if region_sel and 'All' not in region_sel:
        mask &= cleaned['region'].isin(region_sel)
    if category_sel and 'All' not in category_sel:
        mask &= cleaned['category'].isin(category_sel)
    if segment_sel and 'All' not in segment_sel:
        mask &= cleaned['customer_segment'].isin(segment_sel)
    mask &= cleaned['month'] >= month_start
    mask &= cleaned['month'] <= month_end

    f_cleaned = cleaned[mask].copy()

    if f_cleaned.empty:
        zero_overall = {
            'total_orders': 0, 'total_units_sold': 0,
            'total_gross_revenue': 0.0, 'total_discount_amount': 0.0,
            'total_net_revenue': 0.0, 'total_shipping_cost': 0.0,
            'total_net_profit': 0.0, 'avg_order_value': 0.0,
            'avg_profit_margin_pct': 0.0, 'avg_discount_pct': 0.0,
        }
        return f_cleaned, zero_overall

    # Recompute overall KPIs from filtered data
    total_orders = int(f_cleaned['order_id'].nunique())
    total_units_sold = int(f_cleaned['quantity'].sum())
    total_gross_revenue = round(float(f_cleaned['gross_revenue'].sum()), 2)
    total_discount_amount = round(float(f_cleaned['discount_amount'].sum()), 2)
    total_net_revenue = round(float(f_cleaned['net_revenue'].sum()), 2)
    total_shipping_cost = round(float(f_cleaned['shipping_cost'].sum()), 2)
    total_net_profit = round(float(f_cleaned['net_profit'].sum()), 2)
    avg_order_value = round(total_net_revenue / total_orders, 2) if total_orders > 0 else 0.0
    avg_profit_margin_pct = round(float(f_cleaned['profit_margin_pct'].mean()), 2)
    avg_discount_pct = round(float(f_cleaned['discount_pct'].mean()), 2)

    overall_kpis = {
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

    return f_cleaned, overall_kpis


def build_grouped_data(cleaned: pd.DataFrame, group_col: str, agg_col: str = 'net_revenue'):
    """Build grouped aggregation from filtered cleaned data."""
    if cleaned.empty:
        return pd.DataFrame(columns=[group_col, agg_col])
    grouped = cleaned.groupby(group_col, as_index=False).agg({
        'order_id': 'nunique',
        'quantity': 'sum',
        'gross_revenue': 'sum',
        'discount_amount': 'sum',
        'net_revenue': 'sum',
        'shipping_cost': 'sum',
        'net_profit': 'sum',
        'profit_margin_pct': 'mean',
        'discount_pct': 'mean',
    }).rename(columns={
        'order_id': 'total_orders',
        'quantity': 'total_units_sold',
        'gross_revenue': 'total_gross_revenue',
        'discount_amount': 'total_discount_amount',
        'net_revenue': 'total_net_revenue',
        'shipping_cost': 'total_shipping_cost',
        'net_profit': 'total_net_profit',
        'profit_margin_pct': 'avg_profit_margin_pct',
        'discount_pct': 'avg_discount_pct',
    })
    grouped['avg_order_value'] = round(
        grouped['total_net_revenue'] / grouped['total_orders'], 2
    )
    for c in ['total_gross_revenue', 'total_discount_amount', 'total_net_revenue',
              'total_shipping_cost', 'total_net_profit', 'avg_order_value',
              'avg_profit_margin_pct', 'avg_discount_pct']:
        grouped[c] = grouped[c].round(2)
    grouped['total_orders'] = grouped['total_orders'].astype(int)
    grouped['total_units_sold'] = grouped['total_units_sold'].astype(int)
    return grouped


# ---------------------------------------------------------------------------
# 4. Chart helpers
# ---------------------------------------------------------------------------
def _base_layout():
    """Return base layout kwargs for dark-themed Plotly chart."""
    return dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#c0c0e0', family='Inter, sans-serif'),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(font=dict(color='#c0c0e0'), bgcolor='rgba(0,0,0,0)'),
        hoverlabel=dict(bgcolor='#2a2a45', font_color='#ffffff'),
        xaxis=dict(gridcolor='#2a2a40', zerolinecolor='#3a3a55'),
        yaxis=dict(gridcolor='#2a2a40', zerolinecolor='#3a3a55'),
    )


def apply_chart_style(fig, title='', **layout_overrides):
    """Apply dark style + title to a plotly figure.
    
    Uses update_xaxes/update_yaxes to avoid xaxis/yaxis key conflicts.
    """
    base = _base_layout()
    if title:
        base['title'] = dict(text=title, font=dict(size=18, color='#e8e8ff', family='Inter, sans-serif'))
    
    # Apply non-axis layout items directly
    axis_keys = {'xaxis', 'yaxis'}
    layout_kwargs = {k: v for k, v in base.items() if k not in axis_keys}
    layout_kwargs.update({k: v for k, v in layout_overrides.items() if k not in axis_keys})
    
    fig.update_layout(**layout_kwargs)
    
    # Apply axis styling via update_xaxes/update_yaxes to avoid key conflicts
    if 'xaxis' in base:
        fig.update_xaxes(**base['xaxis'])
    if 'yaxis' in base:
        fig.update_yaxes(**base['yaxis'])
    
    return fig


def make_kpi_card(title: str, value: str, accent_color: str, prefix: str = '') -> str:
    """Render a single KPI card as styled HTML."""
    return f"""
    <div style="
        background: linear-gradient(135deg, #1e1e2f 0%, #252540 100%);
        border-radius: 14px;
        padding: 20px 24px;
        flex: 1;
        min-width: 180px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4);
        border-top: 4px solid {accent_color};
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    "
    onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 8px 32px rgba(0,0,0,0.5)';"
    onmouseout="this.style.transform=''; this.style.boxShadow='';"
    >
        <div style="font-size: 13px; font-weight: 500; color: #8888aa; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">
            {title}
        </div>
        <div style="font-size: 28px; font-weight: 700; color: #ffffff; line-height: 1.2;">
            {prefix}{value}
        </div>
    </div>
    """


def empty_figure(message='No data for current filter selection'):
    """Return a minimal empty figure."""
    fig = go.Figure()
    apply_chart_style(fig, message)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


# ---------------------------------------------------------------------------
# 5. Dashboard update callback
# ---------------------------------------------------------------------------
def update_dashboard(
    region_sel, category_sel, segment_sel, month_start, month_end
):
    """Main callback: apply filters, recompute KPIs and all charts."""
    # Ensure lists
    if isinstance(region_sel, str):
        region_sel = [region_sel]
    if isinstance(category_sel, str):
        category_sel = [category_sel]
    if isinstance(segment_sel, str):
        segment_sel = [segment_sel]

    f_cleaned, overall = filter_data(
        cleaned_df, summary_df, region_sel, category_sel, segment_sel,
        month_start, month_end
    )

    # ---- KPI Cards ----
    kpi_net_rev = f"${overall['total_net_revenue']:,.2f}"
    kpi_orders = f"{overall['total_orders']:,}"
    kpi_aov = f"${overall['avg_order_value']:,.2f}"
    kpi_margin = f"{overall['avg_profit_margin_pct']:.1f}%"

    kpi_html = f"""
    <div class="kpi-row">
        {make_kpi_card('Net Revenue', kpi_net_rev, '#636EFA')}
        {make_kpi_card('Total Orders', kpi_orders, '#00CC96')}
        {make_kpi_card('Avg Order Value', kpi_aov, '#AB63FA')}
        {make_kpi_card('Profit Margin', kpi_margin, '#EF553B')}
    </div>
    """

    # Handle empty data
    if f_cleaned.empty:
        empty_fig = empty_figure()
        return (
            kpi_html,
            empty_fig, empty_fig, empty_fig, empty_fig,
            empty_fig, empty_fig, empty_fig, empty_fig,
            empty_fig, empty_fig, empty_fig,
            f_cleaned, summary_df.copy(),
        )

    # ===========================
    # TAB 1: Executive Overview
    # ===========================

    # 1. Monthly Net Revenue Trend
    monthly = build_grouped_data(f_cleaned, 'month_name')
    monthly['month_num'] = monthly['month_name'].map({v: k for k, v in month_names.items()})
    monthly = monthly.sort_values('month_num')
    fig1 = px.line(
        monthly, x='month_name', y='total_net_revenue',
        markers=True, template='plotly_dark',
        title='Monthly Net Revenue Trend (2024)',
        labels={'month_name': 'Month', 'total_net_revenue': 'Net Revenue ($)'},
        color_discrete_sequence=['#636EFA'],
    )
    fig1.update_traces(line=dict(width=3), marker=dict(size=8))
    apply_chart_style(fig1)

    # 2. Revenue by Category (Pie)
    cat_data = build_grouped_data(f_cleaned, 'category')
    fig2 = px.pie(
        cat_data, values='total_net_revenue', names='category',
        template='plotly_dark',
        title='Revenue Distribution by Category',
        color='category',
        color_discrete_map=CATEGORY_COLORS,
    )
    fig2.update_traces(textposition='inside', textinfo='percent+label', hole=0.3)
    apply_chart_style(fig2)

    # 3. Orders by Customer Segment (Bar)
    seg_data = build_grouped_data(f_cleaned, 'customer_segment')
    fig3 = px.bar(
        seg_data, x='customer_segment', y='total_orders',
        color='customer_segment',
        template='plotly_dark',
        title='Orders by Customer Segment',
        labels={'customer_segment': 'Segment', 'total_orders': 'Total Orders'},
        color_discrete_map=SEGMENT_COLORS,
    )
    apply_chart_style(fig3)
    fig3.update_layout(showlegend=False)
    fig3.update_traces(texttemplate='%{y}', textposition='outside')

    # 4. AOV by Customer Segment (Bar)
    fig4 = px.bar(
        seg_data, x='customer_segment', y='avg_order_value',
        color='customer_segment',
        template='plotly_dark',
        title='AOV by Customer Segment',
        labels={'customer_segment': 'Segment', 'avg_order_value': 'Avg Order Value ($)'},
        color_discrete_map=SEGMENT_COLORS,
    )
    apply_chart_style(fig4)
    fig4.update_layout(showlegend=False)
    fig4.update_traces(texttemplate='$%{y:,.2f}', textposition='outside')

    # ===========================
    # TAB 2: Regional Analytics
    # ===========================
    reg_data = build_grouped_data(f_cleaned, 'region')

    # 5. Net Revenue by Region
    fig5 = px.bar(
        reg_data, x='region', y='total_net_revenue',
        color='region',
        template='plotly_dark',
        title='Net Revenue by Region',
        labels={'region': 'Region', 'total_net_revenue': 'Net Revenue ($)'},
        color_discrete_map=REGION_COLORS,
    )
    apply_chart_style(fig5)
    fig5.update_layout(showlegend=False)
    fig5.update_traces(texttemplate='$%{y:,.2f}', textposition='outside')

    # 6. Regional Revenue Share (Donut)
    fig6 = px.pie(
        reg_data, values='total_net_revenue', names='region',
        hole=0.4, template='plotly_dark',
        title='Regional Revenue Share',
        color='region',
        color_discrete_map=REGION_COLORS,
    )
    fig6.update_traces(textposition='inside', textinfo='percent+label')
    apply_chart_style(fig6)

    # 7. AOV by Region
    fig7 = px.bar(
        reg_data, x='region', y='avg_order_value',
        color='region',
        template='plotly_dark',
        title='AOV by Region',
        labels={'region': 'Region', 'avg_order_value': 'Avg Order Value ($)'},
        color_discrete_map=REGION_COLORS,
    )
    apply_chart_style(fig7)
    fig7.update_layout(showlegend=False)
    fig7.update_traces(texttemplate='$%{y:,.2f}', textposition='outside')

    # 8. Region × Category Heatmap
    heat_data = f_cleaned.groupby(['region', 'category'], as_index=False)['net_revenue'].sum()
    pivot = heat_data.pivot_table(
        index='region', columns='category', values='net_revenue',
        aggfunc='sum', fill_value=0
    )
    for c in categories:
        if c not in pivot.columns:
            pivot[c] = 0
    pivot = pivot[categories]
    fig8 = px.imshow(
        pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        text_auto='.0f',
        aspect='auto',
        template='plotly_dark',
        title='Revenue Heatmap: Region × Category ($)',
        color_continuous_scale='Viridis',
        labels={'x': 'Category', 'y': 'Region', 'color': 'Revenue ($)'},
    )
    apply_chart_style(fig8)
    fig8.update_traces(hovertemplate='Region: %{y}<br>Category: %{x}<br>Revenue: $%{z:,.2f}<extra></extra>')

    # ===========================
    # TAB 3: Product Performance
    # ===========================

    # 9. Top Products by Revenue (Horizontal)
    prod_rev = f_cleaned.groupby('product_name', as_index=False)['net_revenue'].sum()
    prod_rev = prod_rev.sort_values('net_revenue', ascending=False).head(10)
    fig9 = px.bar(
        prod_rev, y='product_name', x='net_revenue',
        orientation='h', template='plotly_dark',
        title='Top Products by Net Revenue',
        labels={'product_name': '', 'net_revenue': 'Net Revenue ($)'},
        color='net_revenue',
        color_continuous_scale='Viridis',
    )
    apply_chart_style(fig9)
    fig9.update_yaxes(autorange='reversed')
    fig9.update_traces(texttemplate='$%{x:,.2f}', textposition='outside')

    # 10. Revenue by Product Category (Stacked)
    prod_cat = f_cleaned.groupby(['category', 'product_name'], as_index=False)['net_revenue'].sum()
    fig10 = px.bar(
        prod_cat, x='category', y='net_revenue', color='product_name',
        template='plotly_dark',
        title='Product Breakdown by Category',
        labels={'category': 'Category', 'net_revenue': 'Net Revenue ($)', 'product_name': 'Product'},
        barmode='stack',
    )
    apply_chart_style(fig10)

    # 11. Units Sold by Product
    prod_qty = f_cleaned.groupby('product_name', as_index=False)['quantity'].sum()
    prod_qty = prod_qty.sort_values('quantity', ascending=False)
    fig11 = px.bar(
        prod_qty, x='product_name', y='quantity',
        template='plotly_dark',
        title='Total Units Sold per Product',
        labels={'product_name': 'Product', 'quantity': 'Units Sold'},
        color='quantity',
        color_continuous_scale='Tealgrn',
    )
    apply_chart_style(fig11)

    # Return results
    f_summary = summary_df.copy()

    return (
        kpi_html,
        fig1, fig2, fig3, fig4,
        fig5, fig6, fig7, fig8,
        fig9, fig10, fig11,
        f_cleaned, f_summary,
    )


# ---------------------------------------------------------------------------
# 6. Build Gradio UI
# ---------------------------------------------------------------------------
def build_app():
    with gr.Blocks(title='E-Commerce Executive Dashboard', elem_id='app-container') as demo:
        # Header
        gr.HTML("""
        <div style="
            background: linear-gradient(135deg, #2d1b69, #4a2c8a, #6c3fc9);
            border-radius: 16px;
            padding: 28px 32px;
            margin-bottom: 24px;
            box-shadow: 0 8px 32px rgba(108, 63, 201, 0.25);
        ">
            <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
                <div style="flex: 1;">
                    <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #ffffff; letter-spacing: 0.5px;">
                        📊 E-Commerce Sales Dashboard
                    </h1>
                    <p style="margin: 6px 0 0 0; font-size: 14px; color: #c8b8f0; font-weight: 400;">
                        Executive Analytics · 2024 Performance Overview
                    </p>
                </div>
                <div style="text-align: right;">
                    <span style="background: rgba(255,255,255,0.15); padding: 6px 16px; border-radius: 20px; font-size: 13px; color: #d0c0f0;">
                        🟢 LIVE
                    </span>
                </div>
            </div>
        </div>
        """)

        # ---- Global Filters ----
        with gr.Row(elem_id='filters-row'):
            with gr.Column(scale=1):
                region_filter = gr.Dropdown(
                    choices=['All'] + regions,
                    value=['All'],
                    multiselect=True,
                    label='Region',
                    elem_classes='filter-select',
                )
            with gr.Column(scale=1):
                category_filter = gr.Dropdown(
                    choices=['All'] + categories,
                    value=['All'],
                    multiselect=True,
                    label='Category',
                    elem_classes='filter-select',
                )
            with gr.Column(scale=1):
                segment_filter = gr.Dropdown(
                    choices=['All'] + segments,
                    value=['All'],
                    multiselect=True,
                    label='Customer Segment',
                    elem_classes='filter-select',
                )
            with gr.Column(scale=1):
                month_start = gr.Slider(
                    minimum=1, maximum=12, value=1, step=1,
                    label='Start Month',
                )
            with gr.Column(scale=1):
                month_end = gr.Slider(
                    minimum=1, maximum=12, value=12, step=1,
                    label='End Month',
                )

        # ---- KPI Cards ----
        kpi_cards = gr.HTML(label='Key Metrics')

        # ---- Tabs ----
        with gr.Tabs():
            # Tab 1: Executive Overview
            with gr.Tab('📈 Executive Overview'):
                with gr.Row():
                    with gr.Column(scale=6):
                        chart1 = gr.Plot(label='Monthly Net Revenue Trend')
                    with gr.Column(scale=6):
                        chart2 = gr.Plot(label='Revenue by Category')
                with gr.Row():
                    with gr.Column(scale=6):
                        chart3 = gr.Plot(label='Orders by Segment')
                    with gr.Column(scale=6):
                        chart4 = gr.Plot(label='AOV by Segment')

            # Tab 2: Regional Analytics
            with gr.Tab('🌍 Regional Analytics'):
                with gr.Row():
                    with gr.Column(scale=6):
                        chart5 = gr.Plot(label='Net Revenue by Region')
                    with gr.Column(scale=6):
                        chart6 = gr.Plot(label='Regional Revenue Share')
                with gr.Row():
                    with gr.Column(scale=6):
                        chart7 = gr.Plot(label='AOV by Region')
                    with gr.Column(scale=6):
                        chart8 = gr.Plot(label='Region × Category Heatmap')

            # Tab 3: Product Performance
            with gr.Tab('🏷️ Product Performance'):
                with gr.Row():
                    with gr.Column(scale=6):
                        chart9 = gr.Plot(label='Top Products by Revenue')
                    with gr.Column(scale=6):
                        chart10 = gr.Plot(label='Product Breakdown by Category')
                with gr.Row():
                    with gr.Column(scale=12):
                        chart11 = gr.Plot(label='Units Sold by Product')

            # Tab 4: Summary Data
            with gr.Tab('📋 Summary Data'):
                gr.Markdown("### Cleaned Data")
                cleaned_table = gr.DataFrame(label='Cleaned Data', interactive=True)
                gr.DownloadButton(
                    value=BASE / 'cleaned_data.csv',
                    label='📥 Download Cleaned Data',
                )
                gr.Markdown("### Summary Statistics")
                summary_table = gr.DataFrame(label='Summary Statistics', interactive=True)
                gr.DownloadButton(
                    value=BASE / 'summary_stats.csv',
                    label='📥 Download Summary Stats',
                )

        # ---- Wire up inputs to outputs ----
        all_charts = [chart1, chart2, chart3, chart4, chart5, chart6, chart7, chart8, chart9, chart10, chart11]
        all_outputs = [kpi_cards] + all_charts + [cleaned_table, summary_table]
        filter_inputs = [region_filter, category_filter, segment_filter, month_start, month_end]

        demo.load(
            fn=update_dashboard,
            inputs=filter_inputs,
            outputs=all_outputs,
        )

        for inp in filter_inputs:
            inp.change(
                fn=update_dashboard,
                inputs=filter_inputs,
                outputs=all_outputs,
            )

    return demo


# ---------------------------------------------------------------------------
# 7. Main entry point
# ---------------------------------------------------------------------------
demo = build_app()

if __name__ == '__main__':
    demo.launch(
        theme=gr.themes.Soft(
            primary_hue=gr.themes.colors.violet,
            secondary_hue=gr.themes.colors.indigo,
            neutral_hue=gr.themes.colors.gray,
            text_size=gr.themes.sizes.text_lg,
        ),
        css=CUSTOM_CSS,
        debug=False,
    )