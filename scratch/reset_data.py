import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "expenses.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Clear user financial tables
cursor.execute("DELETE FROM expenses")
cursor.execute("DELETE FROM wallet_transactions")
cursor.execute("DELETE FROM money_lent")
cursor.execute("DELETE FROM money_borrowed")

# Reset wallet_balance in settings table to 0.0
cursor.execute("INSERT INTO settings (key, value) VALUES ('wallet_balance', '0.0') ON CONFLICT(key) DO UPDATE SET value = '0.0'")

# Reset autoincrement sequence counters if sqlite_sequence table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
if cursor.fetchone():
    cursor.execute("DELETE FROM sqlite_sequence")

conn.commit()
conn.close()
print("Successfully cleared all user financial data from expenses.db while preserving schema.")
