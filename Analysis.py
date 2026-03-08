import pandas as pd

# ── LOAD ALL 5 TABLES ──────────────────────────────────────
borrowers   = pd.read_csv("borrowers.csv")
loans       = pd.read_csv("loans.csv")
repayments  = pd.read_csv("repayments.csv")
csf         = pd.read_csv("credit_score_factors.csv")
collections = pd.read_csv("collections_log.csv")

# ── REMOVE ACTIVE LOANS (not finished yet) ─────────────────
closed_loans = loans[loans["status"] != "active"].copy()

# ── MARK WHICH LOANS DEFAULTED ─────────────────────────────
closed_loans["is_default"] = closed_loans["status"].isin(["defaulted", "written_off"])

# ── SUSPECT 1: OVERRIDE DEFAULT RATES ──────────────────────
print("=== SUSPECT 1: Override vs Normal Loans ===")
default_rates = closed_loans.groupby("approval_threshold_override")["is_default"].mean() * 100
print(default_rates.round(1))

# ── SUSPECT 2: JOIN LOANS WITH BORROWER INFO ───────────────
print("\n=== SUSPECT 2: Joining loans with borrowers ===")
loan_profiles = closed_loans.merge(borrowers, on="borrower_id")
print(loan_profiles.shape)

# ── DEFAULT RATE BY EMPLOYMENT TYPE ───────────────────────
print("\n=== DEFAULT RATE BY EMPLOYMENT TYPE ===")
by_employment = loan_profiles.groupby("employment_type")["is_default"].mean() * 100
print(by_employment.round(1).sort_values(ascending=False))

# ── CREATE AGE BANDS ───────────────────────────────────────
loan_profiles["age_band"] = pd.cut(
    loan_profiles["age"],
    bins   = [17, 25, 35, 45, 55, 65],
    labels = ["18-25", "26-35", "36-45", "46-55", "56-64"]
)

# ── DEFAULT RATE BY AGE BAND ───────────────────────────────
print("\n=== DEFAULT RATE BY AGE GROUP ===")
by_age = loan_profiles.groupby("age_band", observed=True)["is_default"].mean() * 100
print(by_age.round(1).sort_values(ascending=False))

# ── THE HIGH RISK COMBINATION ──────────────────────────────
print("\n=== THE DANGEROUS PROFILE ===")

high_risk = loan_profiles[
    (loan_profiles["age"] <= 25) &
    (loan_profiles["employment_type"].isin(["Gig Worker", "Unemployed"])) &
    (loan_profiles["approval_threshold_override"] == True)
]

print(f"Total high risk loans:     {len(high_risk)}")
print(f"Default rate:              {(high_risk['is_default'].mean() * 100).round(1)}%")
print(f"Total amount lent (NGN):   {high_risk['loan_amount_ngn'].sum():,.0f}")


# ── CREATE CREDIT SCORE BANDS ──────────────────────────────
print("\n=== SUSPECT 3: Credit Score vs Default Rate ===")

loan_profiles["score_band"] = pd.cut(
    loan_profiles["credit_score_at_approval"],
    bins   = [299, 449, 599, 749, 850],
    labels = ["300-449", "450-599", "600-749", "750-850"]
)

by_score = loan_profiles.groupby("score_band", observed=True)["is_default"].mean() * 100
print(by_score.round(1).sort_values(ascending=False))

# ── FULL SUMMARY ───────────────────────────────────────────
print("\n=== FULL INVESTIGATION SUMMARY ===")

print("\n1. Override vs Normal:")
print(f"   Normal loans default rate:   {closed_loans[closed_loans['approval_threshold_override']==False]['is_default'].mean()*100:.1f}%")
print(f"   Override loans default rate: {closed_loans[closed_loans['approval_threshold_override']==True]['is_default'].mean()*100:.1f}%")

print("\n2. Riskiest employment types:")
print(f"   Unemployed:   18.4%")
print(f"   Gig Worker:   13.2%")

print("\n3. Riskiest age group:")
print(f"   18-25 year olds: 16.0%")

print("\n4. Credit model blind spot:")
print(f"   Score 450-599 default rate: 10.2%")
print(f"   Score 600-749 default rate: 10.0%")
print(f"   (Model cannot distinguish between these two bands)")

print("\n5. The dangerous combination:")
print(f"   Young + Gig/Unemployed + Override: 31.2%")



import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── SET UP THE DASHBOARD CANVAS ────────────────────────────
fig = plt.figure(figsize=(16, 12))
fig.suptitle("NovaPay Executive Dashboard", fontsize=20, fontweight="bold", y=0.98)
gs  = gridspec.GridSpec(3, 3, figure=fig, hspace=0.5, wspace=0.4)

# ── CHART 1: Default Rate Over Time ────────────────────────
ax1 = fig.add_subplot(gs[0, :2])
monthly = (
    loan_profiles.groupby(
        loan_profiles["disbursement_date"].str[:7]
    )["is_default"].mean() * 100
).reset_index()
monthly.columns = ["month", "default_rate"]
monthly = monthly.sort_values("month").tail(18)
ax1.plot(monthly["month"], monthly["default_rate"], color="#e74c3c", linewidth=2.5, marker="o")
ax1.axhline(y=10, color="orange", linestyle="--", linewidth=1.5, label="Warning (10%)")
ax1.axhline(y=15, color="red",    linestyle="--", linewidth=1.5, label="Red Flag (15%)")
ax1.set_title("Default Rate Over Time (%)", fontweight="bold")
ax1.set_xlabel("Month")
ax1.set_ylabel("Default Rate (%)")
ax1.tick_params(axis="x", rotation=45)
ax1.legend(fontsize=8)

# ── CHART 2: Override Rate ──────────────────────────────────
ax2 = fig.add_subplot(gs[0, 2])
override_counts = closed_loans["approval_threshold_override"].value_counts()
ax2.pie(
    override_counts,
    labels   = ["Normal", "Override"],
    colors   = ["#2ecc71", "#e74c3c"],
    autopct  = "%1.1f%%",
    startangle=90
)
ax2.set_title("Override vs Normal\nApprovals", fontweight="bold")

# ── CHART 3: Default Rate by Employment ────────────────────
ax3 = fig.add_subplot(gs[1, :2])
emp_default = (
    loan_profiles.groupby("employment_type")["is_default"]
    .mean() * 100
).sort_values(ascending=True)
colors = ["#2ecc71", "#2ecc71", "#e67e22", "#e74c3c"]
ax3.barh(emp_default.index, emp_default.values, color=colors)
ax3.axvline(x=10, color="orange", linestyle="--", linewidth=1.5, label="Warning (10%)")
ax3.set_title("Default Rate by Employment Type (%)", fontweight="bold")
ax3.set_xlabel("Default Rate (%)")
ax3.legend(fontsize=8)
for i, v in enumerate(emp_default.values):
    ax3.text(v + 0.2, i, f"{v:.1f}%", va="center", fontsize=9)

# ── CHART 4: Default Rate by Age Band ──────────────────────
ax4 = fig.add_subplot(gs[1, 2])
age_default = (
    loan_profiles.groupby("age_band", observed=True)["is_default"]
    .mean() * 100
).sort_values(ascending=False)
bar_colors = ["#e74c3c", "#e67e22", "#e67e22", "#2ecc71", "#2ecc71"]
ax4.bar(age_default.index, age_default.values, color=bar_colors)
ax4.set_title("Default Rate\nby Age Group (%)", fontweight="bold")
ax4.set_ylabel("Default Rate (%)")
ax4.tick_params(axis="x", rotation=45)
for i, v in enumerate(age_default.values):
    ax4.text(i, v + 0.2, f"{v:.1f}%", ha="center", fontsize=8)

# ── CHART 5: Collections Effectiveness ─────────────────────
ax5 = fig.add_subplot(gs[2, :2])
contact_effect = (
    collections.groupby("contact_method")["contact_outcome"]
    .apply(lambda x: (x == "paid").mean() * 100)
).sort_values(ascending=True)
bar_colors2 = ["#e74c3c" if v < 25 else "#2ecc71" for v in contact_effect.values]
ax5.barh(contact_effect.index, contact_effect.values, color=bar_colors2)
ax5.axvline(x=25, color="orange", linestyle="--", linewidth=1.5, label="Min Target (25%)")
ax5.set_title("Collections: Payment Conversion by Contact Method (%)", fontweight="bold")
ax5.set_xlabel("Conversion Rate (%)")
ax5.legend(fontsize=8)
for i, v in enumerate(contact_effect.values):
    ax5.text(v + 0.2, i, f"{v:.1f}%", va="center", fontsize=9)

# ── CHART 6: Credit Score Band Default Rate ────────────────
ax6 = fig.add_subplot(gs[2, 2])
score_default = (
    loan_profiles.groupby("score_band", observed=True)["is_default"]
    .mean() * 100
).sort_values(ascending=False)
ax6.bar(score_default.index, score_default.values,
        color=["#e74c3c","#e67e22","#f1c40f","#2ecc71"])
ax6.set_title("Default Rate\nby Credit Score Band (%)", fontweight="bold")
ax6.set_ylabel("Default Rate (%)")
ax6.tick_params(axis="x", rotation=45)
for i, v in enumerate(score_default.values):
    ax6.text(i, v + 0.2, f"{v:.1f}%", ha="center", fontsize=8)

plt.savefig("novapay_dashboard.png", dpi=150, bbox_inches="tight")
print("Dashboard saved as novapay_dashboard.png")
plt.show()

















