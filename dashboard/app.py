import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# ── Page config ────────────────────────────────────────
st.set_page_config(
    page_title="Financial Risk Analytics",
    page_icon="💳",
    layout="wide"
)

# ── Load data ──────────────────────────────────────────
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, 'data', 'credit_risk_clean.csv')
    df = pd.read_csv(path)
    return df

df = load_data()

NAVY  = '#1B2A4A'
GOLD  = '#F5A623'
RED   = '#E74C3C'
GREEN = '#2ECC71'
BLUE  = '#3498DB'

# ── Sidebar filters ────────────────────────────────────
st.sidebar.title("🔍 Filters")
age_options = sorted(df['age_group'].dropna().unique().tolist())
selected_age = st.sidebar.multiselect(
    "Age Group", options=age_options, default=age_options
)
income_options = df['income_group'].dropna().unique().tolist()
selected_income = st.sidebar.multiselect(
    "Income Group", options=income_options, default=income_options
)

filtered = df[
    (df['age_group'].isin(selected_age)) &
    (df['income_group'].isin(selected_income))
]

# ── Title ──────────────────────────────────────────────
st.title("💳 Financial Risk & Loan Portfolio Analysis")
st.caption("Give Me Some Credit Dataset | 120,665 loan applicants | Kaggle")
st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Portfolio Overview",
    "⚠️ Credit Risk Analysis",
    "💰 Income & Demographics",
    "🔴 High Risk Profiles"
])

# ══════════════════════════════════════════════════════
# TAB 1 — PORTFOLIO OVERVIEW
# ══════════════════════════════════════════════════════
with tab1:
    total = len(filtered)
    defaults = filtered['SeriousDlqin2yrs'].sum()
    default_rate = defaults/total*100 if total > 0 else 0
    avg_income = filtered['MonthlyIncome'].mean()
    avg_util = filtered['RevolvingUtilizationOfUnsecuredLines'].mean()*100

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Applicants", f"{total:,}")
    col2.metric("Total Defaults", f"{int(defaults):,}")
    col3.metric("Default Rate", f"{default_rate:.2f}%")
    col4.metric("Avg Monthly Income", f"${avg_income:,.0f}")
    col5.metric("Avg Credit Utilization", f"{avg_util:.1f}%")

    st.divider()
    col_l, col_r = st.columns(2)

    with col_l:
        age_data = filtered.groupby('age_group', observed=True).agg(
            default_rate=('SeriousDlqin2yrs', 'mean'),
            count=('SeriousDlqin2yrs', 'count')
        ).reset_index()
        age_data['default_rate'] = age_data['default_rate'] * 100

        bar_colors = [RED if r > 9 else GOLD if r > 6 else GREEN
                      for r in age_data['default_rate']]
        fig1 = go.Figure(go.Bar(
            x=age_data['age_group'],
            y=age_data['default_rate'],
            marker_color=bar_colors,
            text=[f"{v:.1f}%" for v in age_data['default_rate']],
            textposition='outside'
        ))
        fig1.update_layout(
            title='Default Rate by Age Group',
            yaxis=dict(ticksuffix='%', gridcolor='#f0f0f0'),
            plot_bgcolor='white', height=380
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col_r:
        default_dist = filtered['default_label'].value_counts().reset_index()
        default_dist.columns = ['label', 'count']
        fig2 = px.pie(default_dist, values='count', names='label',
                      hole=0.45, title='Default vs Non-Default Distribution',
                      color_discrete_map={'Default': RED, 'No Default': GREEN})
        fig2.update_layout(height=380)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("💡 Key Insights")
    i1, i2, i3 = st.columns(3)
    i1.error("**Highest Risk Age:** 18-30 group defaults at 11.22% — 3.6x higher than 60+ borrowers")
    i2.warning("**Utilization Signal:** 90%+ utilization → 22.28% default rate (9x portfolio average)")
    i3.error("**Delinquency Flag:** 1 prior 90-day late payment → 33.58% default probability")

# ══════════════════════════════════════════════════════
# TAB 2 — CREDIT RISK ANALYSIS
# ══════════════════════════════════════════════════════
with tab2:
    col1, col2, col3 = st.columns(3)
    col1.metric("Default Rate", f"{default_rate:.2f}%")
    col2.metric("Avg Utilization", f"{avg_util:.1f}%")
    col3.metric("Avg Age", f"{filtered['age'].mean():.1f}")

    col_l, col_r = st.columns(2)

    with col_l:
        util_data = filtered.groupby('utilization_risk', observed=True).agg(
            default_rate=('SeriousDlqin2yrs', 'mean')
        ).reset_index()
        util_data['default_rate'] = util_data['default_rate'] * 100
        util_order = ['Low (0-30%)', 'Medium (30-60%)', 'High (60-90%)', 'Very High (90%+)']
        util_data = util_data[util_data['utilization_risk'].isin(util_order)]
        util_data['utilization_risk'] = pd.Categorical(
            util_data['utilization_risk'], categories=util_order, ordered=True
        )
        util_data = util_data.sort_values('utilization_risk')

        fig3 = go.Figure(go.Bar(
            x=util_data['utilization_risk'],
            y=util_data['default_rate'],
            marker_color=[GREEN, GOLD, '#E67E22', RED],
            text=[f"{v:.1f}%" for v in util_data['default_rate']],
            textposition='outside'
        ))
        fig3.add_hline(y=6.87, line_dash='dash', line_color=NAVY,
                       annotation_text="Portfolio avg: 6.87%")
        fig3.update_layout(
            title='Default Rate by Credit Utilization',
            yaxis=dict(ticksuffix='%', gridcolor='#f0f0f0', range=[0, 28]),
            plot_bgcolor='white', height=380
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col_r:
        delinq_data = filtered.groupby('past_delinquency', observed=True).agg(
            default_rate=('SeriousDlqin2yrs', 'mean')
        ).reset_index()
        delinq_data['default_rate'] = delinq_data['default_rate'] * 100
        delinq_order = ['No History', '1 Time', '2+ Times']
        delinq_data['past_delinquency'] = pd.Categorical(
            delinq_data['past_delinquency'], categories=delinq_order, ordered=True
        )
        delinq_data = delinq_data.sort_values('past_delinquency')

        fig4 = go.Figure(go.Bar(
            x=delinq_data['past_delinquency'],
            y=delinq_data['default_rate'],
            marker_color=[GREEN, RED, RED],
            text=[f"{v:.1f}%" for v in delinq_data['default_rate']],
            textposition='outside'
        ))
        fig4.add_hline(y=6.87, line_dash='dash', line_color=NAVY,
                       annotation_text="Portfolio avg: 6.87%")
        fig4.update_layout(
            title='Past Delinquency Impact on Default Rate',
            yaxis=dict(ticksuffix='%', gridcolor='#f0f0f0', range=[0, 65]),
            plot_bgcolor='white', height=380
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.error("**Critical Finding:** Even ONE prior 90-day late payment increases default probability from 4.85% to 33.58% — a 7x increase. This is the single strongest risk signal in the portfolio.")

# ══════════════════════════════════════════════════════
# TAB 3 — INCOME & DEMOGRAPHICS
# ══════════════════════════════════════════════════════
with tab3:
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Monthly Income", f"${avg_income:,.0f}")
    col2.metric("Total Applicants", f"{total:,}")
    col3.metric("Default Rate", f"{default_rate:.2f}%")

    col_l, col_r = st.columns(2)

    with col_l:
        income_order = ['Low (<$3K)', 'Mid ($3K-$6K)',
                        'High ($6K-$10K)', 'Very High ($10K+)']
        income_data = filtered.groupby('income_group', observed=True).agg(
            default_rate=('SeriousDlqin2yrs', 'mean'),
            avg_income=('MonthlyIncome', 'mean')
        ).reset_index()
        income_data['default_rate'] = income_data['default_rate'] * 100
        income_data['income_group'] = pd.Categorical(
            income_data['income_group'], categories=income_order, ordered=True
        )
        income_data = income_data.sort_values('income_group')

        fig5 = go.Figure(go.Bar(
            y=income_data['income_group'],
            x=income_data['default_rate'],
            orientation='h',
            marker_color=[RED, GOLD, BLUE, GREEN],
            text=[f"{v:.1f}%" for v in income_data['default_rate']],
            textposition='outside'
        ))
        fig5.update_layout(
            title='Default Rate by Income Bracket',
            xaxis=dict(ticksuffix='%', gridcolor='#f0f0f0'),
            plot_bgcolor='white', height=380
        )
        st.plotly_chart(fig5, use_container_width=True)

    with col_r:
        age_income = filtered.groupby('age_group', observed=True).agg(
            avg_income=('MonthlyIncome', 'mean')
        ).reset_index()

        fig6 = go.Figure(go.Bar(
            x=age_income['age_group'],
            y=age_income['avg_income'],
            marker_color=NAVY,
            text=[f"${v:,.0f}" for v in age_income['avg_income']],
            textposition='outside'
        ))
        fig6.update_layout(
            title='Avg Monthly Income by Age Group',
            yaxis=dict(tickprefix='$', gridcolor='#f0f0f0'),
            plot_bgcolor='white', height=380
        )
        st.plotly_chart(fig6, use_container_width=True)

    st.subheader("📋 Risk Segment Summary Table")
    summary = filtered.groupby(
        ['age_group', 'income_group'], observed=True
    ).agg(
        total_applicants=('SeriousDlqin2yrs', 'count'),
        total_defaults=('SeriousDlqin2yrs', 'sum'),
        default_rate=('SeriousDlqin2yrs', 'mean')
    ).reset_index()
    summary['default_rate'] = (summary['default_rate'] * 100).round(2)
    summary = summary.sort_values('default_rate', ascending=False)
    st.dataframe(summary, use_container_width=True, height=300)

# ══════════════════════════════════════════════════════
# TAB 4 — HIGH RISK PROFILES
# ══════════════════════════════════════════════════════
with tab4:
    col1, col2 = st.columns(2)
    col1.metric("Total Defaults", f"{int(defaults):,}")
    col2.metric("Overall Default Rate", f"{default_rate:.2f}%")

    st.error("""
    🔴 **Highest Risk Profile Identified**
    Age: 18-30 | Income: Low (<$3K) | Utilization: Very High (90%+)
    → Default Rate: **12.55%** | Avg Utilization: **52.64%**
    → Action: Flag for enhanced credit review before approval
    """)

    col_l, col_r = st.columns(2)

    with col_l:
        high_util = filtered[
            filtered['utilization_risk'] == 'Very High (90%+)'
        ]
        age_defaults = high_util.groupby('age_group', observed=True).agg(
            total_defaults=('SeriousDlqin2yrs', 'sum')
        ).reset_index()

        fig7 = go.Figure(go.Bar(
            x=age_defaults['age_group'],
            y=age_defaults['total_defaults'],
            marker_color=RED,
            text=age_defaults['total_defaults'],
            textposition='outside'
        ))
        fig7.update_layout(
            title='Defaults by Age (Very High Utilization Only)',
            yaxis=dict(gridcolor='#f0f0f0'),
            plot_bgcolor='white', height=380
        )
        st.plotly_chart(fig7, use_container_width=True)

    with col_r:
        delinq_defaults = filtered.groupby(
            'past_delinquency', observed=True
        ).agg(
            total_defaults=('SeriousDlqin2yrs', 'sum')
        ).reset_index()

        delinq_order = ['No History', '1 Time', '2+ Times']
        delinq_defaults['past_delinquency'] = pd.Categorical(
            delinq_defaults['past_delinquency'],
            categories=delinq_order, ordered=True
        )
        delinq_defaults = delinq_defaults.sort_values('past_delinquency')

        fig8 = go.Figure(go.Bar(
            x=delinq_defaults['past_delinquency'],
            y=delinq_defaults['total_defaults'],
            marker_color=[GREEN, RED, RED],
            text=delinq_defaults['total_defaults'],
            textposition='outside'
        ))
        fig8.update_layout(
            title='Total Defaults by Delinquency History',
            yaxis=dict(gridcolor='#f0f0f0'),
            plot_bgcolor='white', height=380
        )
        st.plotly_chart(fig8, use_container_width=True)

    st.subheader("🔎 Raw Data Explorer — High Risk Segment")
    high_risk = filtered[
        (filtered['utilization_risk'] == 'Very High (90%+)') &
        (filtered['SeriousDlqin2yrs'] == 1)
    ][['age', 'age_group', 'income_group', 'MonthlyIncome',
       'DebtRatio', 'RevolvingUtilizationOfUnsecuredLines',
       'past_delinquency', 'SeriousDlqin2yrs']].head(100)
    st.dataframe(high_risk, use_container_width=True, height=300)