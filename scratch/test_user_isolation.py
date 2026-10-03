import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
import supabase_client as sc
import auth
import profiles
from supabase_client import create_supabase_client

def run_test():
    print("=== Testing Real Multi-User Authentication + User Profiles + Expenses Isolation ===")
    
    url = sc.get_supabase_url()
    anon_key = sc.get_anon_key()
    print(f"Supabase URL: {url}")
    print(f"Supabase Key configured: {bool(anon_key)}")
    
    # Generate unique test accounts
    tag = uuid.uuid4().hex[:6]
    email_a = f"student_a_{tag}@finoratest.org"
    password_a = "FinoraPass123!"
    
    email_b = f"student_b_{tag}@finoratest.org"
    password_b = "FinoraPass123!"
    
    print(f"\n1. Creating User A: {email_a}")
    client = create_supabase_client()
    try:
        res_a = client.auth.sign_up({"email": email_a, "password": password_a})
        user_a = res_a.user
        session_a = res_a.session
        print(f"User A created: id={user_a.id if user_a else None}, session={bool(session_a)}")
    except Exception as e:
        print(f"Sign up A result/error: {e}")
        return

    # If Supabase email confirmation is disabled, we have a session. If not, we test with sign_in
    if not session_a:
        try:
            res_in_a = client.auth.sign_in_with_password({"email": email_a, "password": password_a})
            session_a = res_in_a.session
            user_a = res_in_a.user
        except Exception as e:
            print(f"Sign in A notice (confirm email may be required in Supabase settings): {e}")
            
    if session_a:
        token_a = session_a.access_token
        uid_a = user_a.id
        print(f"User A authenticated. UUID = {uid_a}")
        
        # Test Profile Creation for User A
        print("\n2. Creating Profile for User A...")
        auth_session_a = auth.AuthSession(user_id=uid_a, email=email_a, access_token=token_a)
        profile_data_a = {
            "name": f"Student A {tag}",
            "college": "IIT Bombay",
            "course": "Computer Science",
            "year": 3,
            "monthly_income": 20000.0,
            "monthly_budget": 12000.0,
            "monthly_savings_target": 8000.0,
            "primary_goal": "Laptop",
            "goal_amount": 75000.0,
            "goal_deadline": "2026-12-31"
        }
        
        saved_p_a = profiles.save_my_profile(auth_session_a, profile_data_a)
        print(f"Saved Profile A: id={saved_p_a.id}, name={saved_p_a.name}, email={saved_p_a.email}")
        assert saved_p_a.id == uid_a, f"Profile ID ({saved_p_a.id}) must equal auth.users ID ({uid_a})"
        
        # Test Adding Expense for User A
        print("\n3. Adding Expense for User A (₹500 Food)...")
        exp_a = sc.insert_expense(
            access_token=token_a,
            user_id=uid_a,
            expense_data={
                "amount": 500.0,
                "category": "Food",
                "note": "Lunch with friends",
                "expense_date": "2026-10-03",
                "payment_method": "UPI"
            }
        )
        print(f"Added expense for User A: {exp_a}")
        
        # Query expenses for User A
        expenses_a = sc.fetch_expenses(token_a, uid_a)
        print(f"Fetched User A expenses: count={len(expenses_a)}")
        assert len(expenses_a) >= 1
        assert expenses_a[0]["amount"] == 500.0
        
        # Test User B
        print(f"\n4. Creating User B: {email_b}")
        res_b = client.auth.sign_up({"email": email_b, "password": password_b})
        user_b = res_b.user
        session_b = res_b.session
        if not session_b:
            try:
                res_in_b = client.auth.sign_in_with_password({"email": email_b, "password": password_b})
                session_b = res_in_b.session
                user_b = res_in_b.user
            except Exception as e:
                print(f"Sign in B notice: {e}")
                
        if session_b:
            token_b = session_b.access_token
            uid_b = user_b.id
            print(f"User B authenticated. UUID = {uid_b}")
            
            # Verify User B does NOT have User A's profile
            auth_session_b = auth.AuthSession(user_id=uid_b, email=email_b, access_token=token_b)
            profile_b_initial = profiles.fetch_my_profile(auth_session_b)
            print(f"User B initial profile (should be None): {profile_b_initial}")
            assert profile_b_initial is None, "User B must not see User A's profile!"
            
            # Create User B Profile
            profile_data_b = {
                "name": f"Student B {tag}",
                "college": "BITS Pilani",
                "course": "Economics",
                "year": 2,
                "monthly_income": 15000.0,
                "monthly_budget": 9000.0,
                "monthly_savings_target": 6000.0,
                "primary_goal": "Semester Trip",
                "goal_amount": 30000.0,
                "goal_deadline": "2026-11-30"
            }
            saved_p_b = profiles.save_my_profile(auth_session_b, profile_data_b)
            print(f"Saved Profile B: id={saved_p_b.id}, name={saved_p_b.name}")
            
            # Verify User B expenses (should be EMPTY, must NOT see User A's ₹500)
            expenses_b = sc.fetch_expenses(token_b, uid_b)
            print(f"Fetched User B expenses: count={len(expenses_b)}, data={expenses_b}")
            assert len(expenses_b) == 0, f"User B must have 0 expenses, but found {len(expenses_b)}!"
            
            # Now add an expense for User B (₹1200 Books)
            print("\n5. Adding Expense for User B (₹1200 Books)...")
            sc.insert_expense(
                access_token=token_b,
                user_id=uid_b,
                expense_data={
                    "amount": 1200.0,
                    "category": "Education",
                    "note": "Semester textbooks",
                    "expense_date": "2026-10-03",
                    "payment_method": "Card"
                }
            )
            expenses_b_updated = sc.fetch_expenses(token_b, uid_b)
            print(f"User B expenses after addition: count={len(expenses_b_updated)}")
            assert len(expenses_b_updated) == 1
            assert expenses_b_updated[0]["amount"] == 1200.0
            
            # Re-fetch User A's expenses to confirm User A still has ONLY their ₹500 expense
            print("\n6. Verifying User A expenses again...")
            expenses_a_recheck = sc.fetch_expenses(token_a, uid_a)
            print(f"User A expenses rechecked: count={len(expenses_a_recheck)}")
            assert len(expenses_a_recheck) == 1
            assert expenses_a_recheck[0]["amount"] == 500.0
            
            print("\n✅ ALL USER ISOLATION AND AUTHENTICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_test()
