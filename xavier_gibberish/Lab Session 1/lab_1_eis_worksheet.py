
"""

ECON 313 - Lab Session 1

lab_1_eis.py
------------

This file estimates the EIS from the Euler Equation using aggregate data.

"""
import pandas as pd
import statsmodels.api as sm

#%% --------------------------------------------------
# Load the data

cons = pd.read_excel("cdata.xls", sheet_name="Data", skiprows=3)
rate = pd.read_excel("rdata.xls", sheet_name="Data", skiprows=3)

# Change from wide to long

cons = cons.melt(
    id_vars=["Country Name", "Country Code"],
    value_vars=[c for c in cons.columns if str(c).isdigit()],
    var_name="year",
    value_name="consumption"
)

rate = rate.melt(
    
)

# Adjoin the two data sets

data = pd.merge(
    cons,
    rate,
    on=["Country Code", "Country Name", "year"]
)

# Calculate consumption growth

data = data.sort_values(["Country Code", "year"])

data["consumption_growth"] = (
    data.groupby("Country Code")["consumption"].ffill().pct_change(fill_method=None) * 100
)

#%% --------------------------------------------------
# Estimate the EIS by OLS
# consumption growth = a0 + a1 * interest rate + error term

data_clean = data.dropna(
    subset=["consumption_growth", "interest_rate"]
)

X = sm.add_constant(data_clean["interest_rate"])
y = data["consumption_growth"]

ols_model = sm.OLS(y, X).fit()

print(ols_model.summary())

# Estimate EIS for the US only
ols_model_us = sm.OLS(
    data.loc[data["Country Code"] == "USA", "consumption_growth"],
    sm.add_constant(
        data.loc[data["Country Code"] == "USA", "interest_rate"]
    ),
    missing="drop"
).fit()

print(ols_model_us.summary())

#%% --------------------------------------------------
# Estimate the EIS by 2SLS

# Create the instrument
data = data.sort_values(["Country Code", "year"])
data["interest_rate_lag"] = (
    data.groupby("Country Code")["interest_rate"].shift(1)
)

# First stage
first_stage_all = sm.OLS.from_formula(
    "interest_rate ~ interest_rate_lag", # Includes intercept by default
    data=data
).fit()

print(first_stage_all.summary())

# Fitted values
data["interest_rate_hat_all"] = first_stage_all.predict(data)

# Second stage
second_stage_all = sm.OLS.from_formula(
    "consumption_growth ~ interest_rate_hat_all", # Includes intercept by default
    data=data
).fit()

print(second_stage_all.summary()) # The standarde errors won't be correct. Need the other package

# Estimate IV for the US only
# First stage
first_stage_us = sm.OLS.from_formula(
    
    data=data.query("`Country Code` == 'USA'")
).fit()

print(first_stage_us.summary())

# Fitted values
data["interest_rate_hat_us"] = first_stage_us.predict(data)

# Second stage
second_stage_us = sm.OLS.from_formula(
    
    data=data.query("`Country Code` == 'USA'")
).fit()

print(second_stage_us.summary()) # The standarde errors won't be correct. Need the other package