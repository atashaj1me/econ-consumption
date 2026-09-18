# Calculate Consumption Growth Rate (Difference of Natural Logs)
df["Consumption_Growth"] = np.log(df["Consumption"]).diff() * 100

# Clean missing variables; drop years where data is NaN
data = df[["Consumption_Growth", "Real_Interest_Rate"]].dropna()

# Define variables
Y = data["Consumption_Growth"]
X = data ["Real_Interest_Rate"]
X = sm.add_constant(X)  # Adds the intercept to the regression

# Fit Ordinary Least Squares (OLS) model
model = sm.OLS(Y, X)
results = model.fit()

# Output professional summary metrics
print(results.summary())