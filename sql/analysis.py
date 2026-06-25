import sqlite3
import pandas as pd
import numpy as np
import os

# ── Setup ──────────────────────────────────────────────
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, 'data')
db_path  = os.path.join(data_dir, 'credit_risk.db')

# ── Load data ──────────────────────────────────────────
df = pd.read_csv(os.path.join(data_dir, 'cs-training.csv'))
print("Shape:", df.shape)
print("\nColumns:", df.columns.tolist())
print("\nSample:\n", df.head(3))
print("\nDefault rate:", df['SeriousDlqin2yrs'].mean()*100, "%")
print("\nMissing values:\n", df.isnull().sum())

# ── Clean data ─────────────────────────────────────────
# Fill missing values
df['MonthlyIncome'] = df['MonthlyIncome'].fillna(df['MonthlyIncome'].median())
df['NumberOfDependents'] = df['NumberOfDependents'].fillna(0)

# Remove outliers
df = df[df['age'] >= 18]
df = df[df['age'] <= 100]
df = df[df['RevolvingUtilizationOfUnsecuredLines'] <= 1.5]
df = df[df['DebtRatio'] <= 10]

print("\nShape after cleaning:", df.shape)

# ── Create SQLite DB ───────────────────────────────────
conn = sqlite3.connect(db_path)
df.to_sql('loans', conn, if_exists='replace', index=False)
print("\n✅ Database created —", len(df), "loan records loaded")

# ── Create risk segments ───────────────────────────────
df['age_group'] = pd.cut(df['age'],
    bins=[18, 30, 40, 50, 60, 100],
    labels=['18-30', '31-40', '41-50', '51-60', '60+'])

df['income_group'] = pd.cut(df['MonthlyIncome'],
    bins=[0, 3000, 6000, 10000, float('inf')],
    labels=['Low (<3K)', 'Mid (3K-6K)', 'High (6K-10K)', 'Very High (10K+)'])

df['utilization_risk'] = pd.cut(df['RevolvingUtilizationOfUnsecuredLines'],
    bins=[-0.01, 0.3, 0.6, 0.9, 1.5],
    labels=['Low (0-30%)', 'Medium (30-60%)', 'High (60-90%)', 'Very High (90%+)'])

df.to_sql('loans_segmented', conn, if_exists='replace', index=False)

# ── Q1: Overall default rate and portfolio overview ────
print("\n📊 Q1 — Portfolio Overview:")
q1 = pd.read_sql_query("""
    SELECT
        COUNT(*) as total_applicants,
        SUM(SeriousDlqin2yrs) as total_defaults,
        ROUND(AVG(SeriousDlqin2yrs)*100, 2) as default_rate_pct,
        ROUND(AVG(age), 1) as avg_age,
        ROUND(AVG(MonthlyIncome), 0) as avg_monthly_income,
        ROUND(AVG(DebtRatio)*100, 2) as avg_debt_ratio_pct,
        ROUND(AVG(RevolvingUtilizationOfUnsecuredLines)*100, 2) as avg_utilization_pct
    FROM loans
""", conn)
print(q1.to_string(index=False))

# ── Q2: Default rate by age group ─────────────────────
print("\n📊 Q2 — Default Rate by Age Group:")
q2 = pd.read_sql_query("""
    SELECT
        CASE
            WHEN age BETWEEN 18 AND 30 THEN '18-30'
            WHEN age BETWEEN 31 AND 40 THEN '31-40'
            WHEN age BETWEEN 41 AND 50 THEN '41-50'
            WHEN age BETWEEN 51 AND 60 THEN '51-60'
            ELSE '60+'
        END as age_group,
        COUNT(*) as applicants,
        SUM(SeriousDlqin2yrs) as defaults,
        ROUND(AVG(SeriousDlqin2yrs)*100, 2) as default_rate_pct,
        ROUND(AVG(MonthlyIncome), 0) as avg_income
    FROM loans
    GROUP BY age_group
    ORDER BY age_group
""", conn)
print(q2.to_string(index=False))

# ── Q3: Default rate by utilization bracket ───────────
print("\n📊 Q3 — Default Rate by Credit Utilization:")
q3 = pd.read_sql_query("""
    SELECT
        CASE
            WHEN RevolvingUtilizationOfUnsecuredLines <= 0.30 THEN '1. Low (0-30%)'
            WHEN RevolvingUtilizationOfUnsecuredLines <= 0.60 THEN '2. Medium (30-60%)'
            WHEN RevolvingUtilizationOfUnsecuredLines <= 0.90 THEN '3. High (60-90%)'
            ELSE '4. Very High (90%+)'
        END as utilization_bracket,
        COUNT(*) as applicants,
        SUM(SeriousDlqin2yrs) as defaults,
        ROUND(AVG(SeriousDlqin2yrs)*100, 2) as default_rate_pct
    FROM loans
    GROUP BY utilization_bracket
    ORDER BY utilization_bracket
""", conn)
print(q3.to_string(index=False))

# ── Q4: Default rate by income bracket ────────────────
print("\n📊 Q4 — Default Rate by Monthly Income:")
q4 = pd.read_sql_query("""
    SELECT
        CASE
            WHEN MonthlyIncome <= 3000 THEN '1. Low (<$3K)'
            WHEN MonthlyIncome <= 6000 THEN '2. Mid ($3K-$6K)'
            WHEN MonthlyIncome <= 10000 THEN '3. High ($6K-$10K)'
            ELSE '4. Very High ($10K+)'
        END as income_bracket,
        COUNT(*) as applicants,
        SUM(SeriousDlqin2yrs) as defaults,
        ROUND(AVG(SeriousDlqin2yrs)*100, 2) as default_rate_pct,
        ROUND(AVG(MonthlyIncome), 0) as avg_income
    FROM loans
    GROUP BY income_bracket
    ORDER BY income_bracket
""", conn)
print(q4.to_string(index=False))

# ── Q5: Past delinquency impact ───────────────────────
print("\n📊 Q5 — Past Delinquency Impact on Default:")
q5 = pd.read_sql_query("""
    SELECT
        NumberOfTimes90DaysLate as times_90days_late,
        COUNT(*) as applicants,
        ROUND(AVG(SeriousDlqin2yrs)*100, 2) as default_rate_pct,
        ROUND(AVG(MonthlyIncome), 0) as avg_income
    FROM loans
    WHERE NumberOfTimes90DaysLate <= 5
    GROUP BY NumberOfTimes90DaysLate
    ORDER BY NumberOfTimes90DaysLate
""", conn)
print(q5.to_string(index=False))

# ── Q6: Debt ratio impact ─────────────────────────────
print("\n📊 Q6 — Debt Ratio Brackets vs Default Rate:")
q6 = pd.read_sql_query("""
    SELECT
        CASE
            WHEN DebtRatio <= 0.30 THEN '1. Low (0-30%)'
            WHEN DebtRatio <= 0.60 THEN '2. Medium (30-60%)'
            WHEN DebtRatio <= 1.00 THEN '3. High (60-100%)'
            ELSE '4. Very High (100%+)'
        END as debt_bracket,
        COUNT(*) as applicants,
        SUM(SeriousDlqin2yrs) as defaults,
        ROUND(AVG(SeriousDlqin2yrs)*100, 2) as default_rate_pct,
        ROUND(AVG(DebtRatio)*100, 2) as avg_debt_ratio_pct
    FROM loans
    GROUP BY debt_bracket
    ORDER BY debt_bracket
""", conn)
print(q6.to_string(index=False))

# ── Q7: Open credit lines impact ──────────────────────
print("\n📊 Q7 — Number of Open Credit Lines vs Default:")
q7 = pd.read_sql_query("""
    SELECT
        CASE
            WHEN NumberOfOpenCreditLinesAndLoans <= 3 THEN '1. Few (0-3)'
            WHEN NumberOfOpenCreditLinesAndLoans <= 7 THEN '2. Moderate (4-7)'
            WHEN NumberOfOpenCreditLinesAndLoans <= 12 THEN '3. Many (8-12)'
            ELSE '4. Very Many (13+)'
        END as credit_lines_bracket,
        COUNT(*) as applicants,
        ROUND(AVG(SeriousDlqin2yrs)*100, 2) as default_rate_pct
    FROM loans
    GROUP BY credit_lines_bracket
    ORDER BY credit_lines_bracket
""", conn)
print(q7.to_string(index=False))

# ── Q8: High risk segment identification ──────────────
print("\n📊 Q8 — Highest Risk Borrower Profile:")
q8 = pd.read_sql_query("""
    SELECT
        CASE
            WHEN age BETWEEN 18 AND 30 THEN '18-30'
            WHEN age BETWEEN 31 AND 40 THEN '31-40'
            WHEN age BETWEEN 41 AND 50 THEN '41-50'
            WHEN age BETWEEN 51 AND 60 THEN '51-60'
            ELSE '60+'
        END as age_group,
        CASE
            WHEN MonthlyIncome <= 3000 THEN 'Low Income'
            ELSE 'Higher Income'
        END as income_segment,
        COUNT(*) as applicants,
        ROUND(AVG(SeriousDlqin2yrs)*100, 2) as default_rate_pct,
        ROUND(AVG(RevolvingUtilizationOfUnsecuredLines)*100, 2) as avg_utilization_pct
    FROM loans
    GROUP BY age_group, income_segment
    HAVING COUNT(*) > 500
    ORDER BY default_rate_pct DESC
    LIMIT 10
""", conn)
print(q8.to_string(index=False))

conn.close()
print("\n✅ All 8 queries complete")