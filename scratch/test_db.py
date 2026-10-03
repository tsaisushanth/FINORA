import sys
import os
import datetime

# Add root folder to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    init_db,
    add_expense,
    get_all_expenses,
    get_filtered_expenses,
    delete_expense,
    get_wallet_balance,
    set_wallet_balance
)
from analytics import prepare_dataframe, get_dashboard_metrics, generate_spending_insights

def run_tests():
    print("--- 1. Testing DB Initialization ---")
    init_db()
    
    print("--- 2. Setting Starting Wallet Balance ---")
    set_wallet_balance(5000.0)
    bal = get_wallet_balance()
    assert bal == 5000.0, f"Expected 5000.0, got {bal}"
    print(f"Wallet balance set to: Rs. {bal}")

    print("--- 3. Adding Test Expense ---")
    exp_id1 = add_expense(
        amount=120.0,
        category="Food",
        note="Lunch test",
        expense_date=datetime.date.today().strftime("%Y-%m-%d"),
        expense_time="12:30:00",
        payment_method="UPI"
    )
    print(f"Added expense ID: {exp_id1}")
    
    bal_after = get_wallet_balance()
    print(f"Wallet balance after expense: Rs. {bal_after}")
    assert bal_after == 4880.0, f"Expected 4880.0, got {bal_after}"

    exp_id2 = add_expense(
        amount=450.0,
        category="Transportation",
        note="Taxi test",
        expense_date=datetime.date.today().strftime("%Y-%m-%d"),
        expense_time="14:00:00",
        payment_method="Card"
    )
    print(f"Added second expense ID: {exp_id2}")
    bal_after2 = get_wallet_balance()
    assert bal_after2 == 4430.0, f"Expected 4430.0, got {bal_after2}"

    print("--- 4. Querying Expenses & Metrics ---")
    expenses = get_all_expenses()
    assert len(expenses) == 2, f"Expected 2 expenses, got {len(expenses)}"
    
    df = prepare_dataframe(expenses)
    metrics = get_dashboard_metrics(df)
    print("Dashboard Metrics:", metrics)
    assert metrics["spent_this_month"] == 570.0
    
    insights = generate_spending_insights(df)
    print(f"Generated {len(insights)} Insights.")

    print("--- 5. Testing Delete & Refund ---")
    deleted = delete_expense(exp_id1)
    assert deleted, "Failed to delete expense 1"
    bal_restored = get_wallet_balance()
    print(f"Wallet balance after deleting expense 1: Rs. {bal_restored}")
    assert bal_restored == 4550.0, f"Expected 4550.0, got {bal_restored}"

    # Cleanup test data so DB is left clean
    delete_expense(exp_id2)
    set_wallet_balance(0.0)
    print("--- ALL TESTS PASSED SUCCESSFULLY! DB cleaned up. ---")

if __name__ == "__main__":
    run_tests()
