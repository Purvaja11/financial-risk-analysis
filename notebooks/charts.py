import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# ── Setup ──────────────────────────────────────────────
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
conn = sqlite3.connect(os.path.join(base_dir, 'data', 'credit_risk.db'))
os.makedirs(os.path.join(base_dir, 'charts'), exist_ok=True)
charts_dir = os.path.join(base_dir, 'charts')

NAVY   = '#1B2A4A'
GOLD   = '#F5A623'
RED    = '#E74C3C'
GREEN  = '#2ECC71'
BLUE   = '#3498DB'
GRAY   = '#95A5A6'

# ══════════════════════════════════════════════════════
# CHART 1 — Portfolio Overview KPIs
# ══════════════════════════════════════════════════════
df1 = pd.read_sql_query("""
    SELECT
        COUNT(*) as total,
        SUM(SeriousDlqin2yrs) as defaults,
        ROUND(AVG(SeriousDlqin2yrs)*100, 2) as default_rate,
        ROUND(AVG(age), 1) as avg_age,
        ROUND(AVG(MonthlyIncome), 0) as avg_income,
        ROUND(AVG(RevolvingUtilizationOfUnsecuredLines)*100, 2) as avg_util
    FROM loans
""", conn)

fig1 = make_subplots(
    rows=1, cols=3,
    specs=[[{"type":"indicator"}, {"type":"indicator"}, {"type":"indicator"}]]
)
fig1.add_trace(go.Indicator(
    mode="gauge+number",
    value=df1['default_rate'].iloc[0],
    title={'text': "Default Rate", 'font': {'size': 13}},
    number={'suffix': '%', 'font': {'size': 24, 'color': RED}},
    gauge={
        'axis': {'range': [0, 30]},
        'bar': {'color': RED},
        'steps': [{'range': [0, 5], 'color': '#EBF5FB'},
                  {'range': [5, 10], 'color': '#FADBD8'},
                  {'range': [10, 30], 'color': '#F1948A'}]
    }
), row=1, col=1)
fig1.add_trace(go.Indicator(
    mode="number",
    value=df1['avg_income'].iloc[0],
    title={'text': "Avg Monthly Income", 'font': {'size': 14}},
    number={'prefix': '$', 'font': {'size': 36, 'color': NAVY}},
), row=1, col=2)
fig1.add_trace(go.Indicator(
    mode="number",
    value=df1['avg_util'].iloc[0],
    title={'text': "Avg Credit Utilization", 'font': {'size': 14}},
    number={'suffix': '%', 'font': {'size': 36, 'color': GOLD}},
), row=1, col=3)
fig1.update_layout(
    title=dict(
        text='<b>Loan Portfolio Overview</b><br>'
             '<sup>120,665 applicants | 6.87% default rate | $6,753 avg income</sup>',
        font=dict(size=16)
    ),
    plot_bgcolor='white', paper_bgcolor='white',
    height=380, margin=dict(t=100)
)
fig1.write_image(os.path.join(charts_dir, 'chart1_portfolio_overview.png'), scale=2)
fig1.show()
print("✅ Chart 1 saved")
# ══════════════════════════════════════════════════════
# CHART 2 — Default Rate by Age Group
# ══════════════════════════════════════════════════════
df2 = pd.read_sql_query("""
    SELECT
        CASE
            WHEN age BETWEEN 18 AND 30 THEN '18-30'
            WHEN age BETWEEN 31 AND 40 THEN '31-40'
            WHEN age BETWEEN 41 AND 50 THEN '41-50'
            WHEN age BETWEEN 51 AND 60 THEN '51-60'
            ELSE '60+'
        END as age_group,
        COUNT(*) as applicants,
        ROUND(AVG(SeriousDlqin2yrs)*100, 2) as default_rate,
        ROUND(AVG(MonthlyIncome), 0) as avg_income
    FROM loans
    GROUP BY age_group
    ORDER BY age_group
""", conn)

bar_colors = [RED if r > 9 else GOLD if r > 6 else GREEN
              for r in df2['default_rate']]

fig2 = make_subplots(specs=[[{"secondary_y": True}]])
fig2.add_trace(go.Bar(
    x=df2['age_group'], y=df2['default_rate'],
    name='Default Rate %', marker_color=bar_colors,
    text=[f"{v:.1f}%" for v in df2['default_rate']],
    textposition='outside'
), secondary_y=False)
fig2.add_trace(go.Scatter(
    x=df2['age_group'], y=df2['avg_income'],
    name='Avg Income ($)', mode='lines+markers',
    marker=dict(size=10, color=NAVY),
    line=dict(width=3, color=NAVY)
), secondary_y=True)
fig2.update_layout(
    title=dict(text='<b>Default Rate by Age Group</b><br>'
               '<sup>18-30 group has 11.22% default rate — 3.6x higher than 60+ borrowers</sup>',
               font=dict(size=16)),
    plot_bgcolor='white', paper_bgcolor='white', height=420,
    legend=dict(orientation='h', y=1.1),
    xaxis=dict(title='Age Group', gridcolor='#f0f0f0')
)
fig2.update_yaxes(title_text='Default Rate (%)', ticksuffix='%',
                  gridcolor='#f0f0f0', secondary_y=False)
fig2.update_yaxes(title_text='Avg Monthly Income ($)', tickprefix='$',
                  secondary_y=True)
fig2.write_image(os.path.join(charts_dir, 'chart2_default_by_age.png'), scale=2)
fig2.show()
print("✅ Chart 2 saved")

# ══════════════════════════════════════════════════════
# CHART 3 — Credit Utilization vs Default Rate
# ══════════════════════════════════════════════════════
df3 = pd.read_sql_query("""
    SELECT
        CASE
            WHEN RevolvingUtilizationOfUnsecuredLines <= 0.30 THEN '1. Low (0-30%)'
            WHEN RevolvingUtilizationOfUnsecuredLines <= 0.60 THEN '2. Medium (30-60%)'
            WHEN RevolvingUtilizationOfUnsecuredLines <= 0.90 THEN '3. High (60-90%)'
            ELSE '4. Very High (90%+)'
        END as util_bracket,
        COUNT(*) as applicants,
        ROUND(AVG(SeriousDlqin2yrs)*100, 2) as default_rate
    FROM loans
    GROUP BY util_bracket
    ORDER BY util_bracket
""", conn)

fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=df3['util_bracket'], y=df3['default_rate'],
    marker_color=[GREEN, GOLD, '#E67E22', RED],
    text=[f"{v:.1f}%" for v in df3['default_rate']],
    textposition='outside',
    textfont=dict(size=13, color='black')
))
fig3.add_hline(y=6.87, line_dash='dash', line_color=NAVY,
               annotation_text="Portfolio avg: 6.87%",
               annotation_position="top right")
fig3.update_layout(
    title=dict(text='<b>Credit Utilization vs Default Rate</b><br>'
               '<sup>Very High utilization (90%+) borrowers default at 22.28% — 9x higher than Low utilization</sup>',
               font=dict(size=16)),
    xaxis_title='Credit Utilization Bracket',
    yaxis=dict(title='Default Rate (%)', ticksuffix='%',
               gridcolor='#f0f0f0', range=[0, 28]),
    plot_bgcolor='white', paper_bgcolor='white', height=420
)
fig3.write_image(os.path.join(charts_dir, 'chart3_utilization_default.png'), scale=2)
fig3.show()
print("✅ Chart 3 saved")

# ══════════════════════════════════════════════════════
# CHART 4 — Past Delinquency Impact
# ══════════════════════════════════════════════════════
df4 = pd.read_sql_query("""
    SELECT
        NumberOfTimes90DaysLate as times_late,
        COUNT(*) as applicants,
        ROUND(AVG(SeriousDlqin2yrs)*100, 2) as default_rate
    FROM loans
    WHERE NumberOfTimes90DaysLate <= 5
    GROUP BY times_late
    ORDER BY times_late
""", conn)

fig4 = go.Figure()
fig4.add_trace(go.Bar(
    x=df4['times_late'].astype(str),
    y=df4['default_rate'],
    marker_color=[GREEN, RED, RED, RED, RED, RED],
    text=[f"{v:.1f}%" for v in df4['default_rate']],
    textposition='outside'
))
fig4.add_hline(y=6.87, line_dash='dash', line_color=NAVY,
               annotation_text="Portfolio avg: 6.87%")
fig4.update_layout(
    title=dict(text='<b>Past Delinquency Impact on Default Rate</b><br>'
               '<sup>1 prior 90-day late payment → 33.58% default rate. '
               'Zero history → only 4.85%</sup>',
               font=dict(size=16)),
    xaxis_title='Number of Times 90+ Days Late (Past)',
    yaxis=dict(title='Default Rate (%)', ticksuffix='%',
               gridcolor='#f0f0f0', range=[0, 80]),
    plot_bgcolor='white', paper_bgcolor='white', height=420
)
fig4.write_image(os.path.join(charts_dir, 'chart4_delinquency_impact.png'), scale=2)
fig4.show()
print("✅ Chart 4 saved")

# ══════════════════════════════════════════════════════
# CHART 5 — Income & Debt Ratio Risk Matrix
# ══════════════════════════════════════════════════════
df5 = pd.read_sql_query("""
    SELECT
        CASE
            WHEN MonthlyIncome <= 3000 THEN '1. Low (<$3K)'
            WHEN MonthlyIncome <= 6000 THEN '2. Mid ($3K-$6K)'
            WHEN MonthlyIncome <= 10000 THEN '3. High ($6K-$10K)'
            ELSE '4. Very High ($10K+)'
        END as income_bracket,
        CASE
            WHEN DebtRatio <= 0.30 THEN 'Low Debt'
            WHEN DebtRatio <= 0.60 THEN 'Medium Debt'
            ELSE 'High Debt'
        END as debt_bracket,
        COUNT(*) as applicants,
        ROUND(AVG(SeriousDlqin2yrs)*100, 2) as default_rate
    FROM loans
    GROUP BY income_bracket, debt_bracket
    HAVING COUNT(*) > 200
    ORDER BY income_bracket, debt_bracket
""", conn)

fig5 = px.bar(df5, x='income_bracket', y='default_rate',
              color='debt_bracket', barmode='group',
              color_discrete_map={
                  'Low Debt': GREEN,
                  'Medium Debt': GOLD,
                  'High Debt': RED
              },
              title='<b>Income vs Debt Ratio Risk Matrix</b><br>'
                    '<sup>Low income + High debt = highest combined risk profile</sup>',
              labels={'income_bracket': 'Income Bracket',
                      'default_rate': 'Default Rate (%)',
                      'debt_bracket': 'Debt Level'},
              text_auto='.1f',
              height=420)
fig5.update_traces(textposition='outside')
fig5.update_layout(
    plot_bgcolor='white', paper_bgcolor='white',
    height=480,
    yaxis=dict(ticksuffix='%', gridcolor='#f0f0f0'),
    legend_title='Debt Level',
    xaxis=dict(tickangle=-20)
)
fig5.write_image(os.path.join(charts_dir, 'chart5_income_debt_matrix.png'), scale=2)
fig5.show()
print("✅ Chart 5 saved")

# ══════════════════════════════════════════════════════
# CHART 6 — High Risk Borrower Heatmap
# ══════════════════════════════════════════════════════
df6 = pd.read_sql_query("""
    SELECT
        CASE
            WHEN age BETWEEN 18 AND 30 THEN '18-30'
            WHEN age BETWEEN 31 AND 40 THEN '31-40'
            WHEN age BETWEEN 41 AND 50 THEN '41-50'
            WHEN age BETWEEN 51 AND 60 THEN '51-60'
            ELSE '60+'
        END as age_group,
        CASE
            WHEN MonthlyIncome <= 3000 THEN 'Low (<$3K)'
            WHEN MonthlyIncome <= 6000 THEN 'Mid ($3K-$6K)'
            WHEN MonthlyIncome <= 10000 THEN 'High ($6K-$10K)'
            ELSE 'Very High ($10K+)'
        END as income_group,
        ROUND(AVG(SeriousDlqin2yrs)*100, 2) as default_rate,
        COUNT(*) as applicants
    FROM loans
    GROUP BY age_group, income_group
    HAVING COUNT(*) > 300
    ORDER BY age_group, income_group
""", conn)

pivot = df6.pivot(index='age_group', columns='income_group', values='default_rate')
pivot = pivot.reindex(['18-30','31-40','41-50','51-60','60+'])

fig6 = px.imshow(pivot,
    color_continuous_scale=['#EBF5FB', '#AED6F1', GOLD, RED],
    title='<b>Default Rate Heatmap — Age vs Income Segment</b><br>'
          '<sup>Darkest cells = highest default risk | Young + Low Income = most dangerous profile</sup>',
    labels=dict(x='Income Group', y='Age Group', color='Default Rate (%)'),
    text_auto='.1f',
    height=420
)
fig6.update_layout(
    plot_bgcolor='white', paper_bgcolor='white'
)
fig6.write_image(os.path.join(charts_dir, 'chart6_risk_heatmap.png'), scale=2)
fig6.show()
print("✅ Chart 6 saved")

conn.close()
print("\n✅ All 6 charts saved to /charts folder")