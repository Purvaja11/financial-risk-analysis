import pandas as pd
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, 'data')

# ── Load raw data ──────────────────────────────────────
df = pd.read_csv(os.path.join(data_dir, 'cs-training.csv'))
print("Raw shape:", df.shape)
print("Missing values:\n", df.isnull().sum())

# ── Clean ──────────────────────────────────────────────
df['MonthlyIncome'] = df['MonthlyIncome'].fillna(df['MonthlyIncome'].median())
df['NumberOfDependents'] = df['NumberOfDependents'].fillna(0)

# ── Remove outliers ────────────────────────────────────
df = df[df['age'] >= 18]
df = df[df['age'] <= 100]
df = df[df['RevolvingUtilizationOfUnsecuredLines'] <= 1.5]
df = df[df['DebtRatio'] <= 10]

# ── Add risk segments ──────────────────────────────────
df['age_group'] = pd.cut(df['age'],
    bins=[18, 30, 40, 50, 60, 100],
    labels=['18-30', '31-40', '41-50', '51-60', '60+'])

df['income_group'] = pd.cut(df['MonthlyIncome'],
    bins=[0, 3000, 6000, 10000, float('inf')],
    labels=['Low (<$3K)', 'Mid ($3K-$6K)', 'High ($6K-$10K)', 'Very High ($10K+)'])

df['utilization_risk'] = pd.cut(
    df['RevolvingUtilizationOfUnsecuredLines'],
    bins=[-0.01, 0.30, 0.60, 0.90, 1.5],
    labels=['Low (0-30%)', 'Medium (30-60%)', 'High (60-90%)', 'Very High (90%+)'])

df['debt_risk'] = pd.cut(df['DebtRatio'],
    bins=[-0.01, 0.30, 0.60, 1.0, 10],
    labels=['Low (<30%)', 'Medium (30-60%)', 'High (60-100%)', 'Very High (100%+)'])

df['past_delinquency'] = df['NumberOfTimes90DaysLate'].apply(
    lambda x: 'No History' if x == 0 else ('1 Time' if x == 1 else '2+ Times')
)

df['default_label'] = df['SeriousDlqin2yrs'].map({0: 'No Default', 1: 'Default'})

# ── Drop unnamed column ────────────────────────────────
df = df.drop(columns=['Unnamed: 0'], errors='ignore')

# ── Save clean file ────────────────────────────────────
out_path = os.path.join(data_dir, 'credit_risk_clean.csv')
df.to_csv(out_path, index=False)
print(f"\n✅ Clean file saved: {len(df):,} rows")
print("Columns:", df.columns.tolist())
print("\nDefault rate:", df['SeriousDlqin2yrs'].mean()*100, "%")
print("\nAge group distribution:\n", df['age_group'].value_counts())
print("\nMissing values after cleaning:\n", df.isnull().sum())