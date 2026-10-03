import sys
import os
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    init_db,
    set_wallet_balance,
    get_wallet_balance,
    add_money_transaction,
    lend_money,
    borrow_money,
    receive_lent_repayment,
    repay_borrowed_loan,
    get_wallet_summary,
    get_active_lent_records,
    get_active_borrowed_records,
    get_wallet_transaction_history,
    add_expense,
    delete_expense
)

def run_tests():
    print("--- 1. Init DB & Negative Wallet Balance Test ---")
    init_db()
    
    # Set starting balance to negative -200.0
    set_wallet_balance(-200.0)
    bal = get_wallet_balance()
    print(f"Negative balance test: Rs. {bal}")
    assert bal == -200.0, f"Expected -200.0, got {bal}"
    
    s1 = get_wallet_summary()
    assert s1["available_wallet"] == -200.0
    assert s1["net_worth"] == -200.0

    print("--- 2. Add Money Test ---")
    tx1 = add_money_transaction(1000.0, "Salary", "2026-08-19", "Monthly salary")
    s2 = get_wallet_summary()
    print("Summary after Add Money:", s2)
    assert s2["available_wallet"] == 800.0
    assert s2["net_worth"] == 800.0

    print("--- 3. Lend Money Test ---")
    lent_id = lend_money("Rahul", 500.0, "2026-08-19", "2026-08-25", "Dinner share")
    s3 = get_wallet_summary()
    print("Summary after Lend Money:", s3)
    assert s3["available_wallet"] == 300.0
    assert s3["money_to_receive"] == 500.0
    assert s3["net_worth"] == 800.0  # Net worth unchanged!

    print("--- 4. Borrow Money Test ---")
    borrow_id = borrow_money("Priya", 400.0, "2026-08-19", "2026-08-30", "Emergency loan")
    s4 = get_wallet_summary()
    print("Summary after Borrow Money:", s4)
    assert s4["available_wallet"] == 700.0
    assert s4["money_borrowed"] == 400.0
    assert s4["net_worth"] == 800.0  # Net worth unchanged!

    print("--- 5. Repayment Received Test (Partial & Full) ---")
    # Partial repayment from Rahul (200.0 out of 500.0)
    ok1 = receive_lent_repayment(lent_id, 200.0, "2026-08-19", "Partial cash back")
    assert ok1
    s5_partial = get_wallet_summary()
    print("Summary after Partial Lent Repayment:", s5_partial)
    assert s5_partial["available_wallet"] == 900.0
    assert s5_partial["money_to_receive"] == 300.0
    
    active_l = get_active_lent_records()
    assert len(active_l) == 1
    assert active_l[0]["status"] == "Partially Paid"

    # Full remaining repayment from Rahul (300.0)
    ok2 = receive_lent_repayment(lent_id, 300.0, "2026-08-19", "Final payment")
    assert ok2
    s5_full = get_wallet_summary()
    print("Summary after Full Lent Repayment:", s5_full)
    assert s5_full["available_wallet"] == 1200.0
    assert s5_full["money_to_receive"] == 0.0
    assert len(get_active_lent_records()) == 0

    print("--- 6. Loan Repayment Made Test (Partial & Full) ---")
    # Partial repayment to Priya (200.0 out of 400.0)
    ok3 = repay_borrowed_loan(borrow_id, 200.0, "2026-08-19", "Partial UPI transfer")
    assert ok3
    s6_partial = get_wallet_summary()
    print("Summary after Partial Loan Repayment:", s6_partial)
    assert s6_partial["available_wallet"] == 1000.0
    assert s6_partial["money_borrowed"] == 200.0

    # Full remaining repayment to Priya (200.0)
    ok4 = repay_borrowed_loan(borrow_id, 200.0, "2026-08-19", "Settled full loan")
    assert ok4
    s6_full = get_wallet_summary()
    print("Summary after Full Loan Repayment:", s6_full)
    assert s6_full["available_wallet"] == 800.0
    assert s6_full["money_borrowed"] == 0.0
    assert len(get_active_borrowed_records()) == 0

    print("--- 7. Existing Expenses Test ---")
    exp_id = add_expense(150.0, "Food", "Lunch", "2026-08-19", "13:00:00", "Cash")
    s7 = get_wallet_summary()
    assert s7["available_wallet"] == 650.0
    
    delete_expense(exp_id)
    s7_del = get_wallet_summary()
    assert s7_del["available_wallet"] == 800.0

    print("--- 8. Transaction History Query Test ---")
    history = get_wallet_transaction_history()
    print(f"Total transactions logged: {len(history)}")
    assert len(history) >= 6

    # Cleanup DB test state
    set_wallet_balance(0.0)
    print("--- ALL WALLET V2 TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    run_tests()
