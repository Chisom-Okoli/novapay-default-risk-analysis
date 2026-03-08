# novapay-default-risk-analysis
End-to-end loan default investigation for a Nigerian digital lender - Python data analysis + Power BI executive dashboard.  Covers data generation, EDA, risk segmentation, and business recommendations.

#  NovaPay Default Risk Analysis
![Python](https://img.shields.io/badge/Python-3.x-blue)
![PowerBI](https://img.shields.io/badge/PowerBI-Dashboard-yellow)
![Status](https://img.shields.io/badge/Status-Complete-green)
![Domain](https://img.shields.io/badge/Domain-Fintech%20%7C%20Credit%20Risk-orange)

> End-to-end data analysis investigating a spike in micro-loan default rates across a Nigerian digital lending platform from raw data exploration to executive dashboard.

---

##  Project Overview

NovaPay is a Nigerian digital lending company offering instant micro-loans (₦5,000 – ₦500,000) via mobile app. Loans are disbursed within 90 seconds using an automated credit scoring model with no collateral or paperwork required.

After two years of stable performance at a **4.2% default rate**, the company recorded a sharp spike to **9.8% in Q3 2024**, resulting in significant write-offs and growing pressure from investors ahead of the next funding round.

As the data analyst on the risk team, I was tasked with identifying the root causes of the spike and delivering findings to the Chief Risk Officer and board within four weeks.

---
## Dashboard Overview
https://github.com/Chisom-Okoli/novapay-default-risk-analysis/blob/main/Dashboard_Overview.png

##  Business Questions

- Which borrower segments are defaulting and why?
- Did the growth team's manual approval overrides cause disproportionate damage?
- Is the credit scoring model still reliable?
- Which collections channels are most effective at recovering bad debt?
- What should leadership monitor on a weekly basis going forward?

---

## 🔍 Key Findings

| Finding | Detail |
|---|---|
| 🔴 Override loans default rate | **26.8%** vs 9.3% for standard approvals - nearly 3× worse |
| 🔴 Unemployed borrowers | **18.4%** default rate - highest of any employment segment |
| 🔴 18–25 age group | **16.0%** default rate - almost double every other age group |
| 🟡 Credit model blind spot | Scores 450–599 and 600–749 defaulting at near-identical rates (10.2% vs 10.0%) |
| 🟡 Highest risk combination | Young + Gig/Unemployed + Override loans defaulting at **31.2%** |
| 🟢 Best collections channel | Phone calls converting at **27%** - highest of all contact methods |

---

##  Dataset

Five tables extracted from the company data warehouse:

```
borrowers.csv             2,000 rows    Borrower demographics & acquisition channel
loans.csv                 3,202 rows    Loan details, credit scores, override flags
repayments.csv            3,383 rows    Payment records including partial payments
credit_score_factors.csv  2,000 rows    Behavioral signals used in credit scoring
collections_log.csv       1,077 rows    Collections contact attempts & outcomes
```

> ⚠️ All personally identifiable information has been anonymised. Borrower IDs are hashed and no names, phone numbers or BVN data are included in this repository.

---

##  Tools Used

| Tool | Purpose |
|---|---|
| Python 3 | Data exploration & analysis |
| Pandas | Data manipulation & profiling |
| Power BI Desktop | Interactive executive dashboard |
| VS Code | Development environment |

---

##  Project Structure

```
novapay-default-risk-analysis/
│
├── data/
│   ├── borrowers.csv
│   ├── loans.csv
│   ├── repayments.csv
│   ├── credit_score_factors.csv
│   └── collections_log.csv
│
├── scripts/
│   ├── step1_explore.py        # Data exploration & profiling
│   └── step2_analysis.py       # Core analytical queries
│
├── dashboard/
│   └── novapay_dashboard.pbix  # Power BI dashboard file
│
├── assets/
│   └── novapay_titlebar.png    # Dashboard title bar
│
└── README.md
```

---

##  Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/Chisom-Okoli/novapay-default-risk-analysis.git
cd novapay-default-risk-analysis
```

### 2. Install dependencies
```bash
pip install pandas numpy
```

### 3. Run the exploration
```bash
python scripts/step1_explore.py
```

### 4. Open the dashboard
Open `dashboard/novapay_dashboard.pbix` in Power BI Desktop.

---

## 📊 Analysis Walkthrough

### Step 1 - Data Exploration
Profiled all 5 tables. Checked row counts, missing values, data types and referential integrity across tables before any analysis began.

```python
borrowers   = pd.read_csv("data/borrowers.csv")
loans       = pd.read_csv("data/loans.csv")

print(borrowers.shape)   # (2000, 9)
print(loans.shape)       # (3202, 10)
```

Key data quality flags raised at this stage:
- 164 loans issued to borrowers with ₦0 declared income
- 588 loans issued to borrowers with unverified BVN
- 190 defaulted loans with zero repayment records - potential fraud

---

### Step 2 - Suspect 1: Growth Team Overrides
Compared default rates between manually overridden and standard approvals.

```python
closed_loans = loans[loans["status"] != "active"].copy()
closed_loans["is_default"] = closed_loans["status"].isin(["defaulted", "written_off"])

default_rates = closed_loans.groupby("approval_threshold_override")["is_default"].mean() * 100
# False    9.3%
# True    26.8%
```

**Finding:** Override loans defaulted at nearly 3× the rate of standard approvals. The growth team approved 437 loans that the credit model had flagged as high risk. This single decision accounts for a significant portion of the write-offs.

---

### Step 3 - Suspect 2: Customer Segment Risk
Identified which employment types and age groups carried the highest default risk.

```python
loan_profiles = closed_loans.merge(borrowers, on="borrower_id")

by_employment = loan_profiles.groupby("employment_type")["is_default"].mean() * 100
# Unemployed    18.4%
# Gig Worker    13.2%
# Salaried      10.2%
# Self-Employed  9.9%
```

**Finding:** The company's expansion into younger demographics and gig economy workers introduced segments with significantly higher default risk than the core borrower base.

---

### Step 4 - Suspect 3: Credit Model Reliability
Tested whether credit scores still predicted default outcomes accurately.

```python
loan_profiles["score_band"] = pd.cut(
    loan_profiles["credit_score_at_approval"],
    bins=[299, 449, 599, 749, 850],
    labels=["300-449", "450-599", "600-749", "750-850"]
)

by_score = loan_profiles.groupby("score_band", observed=True)["is_default"].mean() * 100
# 300-449    17.2%
# 450-599    10.2%
# 600-749    10.0%   ← near-identical to band below
# 750-850     8.5%
```

**Finding:** The model correctly identifies extreme cases but is effectively blind in the 450–749 range - covering the majority of the loan book. The model has not been retrained since 2022 despite significant macroeconomic shifts including naira devaluation and rising inflation.

---

##  Business Recommendations

###  Immediate (0–30 Days)
- **Freeze all approval overrides** - override loans default at 3× the rate of standard approvals
- **Pause lending to unemployed borrowers** - 18.4% default rate cannot be sustained at current interest rates
- **Escalate collections on 80 identified high-risk active loans** — young + gig/unemployed + override combination defaulting at 31.2%

###  Short Term (1–3 Months)
- **Retrain the credit model** on 2023–2024 data - current model has a significant blind spot between scores 450–749
- **Introduce segment-specific loan products** - gig workers require shorter repayment terms aligned to income volatility
- **Require dual senior approval and written justification** for any future overrides

###  Strategic (3–12 Months)
- **Track clean cohort performance** from the month overrides were frozen - use this as primary evidence of recovery for investor conversations
- **Invest in WhatsApp-based collections sequences** - most personal channel, currently underperforming its potential
- **Present a structured recovery narrative to the board** with month-by-month improvement data

---

##  Executive Dashboard - Weekly Monitoring Metrics

| Metric | Target | Red Flag | Visual |
|---|---|---|---|
| Weekly Default Rate | <10% | >15% | Line chart |
| Override Rate | <2% | >5% | KPI Card |
| Default Rate by Employment | Stable week on week | Any segment +3% | Bar chart |
| Collections Recovery Rate | >35% | <20% | KPI Card |
| New Loans to 18–25 Age Group | <20% of weekly approvals | >30% | Donut chart |
| Average Credit Score of Approvals | >620 | <580 | Line chart |
| Weekly Loan Volume (NGN) | Stable or growing | Drop >20% WoW | Bar chart |
| Collections Channel Conversion | >40% on one channel | All channels <25% | Bar chart |

---

##  Skills Demonstrated

- Exploratory data analysis and data quality profiling
- Multi-table joins and relational data modelling
- Segmentation analysis across demographic and behavioural dimensions
- Credit risk analysis and model performance evaluation
- Translating analytical findings into executive-level business recommendations
- End-to-end dashboard design in Power BI

---
