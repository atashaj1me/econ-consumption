#%% --------------------------------------------------
"""

ECON 313 - Lab Session 3

lab_3_risk_sharing.py
---------------------

This file contains code snippets to estimate regressions. The examples below are not risk-sharing regressions.

"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from linearmodels.system import SUR
from linearmodels.system import IV3SLS
#%% --------------------------------------------------
#Load data
df = pd.read_csv("INSERT CSV FILENAME HERE")

#Drop NA
df = df.dropna(
    subset=["dc", "dy", "hhid", "year", "state"]
).copy()

#Mean in one year
yearly = df.groupby("year")[["dc", "dy"]].mean() 

#Group means in one year
state_year = (                            
    df.groupby(["state", "year"])["dy"]
      .mean()
      .reset_index(name="avg_dy")
)

#Summary statistics by year
summary = (
    df.groupby("year")
      .agg(
          avg_consumption=("dc", "mean"),
          avg_income=("dy", "mean"),
          sd_consumption=("dc", "std"),
          sd_income=("dy", "std"),
          n=("hhid", "count")
      )
)

#Weighted means
def weighted_mean(group, variable, weight):
    return (
        (group[variable] * group[weight]).sum()
        / group[weight].sum()
    )

#%% --------------------------------------------------
#Example application
yearly_weighted = (
    df.groupby("year")
      .apply(
          lambda g: weighted_mean(g, "dy", "weight"),
          include_groups=False
      )
)

#%% --------------------------------------------------
#OLS with clustered standard errors and dummy variables
"Estimating equation: d log c(it) = b0 + b1 d log y(it) + mu(t) + gamma(i) + e(it) "

ols = smf.ols(
    "dc ~ dy + C(hhid) + C(year)",
    data=df
).fit(
    cov_type="cluster", # H0: robust standard errors, H3: robust standard errors for small samples, HAC: Newey-West standard errors for time series
    cov_kwds={"groups": df["state"]} #"state" can be replaced with other groups to cluster over, like "hhid"
)
      
print("Coefficient on income growth:", ols.params["dy"])
print("Clustered standard error:", ols.bse["dy"])
print("P-value:", ols.pvalues["dy"])

#%% --------------------------------------------------
#FGLS with dummy variables
"Estimating equation: d log c(it) = b0 + b1 d log y(it) + mu(t) + gamma(i) + e(it) "

# Estimate by ols
ols = smf.ols(
    "dc ~ dy + C(hhid) + C(year)",
    data=df
).fit()

# Save residuals
df["resid"] = ols.resid

#Estimate residual variance within each state
state_var = (
    df.groupby("state")["resid"]
      .var()
)

# Assign estimated variance to each observation
df["sigma2"] = df["state"].map(state_var)

# Construct the design matrix
y = df["dc"]

X = smf.ols(
    "dc ~ dy + C(hhid) + C(year)",
    data=df
).exog

# Feasible GLS

fgls = sm.GLS(
    y,
    X,
    sigma=df["sigma2"].to_numpy()
).fit()


#%% --------------------------------------------------
#FGLS with dummy variables
"Estimating equation: d log c(it) = b0 + b1 d log y(it) + mu(t) + gamma(i) + e(it) "

# Estimate by ols
ols = smf.ols(
    "dc ~ dy + C(hhid) + C(year)",
    data=df
).fit()

# Save residuals
df["resid"] = ols.resid

#Estimate residual variance within each village
state_var = (
    df.groupby("state")["resid"]
      .var()
)

# Assign estimated variance to each observation
df["sigma2"] = df["state"].map(state_var)

# Construct the design matrix
y = df["dc"]

X = smf.ols(
    "dc ~ dy + C(hhid) + C(year)",
    data=df
).exog

# Feasible GLS

fgls = sm.GLS(
    y,
    X,
    sigma=df["sigma2"].to_numpy()
).fit()

#%% --------------------------------------------------
#SUR model with FGLS
'''
Estimating equation: 
    d log cfood(it) = b0 + b1 d log y(it) + mu(t) + gamma(i) + e(it) 
    d log cnonfood(it) = a0 + a1 d log y(it) + alpha(t) + beta(i) + u(it) 
where e and u are correlated.
'''

#Define the equations to estimate
equations = {
    "food": (
        "dc_food ~ 1 + dy + C(hhid) + C(year)"
    ),

    "nonfood": (
        "dc_nonfood ~ 1 + dy + C(hhid) + C(year)"
    )
}

#Estimate the SUR model
sur_model = SUR.from_formula(
    equations,
    data=df
)

sur_results = sur_model.fit(
    method="gls"
)

print(sur_results.summary)

# Coefficients for the food equation
print(sur_results.equations["food"].params)

# Coefficients for the nonfood equation
print(sur_results.equations["nonfood"].params)

# Estimated covariance matrix of the disturbances
print(sur_results.sigma)

#%% --------------------------------------------------
#SUR model with 3SLS
'''
Estimating equation: 
    d log cfood(it) = b0 + b1 d log y(it) + mu(t) + gamma(i) + e(it) 
    d log cnonfood(it) = a0 + a1 d log y(it) + alpha(t) + beta(i) + u(it) 
where e and u are correlated, y is endogenous, and z is the instrument.
'''

#Define the equations to estimate
equations_3sls = {
    "food": (
        "dc_food ~ 1 + C(hhid) + C(year) "
        "+ [dy ~ z_dy]"
    ),

    "nonfood": (
        "dc_nonfood ~ 1 + C(hhid) + C(year) "
        "+ [dy ~ z_dy]"
    )
}

#Estimate the SUR model
model_3sls = IV3SLS.from_formula(
    equations_3sls,
    data=df
)

results_3sls = model_3sls.fit(
    method="gls"
)

print(results_3sls.summary)