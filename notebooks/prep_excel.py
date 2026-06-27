import pandas as pd
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, 'data')

df = pd.read_csv(os.path.join(data_dir, 'credit_risk_clean.csv'))

# Summary 1 — Age group analysis
age_summary = df.groupby('age_group', observed=True).agg(
    total_applicants=('SeriousDlqin2yrs', 'count'),
    total_defaults=('SeriousDlqin2yrs', 'sum'),
    default_rate=('SeriousDlqin2yrs', 'mean'),
    avg_income=('MonthlyIncome', 'mean'),
    avg_utilization=('RevolvingUtilizationOfUnsecuredLines', 'mean')
).reset_index()
age_summary['default_rate'] = (age_summary['default_rate'] * 100).round(2)
age_summary['avg_income'] = age_summary['avg_income'].round(0)
age_summary['avg_utilization'] = (age_summary['avg_utilization'] * 100).round(2)

# Summary 2 — Risk segment analysis
risk_summary = df.groupby(['income_group', 'utilization_risk'], observed=True).agg(
    total_applicants=('SeriousDlqin2yrs', 'count'),
    total_defaults=('SeriousDlqin2yrs', 'sum'),
    default_rate=('SeriousDlqin2yrs', 'mean'),
    avg_income=('MonthlyIncome', 'mean')
).reset_index()
risk_summary['default_rate'] = (risk_summary['default_rate'] * 100).round(2)
risk_summary['avg_income'] = risk_summary['avg_income'].round(0)

# Save to Excel
out_path = os.path.join(base_dir, 'excel', 'credit_risk_analysis.xlsx')
with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
    age_summary.to_excel(writer, sheet_name='Age Group Analysis', index=False)
    risk_summary.to_excel(writer, sheet_name='Risk Segment Analysis', index=False)

print(f"✅ Excel file saved: {out_path}")
print("\nAge Group Summary:\n", age_summary)
print("\nRisk Segment Summary:\n", risk_summary.head(10))