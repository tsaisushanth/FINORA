import os
import sys
sys.path.insert(0, os.path.abspath("."))

import supabase_client as sc

print("Testing Supabase Live Connection...")
print("Configured URL:", sc.get_supabase_url())
print("Configured Anon Key:", sc.get_anon_key()[:12] + "..." if sc.get_anon_key() else "None")
print("is_configured():", sc.is_configured())

client = sc.create_supabase_client()
print("Client created successfully:", client)

# Test querying public.profiles
try:
    res = client.table("profiles").select("id, name, email").limit(1).execute()
    print("Query public.profiles successful! Rows returned:", len(res.data))
except Exception as e:
    print("Query profiles error:", e)

# Test querying public.expenses
try:
    res_exp = client.table("expenses").select("id, amount, category").limit(1).execute()
    print("Query public.expenses successful! Rows returned:", len(res_exp.data))
except Exception as e:
    print("Query expenses error:", e)
