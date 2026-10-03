import datetime
from database import (
    init_db,
    add_expense,
    get_all_expenses,
    delete_expense,
    get_wallet_summary,
    get_wallet_balance
)

# Ensure init_db runs smoothly
init_db()

summary_before = get_wallet_summary()
print("Initial Summary:", summary_before)
assert summary_before["available_wallet"] == 0.0
assert summary_before["money_to_receive"] == 0.0
assert summary_before["money_borrowed"] == 0.0
assert summary_before["net_worth"] == 0.0
assert len(get_all_expenses()) == 0

# Step 10: Add a small test expense
today = datetime.date.today().strftime("%Y-%m-%d")
exp_id = add_expense(
    amount=50.0,
    category="Food",
    note="Test expense",
    expense_date=today,
    expense_time="12:00:00",
    payment_method="Cash"
)
print(f"Added test expense ID: {exp_id}")

expenses = get_all_expenses()
print("Expenses after add:", expenses)
assert len(expenses) == 1
assert expenses[0]["amount"] == 50.0
assert expenses[0]["category"] == "Food"

# Step 11: Remove the test expense so the application is completely empty again
success = delete_expense(exp_id)
print("Deleted expense success:", success)
assert success is True

summary_after = get_wallet_summary()
print("Summary after delete:", summary_after)
assert summary_after["available_wallet"] == 0.0
assert len(get_all_expenses()) == 0

print("Verification test passed successfully!")
