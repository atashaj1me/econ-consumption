#%% --------------------------------------------------
"""

ECON 313 - Lab Session 1

lab_1_lcp.py
------------

This file plots the life cycle profiles of income and wealth using microdata.

"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm

#%% --------------------------------------------------

#Load data
df = pd.read_csv("scf2022.csv")

print(df.head())
print(df[["AGE", "INCOME", "NETWORTH", "LIQ", "WGT"]].describe())

# Function to calculate a weighted average (since we have survey data)
def weighted_mean(group, variable):
    return np.average(
        group[variable],
        weights=group["WGT"]
    )

# Calculate weighted averages by age
profile = df.groupby("AGE").apply(
    lambda g: pd.Series({
        "income": weighted_mean(g, "INCOME"),
        "wealth": weighted_mean(g, "NETWORTH"),
        "liquid": weighted_mean(g, "LIQ")
    }),
    include_groups=False
)

print(profile.head())

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Income profile
axes[0].plot(profile.index, profile["income"])
axes[0].set_title("Life-Cycle Profile of Income")
axes[0].set_xlabel("Age")
axes[0].set_ylabel("Average income")
axes[0].grid(True)

# Wealth profile
axes[1].plot(profile.index, profile["wealth"])
axes[1].set_title("Life-Cycle Profile of Net Worth")
axes[1].set_xlabel("Age")
axes[1].set_ylabel("Average net worth")
axes[1].grid(True)

plt.tight_layout()
plt.show()

#%% --------------------------------------------------

# Create polynomial terms
for power in range(1, 5): # In Python, the upper limit is not included.
    df[f"age{power}"] = df["AGE"] ** power


# Function to estimate a quartic polynomial
def quartic_regression(data, outcome):

    X = data[
        ["age1", "age2", "age3", "age4"]
    ]

    X = sm.add_constant(X)

    y = data[outcome]

    # Weighted least squares: We weight by the survey weights
    model = sm.WLS(
        y,
        X,
        weights=data["WGT"]
    ).fit()

    return model


# Estimate income profile
income_model = quartic_regression(df, "INCOME")

# Estimate wealth profile
wealth_model = quartic_regression(df, "NETWORTH")

# Display regression results
print(income_model.summary())
print(wealth_model.summary())

# Create an age grid
age_grid = np.arange(18, 96)

# Construct polynomial terms
X_grid = pd.DataFrame({
    "age1": age_grid,
    "age2": age_grid ** 2,
    "age3": age_grid ** 3,
    "age4": age_grid ** 4
})

X_grid = sm.add_constant(X_grid)

# Generate predictions
income_pred = income_model.predict(X_grid)
wealth_pred = wealth_model.predict(X_grid)

# Plot profiles
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Income
axes[0].plot(age_grid, income_pred)
axes[0].set_title("Quartic Income Profile")
axes[0].set_xlabel("Age")
axes[0].set_ylabel("Predicted income")
axes[0].grid(True)

# Wealth
axes[1].plot(age_grid, wealth_pred)
axes[1].set_title("Quartic Wealth Profile")
axes[1].set_xlabel("Age")
axes[1].set_ylabel("Predicted net worth")
axes[1].grid(True)

plt.tight_layout()
plt.show()

#%% --------------------------------------------------

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Income
axes[0].plot(
    profile.index,
    profile["income"],
    label="Weighted averages"
)

axes[0].plot(
    age_grid,
    income_pred,
    label="Quartic polynomial"
)

axes[0].set_title("Income: Averages vs Quartic")
axes[0].set_xlabel("Age")
axes[0].set_ylabel("Income")
axes[0].legend()
axes[0].grid(True)

# Wealth
axes[1].plot(
    profile.index,
    profile["wealth"],
    label="Weighted averages"
)

axes[1].plot(
    age_grid,
    wealth_pred,
    label="Quartic polynomial"
)

axes[1].set_title("Wealth: Averages vs Quartic")
axes[1].set_xlabel("Age")
axes[1].set_ylabel("Net worth")
axes[1].legend()
axes[1].grid(True)

plt.tight_layout()
plt.show()

#%% --------------------------------------------------

# Weighted average liquid wealth by age

plt.figure(figsize=(8, 5))

plt.plot(
    profile["liquid"].index,
    profile["liquid"].values
)

plt.title("Life-Cycle Profile of Liquid Wealth")
plt.xlabel("Age")
plt.ylabel("Average liquid wealth")

plt.grid(True)
plt.show()

# Independent variables
X = df[["age1", "age2", "age3", "age4"]]

# Add constant (intercept)
X = sm.add_constant(X)

# Dependent variable
y = df["LIQ"]

# Estimate weighted least squares regression
liquid_model = sm.WLS(
    y,
    X,
    weights=df["WGT"]
).fit()

# Display results
print(liquid_model.summary())

#%% --------------------------------------------------

# Create polynomial terms for predictions
X_grid = pd.DataFrame({
    
})

X_grid = sm.add_constant(X_grid)

# Generate predicted liquid wealth
liquid_pred = 

# Plot
plt.figure(figsize=(8, 5))

plt.plot(age_grid, liquid_pred)

plt.title("Quartic Life-Cycle Profile of Liquid Wealth")
plt.xlabel("Age")
plt.ylabel("Predicted liquid wealth")

plt.grid(True)
plt.show()

#%% --------------------------------------------------

# Plot both profiles of liquid wealth
plt.figure(figsize=(8, 5))

plt.plot(
    
    label="Weighted averages"
)

plt.plot(
    
    label="Quartic polynomial"
)

plt.title("Liquid Wealth: Averages vs Quartic")
plt.xlabel("Age")
plt.ylabel("Liquid wealth")
plt.legend()
plt.grid(True)

del X, X_grid, y, power, axes, fig