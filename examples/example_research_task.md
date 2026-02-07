# Example Research Task

## Task Description

"Deep dive: Is multifamily real-estate still attractive in 2026 if rates stay high? Use web data + build a simple Python cash-flow model with sensitivity tables."

## Expected Agent Behavior

### Phase 1: Research
The agent should:
1. Search for current multifamily real estate market data
2. Find information about interest rates and cap rates in 2026
3. Look for rental market trends and vacancy rates
4. Query knowledge base for any existing real estate analysis

### Phase 2: Analysis
The agent should:
1. Build a cash-flow model in Python
2. Include key parameters:
   - Purchase price
   - Down payment
   - Interest rate
   - Rental income
   - Operating expenses
   - Vacancy rate
   - Cap rate
3. Run sensitivity analysis on:
   - Interest rates (5%, 6%, 7%, 8%)
   - Rent growth (0%, 2%, 4%)
   - Vacancy rates (5%, 10%, 15%)
   - Cap rates (4%, 5%, 6%, 7%)

### Phase 3: Visualization
The agent should create:
1. Cash flow projection chart (10-year timeline)
2. Sensitivity heatmap (IRR vs. interest rate and rent growth)
3. Break-even analysis chart
4. Comparison table of scenarios

### Phase 4: Report
The agent should write a comprehensive report including:
1. Executive summary with clear recommendation
2. Current market conditions (with sources)
3. Model assumptions and methodology
4. Sensitivity analysis results
5. Risk factors and considerations
6. Actionable recommendations
7. Data sources cited

### Phase 5: Self-Evaluation
The agent should:
1. Rate its work on all quality dimensions
2. Identify strengths (e.g., "Comprehensive sensitivity analysis")
3. Identify weaknesses (e.g., "Limited to publicly available data")
4. Suggest improvements (e.g., "Next time, include more local market data")

## Expected Output Structure

```
research_runs/2026-02-06_multifamily-real-estate/
├── metadata.json
├── report.md
├── evaluation.json
├── sources.json
├── code/
│   ├── cashflow_model.py
│   └── sensitivity_analysis.py
├── charts/
│   ├── cashflow_projection.png
│   ├── sensitivity_heatmap.png
│   ├── breakeven_analysis.png
│   └── scenario_comparison.png
└── data/
    ├── market_data.json
    └── assumptions.json
```

## Sample Report Excerpt

```markdown
# Multifamily Real Estate Investment Analysis: 2026 High-Rate Environment

## Executive Summary

Based on current market data and financial modeling, multifamily real estate 
remains moderately attractive in 2026 despite elevated interest rates. Our 
analysis shows positive cash flows are achievable with:
- Cap rates above 5.5%
- Rent growth of at least 2% annually
- Vacancy rates below 10%

**Recommendation**: Proceed with caution. Focus on markets with strong 
fundamentals and negotiate aggressively on price.

## Current Market Conditions

As of February 2026, the multifamily real estate market faces several headwinds:

1. **Interest Rates**: The Federal Reserve has maintained rates at 5.25-5.50%, 
   with mortgage rates for commercial properties averaging 7.2% [Source: Federal 
   Reserve, 2026].

2. **Cap Rates**: Cap rates have compressed to 5.0-6.5% in major markets, down 
   from historical averages [Source: CBRE Market Report Q4 2025].

3. **Rental Demand**: Despite economic uncertainty, rental demand remains strong 
   with national vacancy rates at 6.8% [Source: Apartment List, Jan 2026].

...
```

## Sample Code Excerpt

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Model Parameters
purchase_price = 5_000_000
down_payment_pct = 0.25
interest_rate = 0.072  # 7.2%
loan_term_years = 30
annual_rent = 450_000
operating_expense_ratio = 0.40
vacancy_rate = 0.068

# Calculate loan details
loan_amount = purchase_price * (1 - down_payment_pct)
monthly_rate = interest_rate / 12
num_payments = loan_term_years * 12

# Monthly mortgage payment
monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / \
                  ((1 + monthly_rate)**num_payments - 1)

# Annual cash flow
effective_gross_income = annual_rent * (1 - vacancy_rate)
operating_expenses = effective_gross_income * operating_expense_ratio
noi = effective_gross_income - operating_expenses
annual_debt_service = monthly_payment * 12
annual_cash_flow = noi - annual_debt_service

print(f"Purchase Price: ${purchase_price:,.0f}")
print(f"Down Payment: ${purchase_price * down_payment_pct:,.0f}")
print(f"Loan Amount: ${loan_amount:,.0f}")
print(f"\\nAnnual Metrics:")
print(f"Effective Gross Income: ${effective_gross_income:,.0f}")
print(f"Net Operating Income: ${noi:,.0f}")
print(f"Annual Debt Service: ${annual_debt_service:,.0f}")
print(f"Annual Cash Flow: ${annual_cash_flow:,.0f}")
print(f"\\nCash-on-Cash Return: {(annual_cash_flow / (purchase_price * down_payment_pct)) * 100:.2f}%")
print(f"Cap Rate: {(noi / purchase_price) * 100:.2f}%")

# Sensitivity Analysis
interest_rates = np.arange(0.05, 0.09, 0.005)
rent_growth_rates = np.arange(0.0, 0.05, 0.01)

# Create sensitivity matrix
sensitivity_matrix = np.zeros((len(interest_rates), len(rent_growth_rates)))

for i, rate in enumerate(interest_rates):
    for j, growth in enumerate(rent_growth_rates):
        # Calculate 10-year IRR with varying parameters
        # ... (detailed calculation)
        sensitivity_matrix[i, j] = irr_value

# Visualize sensitivity
plt.figure(figsize=(12, 8))
sns.heatmap(sensitivity_matrix, annot=True, fmt='.2f', 
            xticklabels=[f'{g*100:.0f}%' for g in rent_growth_rates],
            yticklabels=[f'{r*100:.1f}%' for r in interest_rates],
            cmap='RdYlGn', center=0.08)
plt.title('IRR Sensitivity: Interest Rate vs. Rent Growth')
plt.xlabel('Annual Rent Growth')
plt.ylabel('Interest Rate')
plt.tight_layout()
```

## Sample Evaluation

```json
{
  "task_description": "Analyze multifamily real estate attractiveness in 2026 high-rate environment",
  "metrics": {
    "clarity": 9.0,
    "data_grounding": 8.0,
    "completeness": 8.5,
    "code_quality": 9.0,
    "actionability": 8.5,
    "confidence": 7.5
  },
  "overall_score": 8.42,
  "strengths": [
    "Comprehensive sensitivity analysis covering multiple variables",
    "Clear visualizations with professional formatting",
    "Well-documented code with explanatory comments"
  ],
  "weaknesses": [
    "Limited to publicly available data, no proprietary market insights",
    "Model assumes constant operating expense ratio",
    "Did not account for property appreciation or tax benefits"
  ],
  "next_time_improvements": [
    "Include more granular local market data by MSA",
    "Add Monte Carlo simulation for risk assessment",
    "Incorporate tax implications and depreciation benefits"
  ],
  "data_sources_used": [
    "Federal Reserve Economic Data",
    "CBRE Market Reports",
    "Apartment List Rental Data"
  ],
  "tools_used": [
    "web_research",
    "execute_code",
    "create_research_run",
    "write_file"
  ]
}
```
