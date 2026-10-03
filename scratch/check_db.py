import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "expenses.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

VALID_TABLES = {"expenses", "settings", "wallet_transactions", "money_lent", "money_borrowed"}

tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables in DB:", tables)

for t in tables:
    table_name = t[0]
    if table_name not in VALID_TABLES:
        print(f"Skipping unknown table: {table_name}")
        continue
    count = c.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()[0]
    print(f"Table '{table_name}' count: {count}")
    cursor_rows = c.execute(f"SELECT * FROM [{table_name}] LIMIT 5").fetchall()
    print(f"Sample rows for '{table_name}':", cursor_rows)

conn.close()
