import os
import sys
sys.path.insert(0, os.path.abspath("."))
import pandas as pd
import numpy as np

print("Python version:", sys.version)
print("Pandas version:", pd.__version__)
print("NumPy version:", np.__version__)

import database
import analytics
import supabase_client

print("\n--- Testing Database Init ---")
database.init_db()

raw_expenses = database.get_all_expenses()
print(f"Retrieved {len(raw_expenses)} expenses from local DB.")

print("\n--- Testing prepare_dataframe with empty list ---")
df_empty = analytics.prepare_dataframe([])
print("Empty df shape:", df_empty.shape)
print("Empty df dtypes:\n", df_empty.dtypes)

print("\n--- Testing prepare_dataframe with raw expenses ---")
try:
    df_raw = analytics.prepare_dataframe(raw_expenses)
    print("Raw df shape:", df_raw.shape)
    print("Raw df head:\n", df_raw.head())
except Exception as e:
    import traceback
    print("ERROR in prepare_dataframe(raw_expenses):", e)
    traceback.print_exc()

print("\n--- Testing prepare_dataframe with Supabase-style expenses ---")
sample_supabase_expense = [{
    "id": "e4b3e8c1-1234-5678-9abc-def012345678",
    "user_id": "u1234",
    "amount": 150.50,
    "category": "Food",
    "note": "Lunch",
    "expense_date": "2026-10-03",
    "expense_time": "12:30:00",
    "payment_method": "UPI",
    "created_at": "2026-10-03T12:30:00Z"
}]
try:
    df_sb = analytics.prepare_dataframe(sample_supabase_expense)
    print("Supabase df shape:", df_sb.shape)
except Exception as e:
    import traceback
    print("ERROR with Supabase sample:", e)
    traceback.print_exc()

print("\n--- Supabase Config Check ---")
print("SUPABASE_URL set?", bool(os.environ.get("SUPABASE_URL")))
print("SUPABASE_ANON_KEY set?", bool(os.environ.get("SUPABASE_ANON_KEY")))
print("supabase_client.is_configured():", supabase_client.is_configured())
