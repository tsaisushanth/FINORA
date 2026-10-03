import sys
import os
sys.path.insert(0, os.path.abspath("."))
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

print("========================================")
print("FINORA SYSTEM VERIFICATION & INTEGRATION TEST")
print("========================================")

# 1. Imports
import auth
import profiles
import profile_view
import supabase_client as sc
import database
import analytics
import utils
import goals
print("✓ All modules imported successfully without errors.")

# 2. Database Init
database.init_db()
print("✓ Database initialized.")

# 3. Test Local Profile
p_dict = database.get_local_profile()
profile = sc.Profile.from_row(p_dict)
assert profile.name is not None
print(f"✓ Profile loaded: {profile.name} ({profile.course}, Year {profile.year})")

# 4. Test Expenses & Analytics
expense_id = database.add_expense(
    amount=250.0,
    category="Food",
    note="Team Lunch",
    expense_date="2026-10-03",
    expense_time="13:00:00",
    payment_method="UPI"
)
print(f"✓ Added test expense id: {expense_id}")

raw = database.get_all_expenses()
df = analytics.prepare_dataframe(raw)
assert not df.empty
print(f"✓ DataFrame prepared with shape: {df.shape}")

metrics = analytics.get_dashboard_metrics(df)
print(f"✓ Dashboard metrics: {metrics}")

pie = analytics.create_category_pie_chart(df, "this_month")
trend = analytics.create_trend_chart(df, "this_month")
insights = analytics.generate_spending_insights(df)
print(f"✓ Charts & Insights generated (pie: {pie is not None}, trend: {trend is not None}, insights count: {len(insights)})")

# 5. Test Wallet
w_summary = database.get_wallet_summary()
print(f"✓ Wallet Summary: {w_summary}")

# 6. Test Goals
user_id = database.get_current_user_id()
test_goals = database.get_user_goals(user_id)
print(f"✓ User goals count: {len(test_goals)}")

# 7. Clean up test expense
database.delete_expense(expense_id)
print(f"✓ Cleaned up test expense. Current expenses count: {len(database.get_all_expenses())}")

print("========================================")
print("ALL CHECKS PASSED PERFECTLY!")
print("========================================")
