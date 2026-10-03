import os, sys
sys.path.insert(0, os.path.abspath("."))
import datetime
import pandas as pd
import analytics
import plotly.express as px

print("--- Test 1: Empty DataFrame ---")
df_empty = analytics.prepare_dataframe([])
metrics_empty = analytics.get_dashboard_metrics(df_empty)
pie_empty = analytics.create_category_pie_chart(df_empty)
trend_empty = analytics.create_trend_chart(df_empty)
insights_empty = analytics.generate_spending_insights(df_empty)
print("Empty tests passed!")

print("\n--- Test 2: DataFrame with sample data ---")
sample_data = [
    {
        "id": 1,
        "amount": 250.0,
        "category": "Food",
        "note": "Lunch",
        "expense_date": "2026-10-03",
        "expense_time": "12:00:00",
        "payment_method": "UPI",
        "created_at": "2026-10-03 12:00:00"
    },
    {
        "id": 2,
        "amount": 120.50,
        "category": "Transportation",
        "note": "Bus ticket",
        "expense_date": "2026-10-02",
        "expense_time": "09:00:00",
        "payment_method": "Cash",
        "created_at": "2026-10-02 09:00:00"
    },
    {
        "id": 3,
        "amount": "500",
        "category": "Food",
        "note": "Dinner",
        "expense_date": "2026-09-25",
        "expense_time": "20:00:00",
        "payment_method": "Card",
        "created_at": "2026-09-25 20:00:00"
    }
]

df_sample = analytics.prepare_dataframe(sample_data)
print("Prepared df dtypes:\n", df_sample.dtypes)
print(df_sample)

metrics_sample = analytics.get_dashboard_metrics(df_sample)
print("Metrics:", metrics_sample)

pie_month = analytics.create_category_pie_chart(df_sample, "this_month")
pie_week = analytics.create_category_pie_chart(df_sample, "this_week")
print("Pie charts created:", bool(pie_month), bool(pie_week))

trend_month = analytics.create_trend_chart(df_sample, "this_month")
trend_week = analytics.create_trend_chart(df_sample, "this_week")
print("Trend charts created:", bool(trend_month), bool(trend_week))

insights = analytics.generate_spending_insights(df_sample)
print("Insights:", insights)
