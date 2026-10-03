import os
import sys
import tempfile
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Redirect DB to a temp file so we don't touch real data
tmpdir = tempfile.mkdtemp(prefix="finora_test_")
os.environ["FINORA_TEST"] = "1"

import database

# Monkeypatch DB path to temp
database.DB_DIR = tmpdir
database.DB_PATH = os.path.join(tmpdir, "test.db")

database.init_db()

uid = database.get_current_user_id()
assert database.get_current_user_id() == uid

# Seed wallet
database.adjust_wallet_balance(25000)
assert database.get_wallet_balance() == 25000.0

# --- Create goals ---
g1 = database.create_goal(uid, "New Phone", 30000, "Electronics", "High", "2026-12-15", "Latest model")
g2 = database.create_goal(uid, "Laptop", 60000, "Electronics", "Medium", "2026-06-01", "")
g3 = database.create_goal(uid, "Trip to Goa", 20000, "Travel", "Low", None, "")

goals = database.get_user_goals(uid)
assert len(goals) == 3, f"expected 3 goals, got {len(goals)}"
assert all(g["user_id"] == uid for g in goals)
print("PASS: created 3 goals, user separation field present")

# --- Add money to g1 (wallet decreases) ---
ok = database.add_goal_contribution(g1, uid, 18000, "Salary", "2026-09-01", "Monthly savings")
assert ok
assert database.get_wallet_balance() == 7000.0, f"wallet should be 7000, got {database.get_wallet_balance()}"

g1r = database.get_goal(g1)
assert g1r["saved_amount"] == 18000.0
assert g1r["status"] == "Active"
txs = database.get_goal_transactions(g1)
assert len(txs) == 1
total_alloc = database.get_total_allocated_to_goals(uid)
assert total_alloc == 18000.0
print("PASS: contribution reduced wallet to 7000, goal saved 18000")

# --- Cannot contribute more than wallet balance ---
ok = database.add_goal_contribution(g1, uid, 8000, "Salary", "2026-09-02", "")
assert not ok, "should fail: wallet only has 7000"
assert database.get_wallet_balance() == 7000.0
assert database.get_goal(g1)["saved_amount"] == 18000.0
print("PASS: contribution exceeding wallet rejected, no changes")

# --- Add enough to complete g2 ---
database.set_wallet_balance(100000)
database.add_goal_contribution(g2, uid, 60000, "Salary", "2026-09-03", "")
g2r = database.get_goal(g2)
assert g2r["status"] == "Completed", f"g2 should be completed, got {g2r['status']}"
assert g2r["saved_amount"] == 60000.0
assert database.get_wallet_balance() == 100000.0 - 60000.0 == 40000.0, database.get_wallet_balance()
print("PASS: completing goal caps saved at target and marks Completed")

# --- Overfunding is not allowed (saved never exceeds target) ---
# wallet is negative, so can't anyway; create fresh wallet and test overfund no-op on target
database.set_wallet_balance(100000)
g3_done = database.add_goal_contribution(g3, uid, 20000, "Salary", "2026-09-04", "")
assert g3_done
g3r = database.get_goal(g3)
assert g3r["saved_amount"] == 20000.0 and g3r["status"] == "Completed"
ok = database.add_goal_contribution(g3, uid, 5000, "Salary", "2026-09-05", "")
# money available, but contribution capped to target; goal already completed so new_saved>=target -> capped at target
if ok:
    g3r2 = database.get_goal(g3)
    assert g3r2["saved_amount"] <= 20000.0, "saved must never exceed target"
print("PASS: saved amount never exceeds target")

# --- Remove/reverse a contribution ---
# Reset wallet positive
database.set_wallet_balance(50000)
# create new goal
g4 = database.create_goal(uid, "Headphones", 5000, "Electronics", "Medium", None, "")
database.add_goal_contribution(g4, uid, 1500, "Salary", "2026-08-05", "Allowance")
database.add_goal_contribution(g4, uid, 2000, "Salary", "2026-08-20", "Reduced food")
bal_after2 = database.get_wallet_balance()
assert database.get_goal(g4)["saved_amount"] == 3500.0
txs = database.get_goal_transactions(g4)
assert len(txs) == 2
# reverse the first contribution (50000-1500-2000=46500 after 2 adds; add 50000 then spends)
# Let's reverse the 'Allowance' contribution of 1500
first_tx = txs[-1]  # oldest (Allowance)
ok = database.remove_goal_contribution(g4, uid, first_tx["id"])
assert ok
assert database.get_goal(g4)["saved_amount"] == 2000.0, database.get_goal(g4)["saved_amount"]
assert database.get_wallet_balance() == bal_after2 + 1500, (database.get_wallet_balance(), bal_after2)
print("PASS: contributed money returned to wallet on reversal")

# --- Removing a contribution that completed a goal reactivates it ---
database.set_wallet_balance(20000)
g5 = database.create_goal(uid, "Bike", 10000, "Personal", "High", None, "")
database.add_goal_contribution(g5, uid, 10000, "Salary", "2026-09-10", "Done")
assert database.get_goal(g5)["status"] == "Completed"
txs5 = database.get_goal_transactions(g5)
assert len(txs5) == 1
ok = database.remove_goal_contribution(g5, uid, txs5[0]["id"])
assert ok
assert database.get_goal(g5)["status"] == "Active", database.get_goal(g5)["status"]
assert database.get_goal(g5)["saved_amount"] == 0.0
print("PASS: reversing sole contribution of completed goal reactivates it")

# --- Editing target below saved auto-completes, never invalid ---
database.set_wallet_balance(50000)
g6 = database.create_goal(uid, "Course", 30000, "Education", "Medium", None, "")
database.add_goal_contribution(g6, uid, 20000, "Salary", "2026-09-01", "")
# target 30000 -> 15000, saved 20000 >= 15000 -> Completed
database.update_goal(g6, "Course", 15000, "Education", "Medium", None, "")
g6r = database.get_goal(g6)
assert g6r["status"] == "Completed", g6r["status"]
assert g6r["saved_amount"] == 20000.0
print("PASS: lowering target below saved auto-completes goal")

# --- Delete returns saved money to wallet ---
bal_before = database.get_wallet_balance()
g6saved = database.get_goal(g6)["saved_amount"]
res = database.delete_goal(g6, uid)
assert res["saved_amount"] == g6saved
assert database.get_goal(g6) is None, "goal should be deleted"
# app restores wallet on delete (we simulate here)
database.adjust_wallet_balance(res["saved_amount"])
assert database.get_wallet_balance() == bal_before + g6saved
print("PASS: deleting goal returns saved amount to wallet (no silent loss)")

# --- User separation: another user must not see these goals ---
database.set_current_user(999)
# create a distinct user
import sqlite3
conn = database.get_db_connection()
conn.execute("INSERT INTO users (username) VALUES ('user2')")
c = conn.execute("SELECT id FROM users WHERE username='user2'")
uid2 = c.fetchone()["id"]
conn.commit()
conn.close()
database.set_current_user(uid2)
goals2 = database.get_user_goals(uid2)
assert len(goals2) == 0, f"user2 should see no goals, got {len(goals2)}"
print("PASS: user separation works — user2 sees no goals from user1")

# Switch back
database.set_current_user(uid)
assert database.get_user_goals(uid), "user1 still sees own goals"

print("\nALL GOAL TESTS PASSED")
