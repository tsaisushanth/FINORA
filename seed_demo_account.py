"""
One-Time Demo Account Seed Script for FINORA.

Creates or seeds the demo student account:
- Email: demo@finora.app
- Password: FinoraDemo@2026

Profile:
- Name: Ananya Sharma
- College: National Institute of Technology
- Course: B.Tech Computer Science
- Year: 2
- Income: 15000, Budget: 10000, Savings: 3000
- Goal: Buy a Laptop (₹70,000 by 2027-06-30)

Expenses:
- ~18-20 realistic student expenses across recent weeks in various categories.
"""

import os
import sys
import datetime
from typing import Optional

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import supabase_client as sc
from supabase import create_client, Client

DEMO_EMAIL = "demo@finora.app"
DEMO_PASSWORD = "FinoraDemo@2026"

SAMPLE_EXPENSES = [
    # Food
    {"category": "Food", "amount": 180.0, "note": "College canteen lunch with friends", "days_ago": 1, "payment_method": "UPI"},
    {"category": "Food", "amount": 320.0, "note": "Dinner & dessert at cafe", "days_ago": 3, "payment_method": "UPI"},
    {"category": "Food", "amount": 120.0, "note": "Evening snacks & chai", "days_ago": 5, "payment_method": "Cash"},
    {"category": "Food", "amount": 250.0, "note": "Hostel mess special meal", "days_ago": 9, "payment_method": "UPI"},
    {"category": "Food", "amount": 150.0, "note": "Juice & sandwich break", "days_ago": 14, "payment_method": "UPI"},
    
    # Transport
    {"category": "Transport", "amount": 120.0, "note": "Metro smartcard recharge", "days_ago": 2, "payment_method": "UPI"},
    {"category": "Transport", "amount": 80.0, "note": "Auto rickshaw to campus library", "days_ago": 7, "payment_method": "Cash"},
    {"category": "Transport", "amount": 200.0, "note": "Cab ride back from city center", "days_ago": 12, "payment_method": "UPI"},

    # Education
    {"category": "Education", "amount": 750.0, "note": "Operating Systems textbook & notes", "days_ago": 4, "payment_method": "UPI"},
    {"category": "Education", "amount": 500.0, "note": "Coding contest registration & lab printouts", "days_ago": 11, "payment_method": "Card"},
    {"category": "Education", "amount": 300.0, "note": "Notebooks & stationery supplies", "days_ago": 18, "payment_method": "Cash"},

    # Shopping
    {"category": "Shopping", "amount": 1200.0, "note": "College festival outfit & shoes", "days_ago": 6, "payment_method": "Card"},
    {"category": "Shopping", "amount": 900.0, "note": "Backpack & laptop sleeve replacement", "days_ago": 16, "payment_method": "UPI"},

    # Entertainment
    {"category": "Entertainment", "amount": 400.0, "note": "Weekend movie tickets with batchmates", "days_ago": 8, "payment_method": "UPI"},
    {"category": "Entertainment", "amount": 250.0, "note": "Board game cafe with study group", "days_ago": 15, "payment_method": "UPI"},

    # Bills
    {"category": "Bills", "amount": 399.0, "note": "Monthly 5G mobile data plan", "days_ago": 10, "payment_method": "UPI"},

    # Travel
    {"category": "Travel", "amount": 850.0, "note": "Train ticket for weekend home visit", "days_ago": 13, "payment_method": "Card"},
    {"category": "Travel", "amount": 600.0, "note": "Bus fare return journey", "days_ago": 17, "payment_method": "UPI"},

    # Other
    {"category": "Other", "amount": 150.0, "note": "Laundry & hostel maintenance", "days_ago": 19, "payment_method": "Cash"},
]


def seed_demo():
    print("=" * 60)
    print("FINORA ONE-TIME DEMO ACCOUNT SEEDING")
    print("=" * 60)
    
    sc._load_dotenv()
    url = sc.get_supabase_url()
    anon_key = sc.get_anon_key()
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    
    print(f"Supabase URL: {url}")
    print(f"Anon/Publishable Key: {'Configured' if anon_key else 'Missing'}")
    print(f"Service Role Key: {'Provided' if service_role_key else 'Not provided'}")

    user_id = None
    access_token = None

    # Step 1: Try Admin API if Service Role Key is available
    if service_role_key:
        print("\n[Method 1] Attempting Supabase Admin Client with Service-Role Key...")
        try:
            admin_client: Client = create_client(url, service_role_key)
            # Check if user already exists
            list_res = admin_client.auth.admin.list_users()
            users_list = getattr(list_res, "users", []) or []
            existing_user = next((u for u in users_list if getattr(u, "email", "") == DEMO_EMAIL), None)
            
            if existing_user:
                user_id = existing_user.id
                print(f"Demo user already exists in auth.users (ID: {user_id}).")
                # Update password just in case
                admin_client.auth.admin.update_user_by_id(
                    user_id,
                    {"password": DEMO_PASSWORD, "email_confirm": True}
                )
                print("Confirmed demo user password & email confirmation status.")
            else:
                create_res = admin_client.auth.admin.create_user({
                    "email": DEMO_EMAIL,
                    "password": DEMO_PASSWORD,
                    "email_confirm": True
                })
                new_user = getattr(create_res, "user", None)
                user_id = getattr(new_user, "id", None)
                print(f"Successfully created demo user via Admin API (ID: {user_id})!")
        except Exception as exc:
            print(f"Admin API creation notice: {exc}")

    # Step 2: Authenticate as the demo user using the standard client
    print(f"\n[Step 2] Authenticating as {DEMO_EMAIL}...")
    client = sc.create_supabase_client()
    try:
        sign_in_res = client.auth.sign_in_with_password({"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
        user = sign_in_res.user
        session = sign_in_res.session
        user_id = user.id
        access_token = session.access_token
        print(f"Successfully signed in! User ID: {user_id}")
    except Exception as exc:
        print(f"Sign-in with password attempt: {exc}")
        if not user_id:
            # Try sign_up
            print("Attempting standard sign_up...")
            try:
                su_res = client.auth.sign_up({"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
                user = su_res.user
                session = su_res.session
                if user:
                    user_id = user.id
                if session:
                    access_token = session.access_token
                print(f"Sign up returned user ID: {user_id}, session: {bool(session)}")
            except Exception as e_su:
                print(f"Sign up error: {e_su}")

    if not user_id:
        print("\n" + "!" * 60)
        print("ACTION REQUIRED:")
        print("The demo user could not be created because Supabase rate-limited signups.")
        print("To bypass this instantly, supply your SUPABASE_SERVICE_ROLE_KEY:")
        print("1. Open your Supabase Dashboard -> Project Settings -> API")
        print("2. Copy the 'service_role' secret key.")
        print("3. Run the seed script with the key:")
        print("   $env:SUPABASE_SERVICE_ROLE_KEY='your_service_role_key_here'; .\\.venv\\Scripts\\python.exe seed_demo_account.py")
        print("!" * 60)
        return False

    # Step 3: Seed Profile
    print(f"\n[Step 3] Seeding profile in public.profiles for ID: {user_id}...")
    profile_payload = {
        "id": user_id,
        "name": "Ananya Sharma",
        "email": DEMO_EMAIL,
        "college": "National Institute of Technology",
        "course": "B.Tech Computer Science",
        "year": 2,
        "monthly_income": 15000.0,
        "monthly_budget": 10000.0,
        "monthly_savings_target": 3000.0,
        "primary_goal": "Buy a Laptop",
        "goal_amount": 70000.0,
        "goal_deadline": "2027-06-30"
    }

    # Upsert profile via admin client or authenticated user client
    target_client = sc.create_supabase_client(access_token) if access_token else create_client(url, service_role_key)
    try:
        # Check existing profile
        p_res = target_client.table("profiles").select("*").eq("id", user_id).execute()
        existing_p = getattr(p_res, "data", []) or []
        if existing_p:
            print("Profile already exists. Updating fields...")
            target_client.table("profiles").update(profile_payload).eq("id", user_id).execute()
        else:
            print("Inserting new profile...")
            target_client.table("profiles").insert(profile_payload).execute()
        print("Profile saved successfully in public.profiles!")
    except Exception as e_p:
        print(f"Profile upsert error: {e_p}")

    # Step 4: Seed Sample Expenses
    print(f"\n[Step 4] Seeding sample expenses in public.expenses for ID: {user_id}...")
    try:
        # Check existing expenses for demo user
        exp_res = target_client.table("expenses").select("id").eq("user_id", user_id).execute()
        existing_expenses = getattr(exp_res, "data", []) or []
        print(f"Found {len(existing_expenses)} existing expenses for demo user.")

        if len(existing_expenses) >= 10:
            print("Demo account already has sufficient expenses. Skipping duplicate insertion.")
        else:
            today = datetime.date.today()
            to_insert = []
            for item in SAMPLE_EXPENSES:
                exp_date = (today - datetime.timedelta(days=item["days_ago"])).strftime("%Y-%m-%d")
                exp_time = "14:30:00"
                to_insert.append({
                    "user_id": user_id,
                    "amount": item["amount"],
                    "category": item["category"],
                    "note": item["note"],
                    "expense_date": exp_date,
                    "expense_time": exp_time,
                    "payment_method": item["payment_method"]
                })
            
            print(f"Inserting {len(to_insert)} realistic student expenses...")
            target_client.table("expenses").insert(to_insert).execute()
            print("Sample expenses inserted successfully!")
    except Exception as e_exp:
        print(f"Expenses insertion error: {e_exp}")

    print("\n" + "=" * 60)
    print("DEMO ACCOUNT SEEDING COMPLETE!")
    print(f"Email:    {DEMO_EMAIL}")
    print(f"Password: {DEMO_PASSWORD}")
    print("=" * 60)
    return True


if __name__ == "__main__":
    seed_demo()
