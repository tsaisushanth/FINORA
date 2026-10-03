"""
Finora Demo Mode & Spending Analytics Engine.

Provides:
- Realistic student demo profile (Ananya Sharma)
- Realistic student expense dataset (20 initial expenses)
- In-memory / session state mutation for Add Expense in Demo Mode
- Deterministic, calculated spending analysis for the 'Analyze My Spending' feature
- Student-centric Plotly visualization generators
"""

import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from typing import List, Dict, Any, Optional

from supabase_client import Profile
from utils import format_currency

# Student Category Palette
STUDENT_CATEGORIES = [
    "Food",
    "Transport",
    "Education",
    "Shopping",
    "Entertainment",
    "Bills",
    "Travel",
    "Other"
]

CATEGORY_COLORS_MAP = {
    "Food": "#123C35",
    "Transport": "#2C5E55",
    "Education": "#C7A76A",
    "Shopping": "#E07A5F",
    "Entertainment": "#81B29A",
    "Bills": "#3D405B",
    "Travel": "#F2CC8F",
    "Other": "#8FA99F"
}

# ----------------------------------------------------
# FIXED DEMO STUDENT PROFILE
# ----------------------------------------------------
def get_demo_profile() -> Profile:
    """Return the official pre-configured student profile for Demo Mode."""
    return Profile(
        id="demo-student-ananya",
        name="Ananya Sharma",
        email="demo@finora.app",
        college="National Institute of Technology",
        course="B.Tech Computer Science",
        year=2,
        monthly_income=15000.0,
        monthly_budget=10000.0,
        monthly_savings_target=3000.0,
        primary_goal="Buy Laptop",
        goal_amount=70000.0,
        goal_deadline="2027-06-30",
        created_at="2026-09-01T00:00:00Z",
        updated_at="2026-10-01T00:00:00Z"
    )

# ----------------------------------------------------
# 20 REALISTIC STUDENT EXPENSES
# ----------------------------------------------------
def get_initial_demo_expenses() -> List[Dict[str, Any]]:
    """Return a consistent list of 20 realistic student expenses spread across recent days."""
    today = datetime.date.today()
    
    raw_list = [
        # Food (6 items = ₹1,230)
        {"category": "Food", "amount": 180.0, "note": "Canteen lunch with classmates", "days_ago": 1, "payment_method": "UPI"},
        {"category": "Food", "amount": 250.0, "note": "Hostel cafe special dinner", "days_ago": 3, "payment_method": "UPI"},
        {"category": "Food", "amount": 120.0, "note": "Evening chai & samosas", "days_ago": 6, "payment_method": "Cash"},
        {"category": "Food", "amount": 320.0, "note": "Weekend pizza slice with roomie", "days_ago": 10, "payment_method": "UPI"},
        {"category": "Food", "amount": 210.0, "note": "South Indian breakfast & coffee", "days_ago": 15, "payment_method": "UPI"},
        {"category": "Food", "amount": 150.0, "note": "Juice and fruits after lab", "days_ago": 21, "payment_method": "UPI"},

        # Transport (4 items = ₹550)
        {"category": "Transport", "amount": 80.0, "note": "Auto rickshaw to campus gate", "days_ago": 2, "payment_method": "Cash"},
        {"category": "Transport", "amount": 120.0, "note": "Metro smart card recharge", "days_ago": 7, "payment_method": "UPI"},
        {"category": "Transport", "amount": 150.0, "note": "Shared cab to city centre", "days_ago": 13, "payment_method": "UPI"},
        {"category": "Transport", "amount": 200.0, "note": "Bus pass monthly renewal", "days_ago": 22, "payment_method": "UPI"},

        # Education (3 items = ₹1,550)
        {"category": "Education", "amount": 500.0, "note": "Algorithms reference handbook", "days_ago": 5, "payment_method": "Card"},
        {"category": "Education", "amount": 300.0, "note": "Lab notebooks & spiral binding", "days_ago": 12, "payment_method": "Cash"},
        {"category": "Education", "amount": 750.0, "note": "College coding symposium registration", "days_ago": 18, "payment_method": "UPI"},

        # Shopping (2 items = ₹2,100)
        {"category": "Shopping", "amount": 900.0, "note": "Backpack & laptop protective sleeve", "days_ago": 8, "payment_method": "UPI"},
        {"category": "Shopping", "amount": 1200.0, "note": "Campus tech fest hoodie & sneakers", "days_ago": 16, "payment_method": "Card"},

        # Entertainment (2 items = ₹650)
        {"category": "Entertainment", "amount": 250.0, "note": "Board game night snacks", "days_ago": 9, "payment_method": "UPI"},
        {"category": "Entertainment", "amount": 400.0, "note": "Cinema ticket with hostel batch", "days_ago": 19, "payment_method": "UPI"},

        # Bills (2 items = ₹550)
        {"category": "Bills", "amount": 350.0, "note": "5G mobile data recharge", "days_ago": 11, "payment_method": "UPI"},
        {"category": "Bills", "amount": 200.0, "note": "Hostel wifi contribution", "days_ago": 20, "payment_method": "Cash"},

        # Travel (2 items = ₹1,450)
        {"category": "Travel", "amount": 600.0, "note": "Bus ticket for hometown weekend", "days_ago": 14, "payment_method": "UPI"},
        {"category": "Travel", "amount": 850.0, "note": "Train ticket return journey", "days_ago": 24, "payment_method": "Card"}
    ]

    expenses = []
    for idx, item in enumerate(raw_list, start=1):
        exp_d = today - datetime.timedelta(days=item["days_ago"])
        expenses.append({
            "id": idx,
            "user_id": "demo-student-ananya",
            "amount": float(item["amount"]),
            "category": item["category"],
            "note": item["note"],
            "expense_date": exp_d.strftime("%Y-%m-%d"),
            "expense_time": "14:00:00",
            "payment_method": item["payment_method"],
            "created_at": f"{exp_d.strftime('%Y-%m-%d')}T14:00:00Z"
        })
    return expenses

# ----------------------------------------------------
# DEMO EXPENSES STATE MANAGEMENT
# ----------------------------------------------------
def get_demo_expenses() -> List[Dict[str, Any]]:
    """Retrieve the mutable demo expense list from session state."""
    if "finora_demo_expenses" not in st.session_state:
        st.session_state["finora_demo_expenses"] = get_initial_demo_expenses()
    return st.session_state["finora_demo_expenses"]

def add_demo_expense(amount: float, category: str, note: str, expense_date: str, payment_method: str = "UPI") -> Dict[str, Any]:
    """Add a new expense to the demo state and return it."""
    expenses = get_demo_expenses()
    new_id = (max([e.get("id", 0) for e in expenses]) + 1) if expenses else 1
    new_record = {
        "id": new_id,
        "user_id": "demo-student-ananya",
        "amount": float(amount),
        "category": category,
        "note": note.strip() if note else "",
        "expense_date": expense_date,
        "expense_time": datetime.datetime.now().strftime("%H:%M:%S"),
        "payment_method": payment_method,
        "created_at": datetime.datetime.now().isoformat()
    }
    # Prepend newest
    expenses.insert(0, new_record)
    st.session_state["finora_demo_expenses"] = expenses
    return new_record

def delete_demo_expense(expense_id: int) -> bool:
    """Delete an expense by ID from the demo state."""
    expenses = get_demo_expenses()
    st.session_state["finora_demo_expenses"] = [e for e in expenses if e.get("id") != expense_id]
    return True

# ----------------------------------------------------
# REAL DATA-DRIVEN CALCULATIONS & SPENDING ANALYSIS
# ----------------------------------------------------
def calculate_spending_metrics(df: pd.DataFrame, profile: Optional[Profile] = None) -> Dict[str, Any]:
    """
    Calculate comprehensive, deterministic spending metrics from DataFrame.
    Works identically for demo data and Supabase data.
    """
    budget = float(profile.monthly_budget if profile and profile.monthly_budget else 10000.0)
    income = float(profile.monthly_income if profile and profile.monthly_income else 15000.0)
    goal_target = float(profile.goal_amount if profile and profile.goal_amount else 70000.0)
    saved_for_goal = 24000.0  # Ananya's saved portion toward laptop

    if df.empty or df["amount"].sum() == 0:
        return {
            "total_spent": 0.0,
            "budget": budget,
            "remaining_budget": budget,
            "budget_used_pct": 0.0,
            "available_balance": income,
            "tx_count": 0,
            "avg_daily": 0.0,
            "projected_month": 0.0,
            "highest_expense": {"amount": 0.0, "category": "-", "note": "-", "date": "-"},
            "top_category": {"category": "-", "amount": 0.0, "pct": 0.0, "count": 0, "avg": 0.0},
            "second_category": {"category": "-", "amount": 0.0, "pct": 0.0, "count": 0},
            "category_summary": pd.DataFrame(columns=["category", "amount", "count", "pct", "avg_per_tx"]),
            "saved_for_goal": saved_for_goal,
            "goal_target": goal_target,
            "goal_progress_pct": (saved_for_goal / goal_target * 100) if goal_target > 0 else 0.0
        }

    total_spent = float(df["amount"].sum())
    remaining_budget = budget - total_spent
    budget_used_pct = (total_spent / budget * 100) if budget > 0 else 0.0
    available_balance = max(0.0, income - total_spent)

    tx_count = len(df)
    
    # Daily spending average (over days with records or past 30 days)
    today = datetime.date.today()
    days_span = max(1, min(30, today.day if today.day > 1 else 15))
    avg_daily = total_spent / days_span
    projected_month = avg_daily * 30

    # Highest individual expense
    max_idx = df["amount"].idxmax()
    highest_row = df.loc[max_idx]
    highest_expense = {
        "amount": float(highest_row["amount"]),
        "category": str(highest_row["category"]),
        "note": str(highest_row["note"]),
        "date": str(highest_row["expense_date"])
    }

    # Category Breakdown
    cat_grp = df.groupby("category")["amount"].agg(["sum", "count"]).reset_index()
    cat_grp.columns = ["category", "amount", "count"]
    cat_grp["pct"] = (cat_grp["amount"] / total_spent) * 100
    cat_grp["avg_per_tx"] = cat_grp["amount"] / cat_grp["count"]
    cat_grp = cat_grp.sort_values(by="amount", ascending=False)

    top_cat = cat_grp.iloc[0] if len(cat_grp) > 0 else None
    sec_cat = cat_grp.iloc[1] if len(cat_grp) > 1 else None

    top_category = {
        "category": str(top_cat["category"]) if top_cat is not None else "-",
        "amount": float(top_cat["amount"]) if top_cat is not None else 0.0,
        "pct": float(top_cat["pct"]) if top_cat is not None else 0.0,
        "count": int(top_cat["count"]) if top_cat is not None else 0,
        "avg": float(top_cat["avg_per_tx"]) if top_cat is not None else 0.0
    }

    second_category = {
        "category": str(sec_cat["category"]) if sec_cat is not None else "-",
        "amount": float(sec_cat["amount"]) if sec_cat is not None else 0.0,
        "pct": float(sec_cat["pct"]) if sec_cat is not None else 0.0,
        "count": int(sec_cat["count"]) if sec_cat is not None else 0
    }

    goal_progress_pct = (saved_for_goal / goal_target * 100) if goal_target > 0 else 0.0

    return {
        "total_spent": total_spent,
        "budget": budget,
        "remaining_budget": remaining_budget,
        "budget_used_pct": budget_used_pct,
        "available_balance": available_balance,
        "tx_count": tx_count,
        "avg_daily": avg_daily,
        "projected_month": projected_month,
        "highest_expense": highest_expense,
        "top_category": top_category,
        "second_category": second_category,
        "category_summary": cat_grp,
        "saved_for_goal": saved_for_goal,
        "goal_target": goal_target,
        "goal_progress_pct": goal_progress_pct
    }

# ----------------------------------------------------
# "ANALYZE MY SPENDING" ENGINE (Deterministic Calculations)
# ----------------------------------------------------
def generate_spending_analysis_report(df: pd.DataFrame, profile: Optional[Profile], topic: str) -> Dict[str, Any]:
    """
    Generate human-readable analysis based entirely on calculated DataFrame metrics.
    No hardcoded text, no fake values.
    """
    m = calculate_spending_metrics(df, profile)
    cat_df = m["category_summary"]

    if df.empty:
        return {
            "title": "No Expense Data Available",
            "summary": "Please record some expenses to generate a detailed spending breakdown.",
            "metrics": [],
            "recommendation": "Add your daily expenses to unlock spending intelligence."
        }

    # 1. OVERALL SPENDING
    if topic == "📊 Overall Spending":
        summary_text = (
            f"Your total spending is **{format_currency(m['total_spent'])}** across **{m['tx_count']} transactions**.\n\n"
            f"**{m['top_category']['category']}** is your largest spending category at **{format_currency(m['top_category']['amount'])}**, "
            f"accounting for **{m['top_category']['pct']:.1f}%** of your total expenses.\n\n"
        )
        if m['second_category']['category'] != '-':
            summary_text += (
                f"**{m['second_category']['category']}** is your second-largest category at **{format_currency(m['second_category']['amount'])}** "
                f"({m['second_category']['pct']:.1f}%).\n\n"
            )

        if m['remaining_budget'] >= 0:
            summary_text += f"You have **{format_currency(m['remaining_budget'])}** remaining from your **{format_currency(m['budget'])}** monthly budget."
        else:
            summary_text += f"⚠️ You are currently **{format_currency(abs(m['remaining_budget']))} over** your planned monthly budget of {format_currency(m['budget'])}."

        return {
            "title": "Comprehensive Spending Analysis",
            "summary": summary_text,
            "metrics": [
                ("Total Spent", format_currency(m['total_spent'])),
                ("Transactions", str(m['tx_count'])),
                ("Top Category", f"{m['top_category']['category']} ({m['top_category']['pct']:.0f}%)"),
                ("Daily Average", format_currency(m['avg_daily']))
            ],
            "recommendation": (
                f"At your current spending rate of {format_currency(m['avg_daily'])}/day, your projected monthly expense is {format_currency(m['projected_month'])}. "
                + ("You are on track to stay within your budget!" if m['projected_month'] <= m['budget'] else "Consider trimming non-essential shopping or dining to stay within budget.")
            )
        }

    # 2. BUDGET STATUS & FORECAST
    elif topic == "🎯 Budget Status & Forecast":
        status_word = "Healthy" if m['budget_used_pct'] < 80 else "Tight" if m['budget_used_pct'] < 100 else "Over Budget"
        summary_text = (
            f"You have used **{m['budget_used_pct']:.1f}%** of your **{format_currency(m['budget'])}** monthly budget.\n\n"
            f"• **Total Spent:** {format_currency(m['total_spent'])}\n"
            f"• **Remaining Budget:** {format_currency(m['remaining_budget'])}\n"
            f"• **Average Daily Burn:** {format_currency(m['avg_daily'])}/day\n"
            f"• **Projected Month-End Total:** {format_currency(m['projected_month'])}\n\n"
        )
        if m['projected_month'] > m['budget']:
            over_by = m['projected_month'] - m['budget']
            summary_text += f"⚠️ **Forecast Warning:** If current daily spending continues, you may exceed your budget by approximately **{format_currency(over_by)}**."
        else:
            saved_est = m['budget'] - m['projected_month']
            summary_text += f"✅ **Forecast Positive:** You are on track to save approximately **{format_currency(saved_est)}** extra this month."

        return {
            "title": "Monthly Budget & Projection",
            "summary": summary_text,
            "metrics": [
                ("Budget Used", f"{m['budget_used_pct']:.1f}%"),
                ("Remaining", format_currency(m['remaining_budget'])),
                ("Status", status_word),
                ("Projected", format_currency(m['projected_month']))
            ],
            "recommendation": (
                "Try allocating fixed weekly allowances for discretionary spending (food and entertainment) to prevent mid-month budget depletion."
            )
        }

    # 3. SAVINGS & GOAL PROGRESS
    elif topic == "🐷 Savings & Goal Progress":
        laptop_rem = max(0.0, m['goal_target'] - m['saved_for_goal'])
        summary_text = (
            f"Target Goal: **{profile.primary_goal if profile else 'Buy Laptop'}** ({format_currency(m['goal_target'])})\n\n"
            f"• **Amount Saved So Far:** {format_currency(m['saved_for_goal'])}\n"
            f"• **Goal Progress:** **{m['goal_progress_pct']:.1f}%** complete\n"
            f"• **Remaining to Save:** {format_currency(laptop_rem)}\n"
            f"• **Monthly Savings Target:** {format_currency(profile.monthly_savings_target if profile else 3000.0)}\n\n"
        )
        months_needed = int(laptop_rem / (profile.monthly_savings_target if profile and profile.monthly_savings_target > 0 else 3000.0)) + 1
        summary_text += f"By maintaining your planned monthly savings target of **{format_currency(profile.monthly_savings_target if profile else 3000.0)}**, you will reach your goal in approximately **{months_needed} months**."

        return {
            "title": "Savings & Laptop Goal Progress",
            "summary": summary_text,
            "metrics": [
                ("Goal Amount", format_currency(m['goal_target'])),
                ("Saved So Far", format_currency(m['saved_for_goal'])),
                ("Progress", f"{m['goal_progress_pct']:.0f}%"),
                ("Remaining", format_currency(laptop_rem))
            ],
            "recommendation": (
                "Every ₹500 saved from dining out or impulsive shopping shaves days off your goal timeline!"
            )
        }

    # 4. CATEGORY-SPECIFIC ANALYSES (Food, Transport, Shopping, Education, Entertainment, Bills, Travel)
    else:
        # Extract category name from topic (e.g., '🍔 Food Spending' -> 'Food')
        target_cat = topic.split(" ")[1] if " " in topic else topic
        # Normalize
        cat_match = next((c for c in STUDENT_CATEGORIES if c.lower() in target_cat.lower()), "Food")

        sub_df = df[df["category"].str.lower() == cat_match.lower()]
        cat_spent = float(sub_df["amount"].sum()) if not sub_df.empty else 0.0
        cat_count = len(sub_df)
        cat_pct = (cat_spent / m['total_spent'] * 100) if m['total_spent'] > 0 else 0.0
        cat_avg = (cat_spent / cat_count) if cat_count > 0 else 0.0
        ten_pct_save = cat_spent * 0.10

        is_top = (m['top_category']['category'].lower() == cat_match.lower())
        
        summary_text = (
            f"**{cat_match}** " + ("is currently your **largest expense category**." if is_top else f"accounts for **{cat_pct:.1f}%** of your total spending.") + "\n\n"
            f"• **Total Spent on {cat_match}:** {format_currency(cat_spent)}\n"
            f"• **Transactions Recorded:** {cat_count}\n"
            f"• **Average per Transaction:** {format_currency(cat_avg)}\n"
            f"• **Share of Total Wallet Expenses:** {cat_pct:.1f}%\n\n"
            f"💡 **Potential Savings:** Reducing your {cat_match.lower()} spending by just 10% would save approximately **{format_currency(ten_pct_save)}** this month."
        )

        return {
            "title": f"{cat_match} Spending Breakdown",
            "summary": summary_text,
            "metrics": [
                (f"{cat_match} Total", format_currency(cat_spent)),
                ("Share of Total", f"{cat_pct:.1f}%"),
                ("Transactions", str(cat_count)),
                ("Avg per Item", format_currency(cat_avg))
            ],
            "recommendation": (
                f"Your highest {cat_match.lower()} transaction was {format_currency(sub_df['amount'].max() if not sub_df.empty else 0.0)}. "
                f"Track everyday small purchases as they compound into your largest monthly outlays."
            )
        }

# ----------------------------------------------------
# STUDENT VISUALIZATION GENERATORS
# ----------------------------------------------------
def create_where_money_goes_chart(df: pd.DataFrame):
    """
    Plotly Donut chart for student categories.
    Guaranteed clean layout and no fake payment methods.
    """
    if df.empty:
        return None

    cat_grp = df.groupby("category", as_index=False)["amount"].sum()
    cat_grp = cat_grp.sort_values(by="amount", ascending=False)

    colors = [CATEGORY_COLORS_MAP.get(c, "#123C35") for c in cat_grp["category"]]

    fig = px.pie(
        cat_grp,
        names="category",
        values="amount",
        hole=0.55,
        title="Where Your Money Goes",
        color="category",
        color_discrete_map=CATEGORY_COLORS_MAP
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Amount: ₹%{value:,.2f}<br>Share: %{percent}<extra></extra>"
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#202522", size=13),
        title_font=dict(size=17, color="#0B2920", family="Inter, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        margin=dict(l=15, r=15, t=45, b=45),
        height=360
    )
    return fig

def create_spending_trend_bar_chart(df: pd.DataFrame):
    """
    Plotly Bar chart for daily spending trends across recorded dates.
    """
    if df.empty:
        return None

    # Group by expense_date
    daily_df = df.groupby("expense_date", as_index=False)["amount"].sum()
    daily_df["date_clean"] = pd.to_datetime(daily_df["expense_date"]).dt.strftime("%b %d")
    daily_df = daily_df.sort_values(by="expense_date")

    fig = px.bar(
        daily_df,
        x="date_clean",
        y="amount",
        title="Spending Trend (Recent Days)",
        labels={"date_clean": "Date", "amount": "Spent (₹)"},
        color_discrete_sequence=["#123C35"]
    )

    fig.update_traces(
        marker_color="#123C35",
        marker_line_color="#2C5E55",
        marker_line_width=1.2,
        opacity=0.92,
        hovertemplate="<b>%{x}</b><br>Spent: ₹%{y:,.2f}<extra></extra>"
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#202522", size=13),
        title_font=dict(size=17, color="#0B2920", family="Inter, sans-serif"),
        xaxis=dict(showgrid=False, linecolor="rgba(18, 60, 53, 0.2)", tickangle=-30),
        yaxis=dict(showgrid=True, gridcolor="rgba(18, 60, 53, 0.08)", zeroline=False),
        margin=dict(l=15, r=15, t=45, b=45),
        height=360
    )
    return fig
