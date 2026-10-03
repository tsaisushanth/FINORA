import datetime
from typing import List, Tuple

import streamlit as st

def format_currency(amount: float) -> str:
    """Format numeric value into Indian Rupee string format."""
    if amount is None:
        return "₹0"
    if amount < 0:
        return f"-₹{abs(amount):,.2f}" if amount != int(amount) else f"-₹{abs(int(amount)):,}"
    if amount == int(amount):
        return f"₹{int(amount):,}"
    return f"₹{amount:,.2f}"

def get_date_bounds():
    """Return date objects for today, start of current week, start of current month, and last week."""
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())  # Monday
    start_of_month = today.replace(day=1)
    
    start_of_last_week = start_of_week - datetime.timedelta(days=7)
    end_of_last_week = start_of_week - datetime.timedelta(days=1)
    
    return {
        "today": today,
        "start_of_week": start_of_week,
        "start_of_month": start_of_month,
        "start_of_last_week": start_of_last_week,
        "end_of_last_week": end_of_last_week
    }

def get_category_icon(category: str) -> str:
    """Return an appropriate emoji icon for expense categories."""
    icons = {
        "Food": "🍔",
        "Transportation": "🚌",
        "Tickets": "🎟️",
        "Stationery": "📚",
        "Shopping": "🛍️",
        "Education": "🎓",
        "Bills": "💡",
        "Entertainment": "🎮",
        "Health": "🏥",
        "Other": "📦"
    }
    return icons.get(category, "💳")

def get_greeting(name: str = None) -> str:
    """
    Return a time-of-day greeting string.

    ``name`` is the student's first name when a profile exists. Passing None
    keeps the original nameless behaviour so existing callers are unaffected.
    """
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    first_name = (name or "").strip().split(" ")[0] if name else ""
    if first_name:
        return f"{greeting}, {first_name} 👋"
    return f"{greeting} 👋"

def apply_custom_css():
    """Inject improved Finora CSS: high-contrast branding, better typography, hover states, card elevation."""
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ─── Global Base ─── */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #F7F5EF !important;
        color: #202522 !important;
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
        max-width: 1200px;
    }

    /* ─── Sidebar Background ─── */
    section[data-testid="stSidebar"] {
        background-color: #EFECE3 !important;
        border-right: 1px solid rgba(18, 60, 53, 0.1) !important;
    }

    /* ─── Branding Area ─── */
    .brand-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 4px;
        padding: 4px 0;
    }
    /* Logo tile: deep emerald bg with gold icon — high contrast on cream sidebar */
    .brand-logo {
        width: 44px;
        height: 44px;
        background: #0B2920;
        color: #C7A76A;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
        box-shadow: 0 4px 14px rgba(11, 41, 32, 0.22);
        flex-shrink: 0;
    }
    /* Brand name: darkest teal on cream — WCAG AA+ contrast */
    /* Triple-layered override: class, sidebar-scoped, and element targeting */
    .brand-title,
    h1.brand-title,
    section[data-testid="stSidebar"] h1.brand-title,
    section[data-testid="stSidebar"] .brand-header h1.brand-title,
    section[data-testid="stSidebar"] .brand-header .brand-title {
        font-size: 2.05rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.6px !important;
        color: #063B3B !important;
        margin: 0 !important;
        line-height: 1.1 !important;
        -webkit-text-fill-color: #063B3B !important;
    }
    .brand-tagline {
        font-size: 0.9rem;
        color: #4A5450;
        font-weight: 500;
        margin-top: 3px;
        margin-bottom: 26px;
        letter-spacing: 0.1px;
    }

    /* ─── Sidebar Section Labels ─── */
    .sidebar-section-label {
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.9px;
        color: #5C6660;
        font-weight: 700;
        margin-top: 16px;
        margin-bottom: 6px;
    }

    /* ─── Sidebar Nav Buttons ─── */
    /* Override main button styles for sidebar only — transparent bg, text colored */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important;
        color: #1C3B34 !important;
        border: 1px solid transparent !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.55rem 1rem !important;
        box-shadow: none !important;
        transition: background-color 0.18s ease, border-color 0.18s ease, transform 0.18s ease, color 0.18s ease !important;
        text-align: left !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(11, 41, 32, 0.1) !important;
        border-color: rgba(11, 41, 32, 0.18) !important;
        color: #0B2920 !important;
        transform: translateX(3px) !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button:active {
        background-color: rgba(11, 41, 32, 0.18) !important;
        transform: translateX(1px) !important;
    }

    /* ─── Sidebar Financial Summary Card ─── */
    .sidebar-summary-card {
        background: #FFFDF8;
        border: 1px solid rgba(18, 60, 53, 0.12);
        border-radius: 14px;
        padding: 18px;
        margin-top: 14px;
        margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
    }
    .sidebar-summary-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #5C6660;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .sidebar-val-group {
        margin-bottom: 10px;
    }
    .sidebar-val-label {
        font-size: 0.82rem;
        color: #5C6660;
        font-weight: 500;
    }
    .sidebar-val-amount {
        font-size: 1.35rem;
        font-weight: 800;
        color: #0B2920;
    }

    /* ─── Hero Balance Card ─── */
    .hero-balance-card {
        background: linear-gradient(140deg, #123C35 0%, #1A4D45 100%);
        border-radius: 20px;
        padding: 34px;
        color: #FFFDF8;
        box-shadow: 0 12px 30px -8px rgba(18, 60, 53, 0.28);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
        transition: box-shadow 0.22s ease, transform 0.22s ease;
    }
    .hero-balance-card:hover {
        box-shadow: 0 18px 42px -8px rgba(18, 60, 53, 0.36);
        transform: translateY(-2px);
    }
    .hero-balance-card::after {
        content: "💳";
        position: absolute;
        right: 28px;
        top: 24px;
        font-size: 3.5rem;
        opacity: 0.15;
    }
    .hero-label {
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.9px;
        color: #8FA99F;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .hero-amount {
        font-size: 3.1rem;
        font-weight: 800;
        letter-spacing: -1.5px;
        color: #FFFDF8;
        margin-bottom: 8px;
    }
    .hero-subtext {
        font-size: 0.92rem;
        color: #C7A76A;
        font-weight: 500;
    }

    /* ─── Secondary Metric Tiles ─── */
    .metric-tile {
        background: #FFFDF8;
        border: 1px solid rgba(18, 60, 53, 0.08);
        border-radius: 18px;
        padding: 24px 26px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
        transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-tile:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 30px rgba(18, 60, 53, 0.1);
        border-color: rgba(18, 60, 53, 0.22);
    }
    .metric-tile-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
    }
    .metric-tile-label {
        font-size: 0.88rem;
        font-weight: 600;
        color: #5C6660;
    }
    .metric-tile-icon {
        width: 34px;
        height: 34px;
        border-radius: 10px;
        background: rgba(18, 60, 53, 0.07);
        color: #123C35;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.05rem;
    }
    .metric-tile-amount {
        font-size: 2rem;
        font-weight: 800;
        color: #0B2920;
        letter-spacing: -0.5px;
    }
    .metric-tile-sub {
        font-size: 0.82rem;
        color: #68716D;
        margin-top: 5px;
        font-weight: 500;
    }

    /* ─── Chart / Content Cards ─── */
    .finora-card {
        background: #FFFDF8;
        border: 1px solid rgba(18, 60, 53, 0.08);
        border-radius: 20px;
        padding: 26px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
        margin-bottom: 24px;
        transition: box-shadow 0.22s ease;
    }
    .finora-card:hover {
        box-shadow: 0 10px 28px rgba(18, 60, 53, 0.08);
    }

    /* ─── Insight Cards ─── */
    .insight-card {
        background: #FFFDF8;
        border: 1px solid rgba(18, 60, 53, 0.1);
        border-left: 4px solid #123C35;
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 12px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .insight-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(18, 60, 53, 0.07);
    }
    .insight-text {
        color: #202522;
        font-size: 0.97rem;
        line-height: 1.55;
        font-weight: 500;
    }

    /* ─── Recent Activity Rows ─── */
    .activity-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px;
        background: #FFFDF8;
        border: 1px solid rgba(18, 60, 53, 0.06);
        border-radius: 16px;
        margin-bottom: 10px;
        transition: transform 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
    }
    .activity-row:hover {
        transform: translateX(4px);
        background: #F4F0E6;
        box-shadow: 0 4px 14px rgba(18, 60, 53, 0.07);
    }
    .activity-left {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .activity-icon {
        width: 46px;
        height: 46px;
        border-radius: 50%;
        background: rgba(18, 60, 53, 0.07);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
    }
    .activity-desc {
        font-weight: 700;
        font-size: 1.05rem;
        color: #1A2520;
    }
    .activity-meta {
        font-size: 0.86rem;
        color: #68716D;
        margin-top: 3px;
    }
    .activity-amount {
        font-weight: 800;
        font-size: 1.18rem;
    }
    .activity-amount.out {
        color: #991B1B;
    }
    .activity-amount.in {
        color: #124B38;
    }

    /* ─── Status Badges ─── */
    .status-badge-pending {
        background: rgba(199, 167, 106, 0.18);
        color: #8A6D3B;
        border: 1px solid rgba(199, 167, 106, 0.4);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .status-badge-partial {
        background: rgba(143, 169, 159, 0.2);
        color: #123C35;
        border: 1px solid rgba(18, 60, 53, 0.2);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .status-badge-paid {
        background: rgba(18, 75, 56, 0.12);
        color: #124B38;
        border: 1px solid rgba(18, 75, 56, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
    }

    /* ─── Buttons — Main Content Area ─── */
    /* Target main content buttons without touching sidebar */
    .main .stButton > button,
    [data-testid="stMainBlockContainer"] .stButton > button {
        background-color: #123C35 !important;
        color: #FFFDF8 !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 0.97rem !important;
        padding: 0.62rem 1.4rem !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(18, 60, 53, 0.15) !important;
        transition: all 0.2s ease !important;
    }
    .main .stButton > button:hover,
    [data-testid="stMainBlockContainer"] .stButton > button:hover {
        background-color: #1A4D45 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 22px rgba(18, 60, 53, 0.25) !important;
    }

    /* ─── Form Cards ─── */
    .form-card {
        background: #FFFDF8;
        border: 1px solid rgba(18, 60, 53, 0.1);
        border-radius: 20px;
        padding: 32px;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.04);
    }

    /* ─── Empty State ─── */
    .empty-state-box {
        text-align: center;
        padding: 52px 24px;
        background: #FFFDF8;
        border: 2px dashed rgba(18, 60, 53, 0.15);
        border-radius: 20px;
        margin: 24px 0;
    }
    .empty-state-icon {
        font-size: 3.2rem;
        margin-bottom: 14px;
    }
    .empty-state-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #14201B;
        margin-bottom: 8px;
    }
    .empty-state-desc {
        font-size: 0.97rem;
        color: #56635D;
        max-width: 420px;
        margin: 0 auto 20px auto;
        line-height: 1.55;
    }

    /* ─── Improved Input & Label Visibility (whole app) ─── */
    [data-testid="stTextInput"] label p,
    [data-testid="stNumberInput"] label p,
    [data-testid="stSelectbox"] label p,
    [data-testid="stTextArea"] label p,
    [data-testid="stDateInput"] label p,
    [data-testid="stMultiselect"] label p {
        color: #14201B !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stDateInput"] input {
        color: #171F1B !important;
        background-color: #FFFFFF !important;
        border: 1px solid #C7CFC9 !important;
        border-radius: 10px !important;
    }
    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stNumberInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {
        color: #6B7670 !important;
        opacity: 1 !important;
    }
    [data-baseweb="select"] {
        color: #171F1B !important;
        background-color: #FFFFFF !important;
        border: 1px solid #C7CFC9 !important;
        border-radius: 10px !important;
    }
    [data-baseweb="select"] div[class*="Placeholder"] {
        color: #6B7670 !important;
    }
    [data-baseweb="select"] div[class*="SelectArrow"] {
        color: #2E3A34 !important;
    }
    [data-baseweb="calendar"] {
        background-color: #FFFFFF !important;
    }

    /* ─── Bucket List (Goals) ─── */

    /* Page hero */
    .goal-hero {
        background: linear-gradient(135deg, #0B2231 0%, #123C35 55%, #1A4D45 100%);
        border-radius: 22px;
        padding: 30px 34px;
        margin-bottom: 22px;
        box-shadow: 0 14px 34px -10px rgba(11, 34, 49, 0.45);
        position: relative;
        overflow: hidden;
        color: #FFFFFF;
    }
    .goal-hero::after {
        content: "🎯";
        position: absolute;
        right: 26px;
        top: 20px;
        font-size: 4.2rem;
        opacity: 0.16;
    }
    .goal-hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF;
    }
    .goal-hero-sub {
        color: #AFC7D2;
        font-size: 1.02rem;
        margin-top: 5px;
        font-weight: 500;
    }
    .goal-hero-chip-row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 16px;
    }
    .goal-hero-chip {
        background: rgba(255, 255, 255, 0.13);
        border: 1px solid rgba(255, 255, 255, 0.24);
        color: #FFFFFF;
        padding: 8px 14px;
        border-radius: 40px;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .goal-hero-chip b {
        color: #7CE4B6;
        font-weight: 800;
    }

    /* Summary stats grid */
    .g-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(175px, 1fr));
        gap: 14px;
        margin-bottom: 26px;
    }
    .g-stat {
        background: #FFFDF8;
        border: 1px solid rgba(18, 60, 53, 0.1);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .g-stat:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 24px rgba(18, 60, 53, 0.1);
    }
    .g-stat-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .g-stat-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        color: #42504A;
        font-weight: 700;
    }
    .g-stat-icon {
        font-size: 1.2rem;
    }
    .g-stat-value {
        font-size: 1.55rem;
        font-weight: 800;
        color: #14201B;
        letter-spacing: -0.4px;
    }
    .g-stat-sub {
        font-size: 0.8rem;
        color: #56635D;
        margin-top: 3px;
        font-weight: 500;
    }

    /* Feature cards (Top priority / Closest) */
    .goal-summary-card {
        background: #FFFDF8;
        border: 1px solid rgba(18, 60, 53, 0.1);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
        margin-top: 14px;
        height: 100%;
    }
    .goal-summary-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        color: #42504A;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .goal-summary-value {
        font-size: 1.55rem;
        font-weight: 800;
        color: #14201B;
        letter-spacing: -0.4px;
    }
    .goal-summary-sub {
        font-size: 0.82rem;
        color: #56635D;
        margin-top: 4px;
        font-weight: 500;
    }

    /* Goal cards */
    .goal-card {
        background: #FFFFFF;
        border: 1px solid #DDE4E0;
        border-radius: 18px;
        padding: 22px 24px;
        box-shadow: 0 4px 18px rgba(15, 35, 30, 0.06);
        display: flex;
        flex-direction: column;
        height: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .goal-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 14px 32px rgba(15, 35, 30, 0.13);
        border-color: #9FBFB3;
    }
    .goal-card.completed {
        background: linear-gradient(150deg, #EDF8F1 0%, #FFFFFF 100%);
        border: 1px solid #A9D6BE;
    }
    .goal-card.paused {
        background: #FBF9F6;
        border-color: #E4DCC8;
    }
    .goal-card-top {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 12px;
    }
    .g-icon {
        width: 46px;
        height: 46px;
        border-radius: 14px;
        background: #E8EFEB;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.35rem;
        flex-shrink: 0;
    }
    .goal-card.completed .g-icon {
        background: #D9F1E3;
    }
    .goal-card-name {
        font-size: 1.18rem;
        font-weight: 800;
        color: #14201B;
        letter-spacing: -0.2px;
        line-height: 1.2;
    }
    .goal-card-cat {
        font-size: 0.84rem;
        color: #42504A;
        font-weight: 600;
        margin-top: 2px;
    }
    .g-badges {
        margin-left: auto;
        display: flex;
        flex-direction: column;
        gap: 6px;
        align-items: flex-end;
    }

    /* Badges — high contrast */
    .gb {
        font-size: 0.72rem;
        font-weight: 800;
        padding: 4px 11px;
        border-radius: 30px;
        letter-spacing: 0.3px;
        white-space: nowrap;
    }
    .gb-active { background: #DDF0E9; color: #0C5B46; border: 1px solid #AFDECD; }
    .gb-paused { background: #F3EEDC; color: #7A6820; border: 1px solid #E0D3A8; }
    .gb-completed { background: #D8F1E4; color: #0F6F42; border: 1px solid #AEE0C3; }
    .gb-archived { background: #ECEFED; color: #4A5751; border: 1px solid #D3DAD5; }
    .gb-high { background: #FCEAE7; color: #AE221A; border: 1px solid #F2C6BF; }
    .gb-medium { background: #F7EED8; color: #82620F; border: 1px solid #EAD8A8; }
    .gb-low { background: #E3EFFA; color: #1D5F94; border: 1px solid #BAD8F0; }

    /* Amounts */
    .goal-amount {
        display: flex;
        align-items: baseline;
        gap: 8px;
        margin-bottom: 2px;
        flex-wrap: wrap;
    }
    .g-saved {
        font-size: 1.65rem;
        font-weight: 800;
        color: #14201B;
        letter-spacing: -0.5px;
    }
    .g-target {
        font-size: 1.02rem;
        font-weight: 600;
        color: #56635D;
    }
    .g-percent {
        margin-left: auto;
        font-weight: 800;
        font-size: 1.08rem;
    }
    .g-remaining {
        font-size: 0.92rem;
        color: #42504A;
        font-weight: 500;
        margin: 6px 0 12px;
    }
    .g-remaining b {
        color: #14201B;
    }

    /* Progress bar */
    .g-bar {
        width: 100%;
        height: 11px;
        background: #E3E9E6;
        border-radius: 30px;
        overflow: hidden;
    }
    .g-fill {
        height: 100%;
        border-radius: 30px;
        transition: width 0.45s ease;
    }
    .g-stage-0 { background: #D0D7D3; }
    .g-stage-1 { background: #8AA0B5; }
    .g-stage-2 { background: #4F8BFF; }
    .g-stage-3 { background: #2BB3A3; }
    .g-stage-4 { background: #8B5CF6; }
    .g-stage-5 { background: #16A34A; }
    .g-progress-caption {
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
        color: #42504A;
        margin-top: 6px;
        font-weight: 600;
    }
    .g-progress-caption b {
        color: #14201B;
    }

    /* Deadline strip */
    .g-deadline {
        margin-top: 12px;
        padding: 10px 12px;
        background: #F4F6F4;
        border: 1px solid #E4E9E6;
        border-radius: 12px;
        font-size: 0.85rem;
        color: #3D4A44;
        display: flex;
        flex-wrap: wrap;
        gap: 4px 14px;
        font-weight: 600;
    }
    .g-deadline span {
        color: #3D4A44;
    }
    .g-deadline b {
        color: #14201B;
        font-weight: 800;
    }

    .goal-completed-flag {
        margin-top: 10px;
        background: #E4F7EC;
        border: 1px solid #AEE0C3;
        color: #0C6B3F;
        border-radius: 12px;
        padding: 10px 12px;
        font-weight: 800;
        text-align: center;
        font-size: 0.95rem;
    }
    .goal-paused-flag {
        margin-top: 10px;
        background: #F3EEDC;
        border: 1px solid #E0D3A8;
        color: #7A6820;
        border-radius: 12px;
        padding: 9px 12px;
        font-weight: 700;
        text-align: center;
        font-size: 0.9rem;
    }
    .g-desc {
        margin-top: 10px;
        font-size: 0.86rem;
        color: #42504A;
        line-height: 1.5;
    }

    /* ─── Student Profile & Auth ─── */
    .auth-hero {
        background: linear-gradient(135deg, #0B2231 0%, #123C35 55%, #1A4D45 100%);
        border-radius: 22px;
        padding: 32px 34px;
        margin-bottom: 22px;
        box-shadow: 0 14px 34px -10px rgba(11, 34, 49, 0.45);
        position: relative;
        overflow: hidden;
        color: #FFFFFF;
    }
    .auth-hero::after {
        content: "🎓";
        position: absolute;
        right: 26px;
        top: 20px;
        font-size: 4.2rem;
        opacity: 0.16;
    }
    .auth-hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF;
    }
    .auth-hero-sub {
        color: #AFC7D2;
        font-size: 1.02rem;
        margin-top: 5px;
        font-weight: 500;
    }

    /* Profile identity header */
    .pf-identity {
        display: flex;
        align-items: center;
        gap: 18px;
        background: #FFFDF8;
        border: 1px solid rgba(18, 60, 53, 0.1);
        border-radius: 20px;
        padding: 22px 26px;
        margin-bottom: 22px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
    }
    .pf-avatar {
        width: 62px;
        height: 62px;
        border-radius: 18px;
        background: linear-gradient(140deg, #123C35 0%, #2C5E55 100%);
        color: #C7A76A;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.7rem;
        font-weight: 800;
        flex-shrink: 0;
    }
    .pf-identity-name {
        font-size: 1.5rem;
        font-weight: 800;
        color: #14201B;
        letter-spacing: -0.3px;
        line-height: 1.2;
    }
    .pf-identity-meta {
        font-size: 0.9rem;
        color: #56635D;
        margin-top: 4px;
        font-weight: 500;
    }

    /* Read-only profile detail grid */
    .pf-section-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        color: #42504A;
        font-weight: 700;
        margin: 4px 0 10px 0;
    }
    .pf-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 14px;
        margin-bottom: 8px;
    }
    .pf-detail {
        background: #FFFDF8;
        border: 1px solid rgba(18, 60, 53, 0.08);
        border-radius: 14px;
        padding: 15px 18px;
    }
    .pf-detail-label {
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #5C6660;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .pf-detail-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: #14201B;
        line-height: 1.35;
    }

    /* Goal progress teaser inside the profile page */
    .pf-goal-card {
        background: linear-gradient(150deg, #EDF8F1 0%, #FFFDF8 100%);
        border: 1px solid #A9D6BE;
        border-radius: 18px;
        padding: 22px 24px;
        margin-bottom: 22px;
    }
    .pf-goal-title {
        font-size: 1.2rem;
        font-weight: 800;
        color: #0C5B46;
        margin-bottom: 4px;
    }

    /* Status / feedback boxes */
    .pf-notice {
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 16px;
        font-size: 0.94rem;
        font-weight: 600;
        line-height: 1.55;
    }
    .pf-notice-warn {
        background: #FFF7E0;
        border: 1px solid #FFE6A1;
        color: #7A5A00;
    }
    .pf-notice-info {
        background: #F1F6F9;
        border: 1px solid #CBDDE8;
        color: #274E5E;
    }

    /* ─── Responsive ─── */
    @media (max-width: 768px) {
        .hero-amount {
            font-size: 2.2rem;
        }
        .main .block-container {
            padding-left: 1.2rem;
            padding-right: 1.2rem;
        }
        .goal-hero {
            padding: 22px 22px;
        }
        .goal-hero-title {
            font-size: 1.6rem;
        }
        .goal-hero::after {
            display: none;
        }
        .g-stats {
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        }
        .g-badges {
            align-items: flex-start;
        }
        .auth-hero,
        .goal-hero {
            padding: 22px 22px;
        }
        .pf-identity {
            padding: 18px 18px;
            gap: 14px;
        }
        .pf-avatar {
            width: 52px;
            height: 52px;
            font-size: 1.4rem;
        }
        .pf-grid {
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def render_hero_balance(amount_str: str, subtext: str = "Available in your wallet"):
    """Render large Deep Emerald Hero Balance Card."""
    html = f"""
    <div class="hero-balance-card">
        <div class="hero-label">Available Balance</div>
        <div class="hero-amount">{amount_str}</div>
        <div class="hero-subtext">{subtext}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_metric_tile(label: str, amount_str: str, subtext: str = "", icon: str = "💸"):
    """Render a clean light metric card."""
    sub_html = f'<div class="metric-tile-sub">{subtext}</div>' if subtext else ''
    html = f"""
    <div class="metric-tile">
        <div class="metric-tile-header">
            <span class="metric-tile-label">{label}</span>
            <div class="metric-tile-icon">{icon}</div>
        </div>
        <div>
            <div class="metric-tile-amount">{amount_str}</div>
            {sub_html}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def format_transaction_type(tx_type: str):
    """Return badge/label for transaction type."""
    mapping = {
        "add_money": ("🟢 Money Added", "activity-amount in"),
        "expense": ("🔴 Expense", "activity-amount out"),
        "money_lent": ("🔴 Money Lent", "activity-amount out"),
        "money_received": ("🟢 Money Received", "activity-amount in"),
        "money_borrowed": ("🟢 Money Borrowed", "activity-amount in"),
        "money_repaid": ("🔴 Loan Repayment", "activity-amount out"),
        "goal_allocation": ("🎯 Allocated to Goal", "activity-amount out"),
        "goal_removal": ("↩️ Goal Removal", "activity-amount in")
    }
    return mapping.get(tx_type, (tx_type, ""))


def get_goal_category_icon(category: str) -> str:
    """Return an appropriate emoji icon for goal categories."""
    icons = {
        "Electronics": "📱",
        "Travel": "✈️",
        "Education": "🎓",
        "Shopping": "🛍️",
        "Entertainment": "🎬",
        "Personal": "🌱",
        "Emergency": "🆘",
        "Other": "🎯"
    }
    return icons.get(category, "🎯")


# ---------------------------------------------------------------------
# STUDENT PROFILE RENDERING HELPERS
# ---------------------------------------------------------------------

def get_initials(name: str) -> str:
    """Return up to two initials for the profile avatar."""
    parts = [p for p in (name or "").split() if p]
    if not parts:
        return "🎓"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def format_study_year(year: int) -> str:
    """Render a study year as '2nd Year' where possible, else 'Year 2'."""
    suffixes = {1: "st", 2: "nd", 3: "rd"}
    try:
        value = int(year)
    except (TypeError, ValueError):
        return "—"
    suffix = suffixes.get(value)
    if suffix:
        return f"{value}{suffix} Year"
    return f"Year {value}"


def render_auth_hero(title: str, subtitle: str) -> None:
    """Render the hero banner used by the sign-in and profile-setup screens."""
    st.markdown(f"""
    <div class="auth-hero">
        <div class="auth-hero-title">{title}</div>
        <div class="auth-hero-sub">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def render_profile_identity(name: str, meta_line: str) -> None:
    """Render the avatar + name + college/course header for a profile."""
    st.markdown(f"""
    <div class="pf-identity">
        <div class="pf-avatar">{get_initials(name)}</div>
        <div>
            <div class="pf-identity-name">{name}</div>
            <div class="pf-identity-meta">{meta_line}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_profile_details(details: List[Tuple[str, str]]) -> None:
    """
    Render a responsive grid of read-only label/value pairs.

    ``details`` is a list of ``(label, value)`` tuples.
    """
    cells = "".join(
        f'<div class="pf-detail"><div class="pf-detail-label">{label}</div>'
        f'<div class="pf-detail-value">{value}</div></div>'
        for label, value in details
    )
    st.markdown(f'<div class="pf-grid">{cells}</div>', unsafe_allow_html=True)


def render_section_label(label: str) -> None:
    """Render a small uppercase section heading."""
    st.markdown(f'<div class="pf-section-label">{label}</div>', unsafe_allow_html=True)


def render_notice(message: str, kind: str = "info") -> None:
    """Render an inline notice box. ``kind`` is 'info' or 'warn'."""
    css_class = "pf-notice-warn" if kind == "warn" else "pf-notice-info"
    icon = "⚠️" if kind == "warn" else "ℹ️"
    st.markdown(
        f'<div class="pf-notice {css_class}">{icon} {message}</div>',
        unsafe_allow_html=True
    )
