import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Tuple
from utils import get_date_bounds, format_currency
from database import get_wallet_balance

# Premium Finora Light Color Palette
CATEGORY_COLORS = [
    "#123C35", "#8FA99F", "#C7A76A", "#2C5E55",
    "#6B8B7F", "#998563", "#3B6258", "#52786D"
]

def prepare_dataframe(expenses: Any) -> pd.DataFrame:
    """
    Convert expenses list/data into pandas DataFrame with guaranteed columns and clean types.
    Handles None, empty lists, SQLite Row objects, dicts, and Supabase data structures.
    """
    expected_columns = [
        "id", "amount", "category", "note", "expense_date",
        "expense_time", "payment_method", "created_at"
    ]
    
    if expenses is None:
        expenses = []
    elif hasattr(expenses, "data"):
        expenses = expenses.data
    elif isinstance(expenses, dict):
        expenses = [expenses]
    elif not isinstance(expenses, list):
        try:
            expenses = list(expenses)
        except Exception:
            expenses = []

    if not expenses:
        df = pd.DataFrame(columns=expected_columns)
        df["amount"] = pd.Series(dtype="float64")
        return df

    # Normalize elements to plain dicts if they are SQLite Rows or custom objects
    clean_records = []
    for item in expenses:
        if isinstance(item, dict):
            clean_records.append(item)
        elif hasattr(item, "as_dict"):
            clean_records.append(item.as_dict())
        elif hasattr(item, "__dict__"):
            clean_records.append(dict(item.__dict__))
        else:
            try:
                clean_records.append(dict(item))
            except Exception:
                continue

    if not clean_records:
        df = pd.DataFrame(columns=expected_columns)
        df["amount"] = pd.Series(dtype="float64")
        return df

    df = pd.DataFrame(clean_records)

    # Ensure all expected columns exist
    for col in expected_columns:
        if col not in df.columns:
            df[col] = None

    # Safe datetime and numeric parsing
    try:
        df["expense_date"] = pd.to_datetime(df["expense_date"], errors="coerce").dt.date
    except Exception:
        pass

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["category"] = df["category"].fillna("Other").astype(str)
    df["note"] = df["note"].fillna("").astype(str)
    df["payment_method"] = df["payment_method"].fillna("Other").astype(str)

    return df

def get_dashboard_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate key dashboard metrics from real database DataFrame."""
    dates = get_date_bounds()
    wallet_bal = get_wallet_balance()
    
    if df.empty:
        return {
            "wallet_balance": wallet_bal,
            "spent_this_week": 0.0,
            "spent_this_month": 0.0,
            "count_this_month": 0
        }
        
    week_df = df[df["expense_date"] >= dates["start_of_week"]]
    spent_week = week_df["amount"].sum()
    
    month_df = df[df["expense_date"] >= dates["start_of_month"]]
    spent_month = month_df["amount"].sum()
    count_month = len(month_df)
    
    return {
        "wallet_balance": wallet_bal,
        "spent_this_week": float(spent_week),
        "spent_this_month": float(spent_month),
        "count_this_month": int(count_month)
    }

def create_category_pie_chart(df: pd.DataFrame, period: str = "this_month"):
    """Generate Plotly Donut chart for category-wise spending."""
    if df.empty:
        return None
        
    dates = get_date_bounds()
    if period == "this_week":
        filtered_df = df[df["expense_date"] >= dates["start_of_week"]]
        title_suffix = "This Week"
    else:
        filtered_df = df[df["expense_date"] >= dates["start_of_month"]]
        title_suffix = "This Month"
        
    if filtered_df.empty:
        return None
        
    cat_summary = filtered_df.groupby("category", as_index=False)["amount"].sum()
    cat_summary = cat_summary.sort_values(by="amount", ascending=False)
    
    fig = px.pie(
        cat_summary,
        names="category",
        values="amount",
        hole=0.55,
        color_discrete_sequence=CATEGORY_COLORS,
        title=f"Where your money goes ({title_suffix})"
    )
    
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Amount: ₹%{value:,.2f}<br>Share: %{percent}"
    )
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#202522", size=14),
        title_font=dict(size=18, color="#123C35", family="Inter, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=50, b=50),
        height=380
    )
    return fig

def create_trend_chart(df: pd.DataFrame, period: str = "this_month"):
    """Generate Plotly spending line/bar chart over time."""
    if df.empty:
        return None
        
    dates = get_date_bounds()
    today = dates["today"]
    
    if period == "this_week":
        start_d = dates["start_of_week"]
        title_suffix = "This Week"
        date_range = [start_d + datetime.timedelta(days=i) for i in range((today - start_d).days + 1)]
    else:
        start_d = dates["start_of_month"]
        title_suffix = "This Month"
        date_range = [start_d + datetime.timedelta(days=i) for i in range((today - start_d).days + 1)]
        
    filtered_df = df[(df["expense_date"] >= start_d) & (df["expense_date"] <= today)]
    
    daily_summary = filtered_df.groupby("expense_date", as_index=False)["amount"].sum()
    range_df = pd.DataFrame({"expense_date": date_range})
    merged = pd.merge(range_df, daily_summary, on="expense_date", how="left").fillna(0.0)
    merged["date_str"] = merged["expense_date"].apply(lambda d: d.strftime("%b %d"))
    
    fig = px.bar(
        merged,
        x="date_str",
        y="amount",
        title=f"Spending over time ({title_suffix})",
        labels={"date_str": "Date", "amount": "Spent (₹)"},
        color_discrete_sequence=["#123C35"]
    )
    
    fig.update_traces(
        marker_color="#123C35",
        marker_line_color="#2C5E55",
        marker_line_width=1.5,
        opacity=0.9,
        hovertemplate="<b>%{x}</b><br>Spent: ₹%{y:,.2f}<extra></extra>"
    )
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#202522", size=14),
        title_font=dict(size=18, color="#123C35", family="Inter, sans-serif"),
        xaxis=dict(showgrid=False, linecolor="rgba(18, 60, 53, 0.2)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(18, 60, 53, 0.06)", zeroline=False),
        margin=dict(l=20, r=20, t=50, b=40),
        height=380
    )
    return fig

def generate_spending_insights(df: pd.DataFrame) -> List[str]:
    """
    Generate rule-based spending insights based on actual database data.
    Only returns insights if sufficient data exists.
    """
    if df.empty:
        return []
        
    dates = get_date_bounds()
    today = dates["today"]
    month_df = df[df["expense_date"] >= dates["start_of_month"]]
    
    if month_df.empty or month_df["amount"].sum() <= 0:
        return []
        
    insights = []
    total_month_spent = month_df["amount"].sum()
    
    cat_totals = month_df.groupby("category")["amount"].sum()
    top_category = cat_totals.idxmax()
    top_cat_amount = cat_totals.max()
    top_cat_pct = (top_cat_amount / total_month_spent) * 100
    
    insights.append(
        f"💡 **{top_category} is your largest expense category** — You spent {format_currency(top_cat_amount)} on {top_category.lower()} this month ({top_cat_pct:.1f}% of total)."
    )
    
    days_in_month_so_far = max(1, (today - dates["start_of_month"]).days + 1)
    avg_daily = total_month_spent / days_in_month_so_far
    insights.append(
        f"📊 **Daily spending average** — You are averaging **{format_currency(avg_daily)}** per day this month."
    )
    
    this_week_df = df[df["expense_date"] >= dates["start_of_week"]]
    last_week_df = df[(df["expense_date"] >= dates["start_of_last_week"]) & (df["expense_date"] <= dates["end_of_last_week"])]
    
    this_week_spent = this_week_df["amount"].sum()
    last_week_spent = last_week_df["amount"].sum()
    
    if last_week_spent > 0:
        diff = this_week_spent - last_week_spent
        if diff > 0:
            insights.append(
                f"📈 **Spending trend** — Your spending is **{format_currency(diff)} higher** this week compared to last week ({format_currency(this_week_spent)} vs {format_currency(last_week_spent)})."
            )
        elif diff < 0:
            insights.append(
                f"📉 **Spending trend** — Your spending is **{format_currency(abs(diff))} lower** this week compared to last week ({format_currency(this_week_spent)} vs {format_currency(last_week_spent)})."
            )

    return insights
