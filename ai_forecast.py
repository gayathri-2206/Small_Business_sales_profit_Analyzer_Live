import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import timedelta


def profit_forecast(csv_file, days=7):
    df = pd.read_csv(csv_file)

    # Convert date
    df["date"] = pd.to_datetime(df["date"])

    # Calculate profit per day
    df["signed_amount"] = df.apply(
        lambda x: x["transaction_amount"] if x["transaction_type"] == "Income" else -x["transaction_amount"],
        axis=1
    )

    daily_profit = df.groupby("date")["signed_amount"].sum().reset_index()

    # Prepare ML data
    daily_profit["day_index"] = np.arange(len(daily_profit))

    X = daily_profit[["day_index"]]
    y = daily_profit["signed_amount"]

    model = LinearRegression()
    model.fit(X, y)

    # Future prediction
    future_days = np.arange(len(daily_profit), len(daily_profit) + days).reshape(-1, 1)
    predictions = model.predict(future_days)

    future_dates = [
        daily_profit["date"].max() + timedelta(days=i + 1)
        for i in range(days)
    ]

    return {
        "dates": [d.strftime("%Y-%m-%d") for d in future_dates],
        "profits": predictions.round(2).tolist()
    }
def monthly_income_expense_forecast(csv_file, months=6):
    df = pd.read_csv(csv_file)
    df["date"] = pd.to_datetime(df["date"])

    monthly = df.groupby([
        df["date"].dt.to_period("M"),
        "transaction_type"
    ])["transaction_amount"].sum().unstack(fill_value=0)

    monthly = monthly.reset_index()
    monthly["month_index"] = range(len(monthly))

    # ----- Income Model -----
    X = monthly[["month_index"]]
    income_y = monthly.get("Income", 0)

    expense_y = monthly.get("Expense", 0)

    income_model = LinearRegression().fit(X, income_y)
    expense_model = LinearRegression().fit(X, expense_y)

    future_idx = np.arange(len(monthly), len(monthly) + months).reshape(-1, 1)

    income_pred = income_model.predict(future_idx)
    expense_pred = expense_model.predict(future_idx)

    future_months = [
        (monthly["date"].iloc[-1].to_timestamp() + pd.DateOffset(months=i + 1)).strftime("%Y-%m")
        for i in range(months)
    ]

    return {
        "labels": future_months,
        "income": income_pred.round(2).tolist(),
        "expense": expense_pred.round(2).tolist()
    }


def yearly_income_expense_forecast(csv_file, years=3):
    df = pd.read_csv(csv_file)
    df["date"] = pd.to_datetime(df["date"])

    yearly = df.groupby([
        df["date"].dt.year,
        "transaction_type"
    ])["transaction_amount"].sum().unstack(fill_value=0)

    yearly = yearly.reset_index()
    yearly["year_index"] = range(len(yearly))

    X = yearly[["year_index"]]

    income_y = yearly.get("Income", 0)
    expense_y = yearly.get("Expense", 0)

    income_model = LinearRegression().fit(X, income_y)
    expense_model = LinearRegression().fit(X, expense_y)

    future_idx = np.arange(len(yearly), len(yearly) + years).reshape(-1, 1)

    income_pred = income_model.predict(future_idx)
    expense_pred = expense_model.predict(future_idx)

    future_years = [str(yearly["date"].iloc[-1] + i + 1) for i in range(years)]

    return {
        "labels": future_years,
        "income": income_pred.round(2).tolist(),
        "expense": expense_pred.round(2).tolist()
    }

