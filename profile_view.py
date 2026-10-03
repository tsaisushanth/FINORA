"""
Streamlit views for Finora authentication and the student profile.

Screens
-------
* :func:`render_auth_screen`   — sign in / create account (Supabase Auth)
* :func:`render_profile_setup` — first-time student profile (blocks the app)
* :func:`render_profile_page`  — view and edit an existing profile

All three reuse Finora's existing design system (``utils.apply_custom_css``
classes, ``form-card``, ``render_notice``) and keep the same emoji + st.error /
st.success tone as the rest of the app.

No screen ever accepts a profile id: the id always comes from the verified
session in :mod:`auth`.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

import streamlit as st

import auth
import profiles as profiles_mod
import supabase_client as sc
from database import get_user_goals, get_total_allocated_to_goals, get_wallet_summary, save_local_profile
from profiles import (
    COMMON_PRIMARY_GOALS,
    CUSTOM_GOAL_OPTION,
    Profile,
    ProfileDraft,
    ProfileValidationError,
)
from utils import (
    format_currency,
    format_study_year,
    render_auth_hero,
    render_notice,
    render_profile_details,
    render_profile_identity,
    render_section_label,
)

SETUP_NAV_KEY = "profile_setup_complete"


# =====================================================================
# =====================================================================
# PUBLIC LANDING PAGE & AUTHENTICATION
# =====================================================================

def render_auth_screen() -> None:
    """
    Render the public landing page, sign-in, or sign-up screen for Finora.
    """
    if "auth_view_mode" not in st.session_state:
        st.session_state.auth_view_mode = "landing"

    mode = st.session_state.auth_view_mode

    if mode == "login":
        _render_login_page()
    elif mode == "signup":
        _render_signup_page()
    else:
        _render_landing_page()


def _render_landing_page() -> None:
    """Render the public Finora Landing Page for unauthenticated visitors."""
    st.markdown("""
    <div style="text-align: center; max-width: 820px; margin: 10px auto 28px auto; padding: 20px 0;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 72px; height: 72px; background: #0B2920; color: #C7A76A; font-size: 2.3rem; border-radius: 22px; margin-bottom: 18px; box-shadow: 0 8px 24px rgba(11, 41, 32, 0.22);">
            💳
        </div>
        <h1 style="font-size: 3.4rem; font-weight: 800; color: #0B2920; margin-bottom: 6px; letter-spacing: -1.2px;">FINORA</h1>
        <div style="font-size: 1.4rem; font-weight: 700; color: #123C35; margin-bottom: 16px; letter-spacing: -0.3px;">
            Know where your money goes.
        </div>
        <p style="font-size: 1.15rem; color: #4A5450; line-height: 1.65; max-width: 640px; margin: 0 auto 30px auto; font-weight: 450;">
            A simple personal finance companion built for students to track spending, understand their habits and manage their money better.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Three action buttons: Login, Sign Up, and Explore Demo
    col_btn_login, col_btn_signup, col_btn_demo = st.columns([1.2, 1.2, 1.6])
    with col_btn_login:
        if st.button("🔐 Login", use_container_width=True):
            st.session_state.auth_view_mode = "login"
            st.rerun()
    with col_btn_signup:
        if st.button("✨ Sign Up", use_container_width=True):
            st.session_state.auth_view_mode = "signup"
            st.rerun()
    with col_btn_demo:
        if st.button("🚀 Explore Demo (Sample Data)", use_container_width=True, type="primary"):
            st.session_state["is_demo_mode"] = True
            st.rerun()

    st.write("")
    st.write("")

    # 3 Feature highlights
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("""
        <div style="background: #FFFDF8; border: 1px solid rgba(18, 60, 53, 0.12); border-radius: 16px; padding: 24px 20px; height: 100%; box-shadow: 0 4px 16px rgba(18, 60, 53, 0.04);">
            <div style="font-size: 2.2rem; margin-bottom: 12px;">🎯</div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #0B2920; margin-bottom: 8px;">Smart Budgets</div>
            <div style="font-size: 0.92rem; color: #56635D; line-height: 1.55;">
                Plan your monthly pocket money, stipend, or allowance with clear student-centric spending limits.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with f2:
        st.markdown("""
        <div style="background: #FFFDF8; border: 1px solid rgba(18, 60, 53, 0.12); border-radius: 16px; padding: 24px 20px; height: 100%; box-shadow: 0 4px 16px rgba(18, 60, 53, 0.04);">
            <div style="font-size: 2.2rem; margin-bottom: 12px;">📊</div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #0B2920; margin-bottom: 8px;">Visual Spending</div>
            <div style="font-size: 0.92rem; color: #56635D; line-height: 1.55;">
                See where your money goes with category breakdowns, daily trends, and automated financial insights.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with f3:
        st.markdown("""
        <div style="background: #FFFDF8; border: 1px solid rgba(18, 60, 53, 0.12); border-radius: 16px; padding: 24px 20px; height: 100%; box-shadow: 0 4px 16px rgba(18, 60, 53, 0.04);">
            <div style="font-size: 2.2rem; margin-bottom: 12px;">🏆</div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #0B2920; margin-bottom: 8px;">Goal Milestones</div>
            <div style="font-size: 0.92rem; color: #56635D; line-height: 1.55;">
                Save toward a new laptop, course fees, or your dream trip with deadline progress calculations.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top: 40px; text-align: center; font-size: 0.85rem; color: #68716D;">
        🔒 Private and Isolated per Student · Supabase Authentication &amp; RLS Protected
    </div>
    """, unsafe_allow_html=True)


def _render_login_page() -> None:
    """Render the sign-in form page."""
    c_back, _ = st.columns([1, 5])
    with c_back:
        if st.button("← Back", key="login_back_btn"):
            st.session_state.auth_view_mode = "landing"
            st.rerun()

    st.markdown("""
    <div style="text-align: center; margin-bottom: 24px;">
        <h2 style="font-size: 2.2rem; font-weight: 800; color: #0B2920; margin-bottom: 4px;">Welcome Back</h2>
        <p style="color: #5C6660; font-size: 1.05rem;">Sign in to your Finora account to see your dashboard.</p>
    </div>
    """, unsafe_allow_html=True)

    c_sp1, c_card, c_sp2 = st.columns([1, 2.2, 1])
    with c_card:
        # Pre-seeded Demo Helper Box
        st.markdown("""
        <div style="background: #EBF5F1; border: 1.5px dashed #2D7A5E; border-radius: 14px; padding: 18px 20px; margin-bottom: 16px;">
            <div style="font-weight: 800; color: #0B2920; font-size: 1.05rem; margin-bottom: 6px;">🎓 Demo Student Account</div>
            <div style="font-size: 0.88rem; color: #2C423B; line-height: 1.6; margin-bottom: 4px;">
                <b>Email:</b> <code style="background:#FFF; padding:2px 6px; border-radius:4px; font-weight:700;">demo@finora.app</code><br>
                <b>Password:</b> <code style="background:#FFF; padding:2px 6px; border-radius:4px; font-weight:700;">FinoraDemo@2026</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("⚡ Use Demo Account (Auto-Fill & Sign In)", use_container_width=True):
            _run_signin("demo@finora.app", "FinoraDemo@2026")

        st.markdown("<div style='text-align:center; color:#85908B; font-size:0.8rem; margin:16px 0;'>— OR ENTER CREDENTIALS —</div>", unsafe_allow_html=True)

        with st.form("finora_signin_form", clear_on_submit=False):
            si_email = st.text_input("Email *", placeholder="you@college.edu")
            si_password = st.text_input(
                "Password *", type="password", placeholder="Your password"
            )
            st.write("")
            si_submit = st.form_submit_button(
                "Sign In", use_container_width=True, type="primary"
            )

        if si_submit:
            _run_signin(si_email, si_password)

        st.markdown("---")
        sw_c1, sw_c2 = st.columns([2, 1.4])
        with sw_c1:
            st.caption("Don't have an account?")
        with sw_c2:
            if st.button("Sign Up →", key="switch_to_signup", use_container_width=True):
                st.session_state.auth_view_mode = "signup"
                st.rerun()


def _render_signup_page() -> None:
    """Render the account creation form page."""
    c_back, _ = st.columns([1, 5])
    with c_back:
        if st.button("← Back", key="signup_back_btn"):
            st.session_state.auth_view_mode = "landing"
            st.rerun()

    st.markdown("""
    <div style="text-align: center; margin-bottom: 24px;">
        <h2 style="font-size: 2.2rem; font-weight: 800; color: #0B2920; margin-bottom: 4px;">Create Account</h2>
        <p style="color: #5C6660; font-size: 1.05rem;">Sign up with your email to start managing your student finances.</p>
    </div>
    """, unsafe_allow_html=True)

    c_sp1, c_card, c_sp2 = st.columns([1, 2.2, 1])
    with c_card:
        st.markdown("<div class='form-card'>", unsafe_allow_html=True)
        with st.form("finora_signup_form", clear_on_submit=False):
            su_email = st.text_input("Email *", placeholder="you@college.edu")
            su_password = st.text_input(
                "Password *", type="password", placeholder="At least 6 characters"
            )
            su_confirm = st.text_input(
                "Confirm Password *", type="password", placeholder="Repeat your password"
            )
            st.write("")
            su_submit = st.form_submit_button(
                "Create Account", use_container_width=True, type="primary"
            )

        if su_submit:
            _run_signup(su_email, su_password, su_confirm)

        st.markdown("---")
        sw_c1, sw_c2 = st.columns([2, 1.4])
        with sw_c1:
            st.caption("Already have an account?")
        with sw_c2:
            if st.button("Sign In →", key="switch_to_signin", use_container_width=True):
                st.session_state.auth_view_mode = "login"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def _run_signin(email: str, password: str) -> None:
    try:
        with st.spinner("Signing you in…"):
            session = auth.sign_in(email, password)
            auth.ensure_local_identity(session)
    except sc.FinoraSupabaseError as exc:
        st.error(exc.user_message)
        return
    except Exception:
        st.error("Invalid email or password. Please check your credentials and try again.")
        return

    st.session_state[SETUP_NAV_KEY] = False
    display = session.email.split("@")[0] if session.email else "there"
    st.success(f"Welcome back, {display}!")
    st.rerun()


def _run_signup(email: str, password: str, confirm_password: str) -> None:
    try:
        with st.spinner("Creating your account…"):
            session = auth.sign_up(email, password, confirm_password)
            auth.ensure_local_identity(session)
    except sc.FinoraSupabaseError as exc:
        st.error(exc.user_message)
        return
    except Exception:
        st.error("We couldn't create your account just now. Please try again.")
        return

    st.success("Account created! Let's set up your student profile.")
    st.rerun()


# =====================================================================
# PROFILE FORM  (shared by setup and edit)
# =====================================================================

def _render_profile_form(session, profile: Optional[Profile]) -> Optional[Profile]:
    """
    Render the profile form and return the saved profile, or None.

    ``profile`` pre-fills the fields when editing; pass None for first-time setup.
    Returns None when the user has not successfully saved.
    """
    form_key = "finora_profile_edit_form" if profile else "finora_profile_setup_form"
    draft = ProfileDraft.from_profile(profile) if profile else ProfileDraft()
    min_deadline = datetime.date.today()
    max_deadline = min_deadline + datetime.timedelta(days=365 * profiles_mod.MAX_DEADLINE_YEARS_AHEAD)

    goal_suggestions = COMMON_PRIMARY_GOALS + [CUSTOM_GOAL_OPTION]
    if profile and profile.primary_goal and profile.primary_goal not in goal_suggestions:
        goal_index = goal_suggestions.index(CUSTOM_GOAL_OPTION)
    else:
        goal_index = goal_suggestions.index(profile.primary_goal) if profile and profile.primary_goal in goal_suggestions else 0

    st.markdown("<div class='form-card'>", unsafe_allow_html=True)
    with st.form(form_key, clear_on_submit=False):
        st.markdown(
            "<h3 style='margin-bottom: 4px; color: #123C35; font-weight: 800;'>Student details</h3>",
            unsafe_allow_html=True,
        )
        st.caption("Fields marked * are required. Everything here is private to your account.")

        col_a, col_b = st.columns(2)

        with col_a:
            render_section_label("About you")
            name_value = st.text_input(
                "Full Name *",
                value=draft.name,
                placeholder="e.g. Ananya Sharma",
                max_chars=profiles_mod.MAX_NAME_LENGTH,
            )
            college_value = st.text_input(
                "College / University *",
                value=draft.college,
                placeholder="e.g. Delhi University",
                max_chars=profiles_mod.MAX_TEXT_LENGTH,
            )
            course_value = st.text_input(
                "Course / Branch *",
                value=draft.course,
                placeholder="e.g. B.Tech Computer Science",
                max_chars=profiles_mod.MAX_TEXT_LENGTH,
            )
            year_value = st.number_input(
                "Year of Study *",
                min_value=profiles_mod.MIN_YEAR,
                max_value=profiles_mod.MAX_YEAR,
                value=int(draft.year) if draft.year.isdigit() and draft.year else 1,
                step=1,
            )

        with col_b:
            render_section_label("Your monthly money plan")
            income_value = st.number_input(
                "Monthly Income (₹) *",
                min_value=0.0,
                value=float(draft.monthly_income or 0.0),
                step=500.0,
                format="%.2f",
                help="Pocket money, allowance, part-time work — everything you receive in a month.",
            )
            budget_value = st.number_input(
                "Monthly Budget (₹) *",
                min_value=0.0,
                value=float(draft.monthly_budget or 0.0),
                step=500.0,
                format="%.2f",
                help="What you plan to spend each month on food, travel, shopping and so on.",
            )
            savings_value = st.number_input(
                "Monthly Savings Target (₹) *",
                min_value=0.0,
                value=float(draft.monthly_savings_target or 0.0),
                step=100.0,
                format="%.2f",
                help="What you want to put away each month toward your goal.",
            )

        render_section_label("Your primary goal")
        goal_choice = st.selectbox(
            "Primary Financial Goal *",
            goal_suggestions,
            index=goal_index,
            help="Finora uses this to keep your budget and savings plan focused.",
        )
        custom_goal_value = st.text_input(
            "Describe your goal (used only if you picked “Something else”)",
            value="" if goal_choice != CUSTOM_GOAL_OPTION else draft.primary_goal,
            placeholder="e.g. Save for a new laptop",
            max_chars=profiles_mod.MAX_TEXT_LENGTH,
        )

        g_col1, g_col2 = st.columns(2)
        with g_col1:
            goal_amount_value = st.number_input(
                "Goal Amount (₹) *",
                min_value=0.0,
                value=float(draft.goal_amount or 0.0),
                step=1000.0,
                format="%.2f",
            )
        with g_col2:
            deadline_value = st.date_input(
                "Goal Deadline *",
                value=_initial_deadline(draft.goal_deadline, min_deadline, max_deadline),
                min_value=min_deadline,
                max_value=max_deadline,
            )

        submit_label = "Save Changes" if profile else "Create My Profile"
        submitted = st.form_submit_button(submit_label, use_container_width=True, type="primary")

    st.markdown("</div>", unsafe_allow_html=True)

    if not submitted:
        return None

    resolved_goal = (
        custom_goal_value.strip()
        if goal_choice == CUSTOM_GOAL_OPTION
        else goal_choice
    )

    raw_values: Dict[str, Any] = {
        "name": name_value,
        "college": college_value,
        "course": course_value,
        "year": year_value,
        "monthly_income": income_value,
        "monthly_budget": budget_value,
        "monthly_savings_target": savings_value,
        "primary_goal": resolved_goal,
        "goal_amount": goal_amount_value,
        "goal_deadline": deadline_value,
    }

    draft_to_save = ProfileDraft.from_mapping(raw_values)

    try:
        with st.spinner("Saving your profile…"):
            if session is None:
                validated = draft_to_save.validate()
                saved_dict = save_local_profile(validated)
                saved = Profile.from_row(saved_dict)
            elif profile:
                saved = profiles_mod.update_my_profile(session, draft_to_save)
            else:
                saved = profiles_mod.create_my_profile(session, draft_to_save)
    except ProfileValidationError as exc:
        _render_field_errors(exc.errors)
        return None
    except Exception as exc:
        import traceback
        traceback.print_exc()
        user_id = getattr(session, 'user_id', None) if session else None
        user_email = getattr(session, 'email', None) if session else None
        print(f"[Profile save ERROR] user.id={user_id}, user.email={user_email}, error={exc}")
        st.error(f"Profile save failed: {exc}")
        return None

    return saved


def _initial_deadline(
    stored: str, minimum: datetime.date, maximum: datetime.date
) -> datetime.date:
    parsed = profiles_mod._parse_date(stored)
    if parsed is None:
        return minimum + datetime.timedelta(days=180)
    return min(max(parsed, minimum), maximum)


def _render_field_errors(errors: Dict[str, str]) -> None:
    """Render a per-field validation summary below the form."""
    render_notice("Please fix the following to continue:", kind="warn")
    labels = {
        "name": "Full Name",
        "college": "College / University",
        "course": "Course / Branch",
        "year": "Year of Study",
        "monthly_income": "Monthly Income",
        "monthly_budget": "Monthly Budget",
        "monthly_savings_target": "Monthly Savings Target",
        "primary_goal": "Primary Financial Goal",
        "goal_amount": "Goal Amount",
        "goal_deadline": "Goal Deadline",
    }
    for field, message in errors.items():
        st.error(f"{labels.get(field, field)}: {message}")


# =====================================================================
# PROFILE SETUP  (the gate after first sign-in)
# =====================================================================

def render_profile_setup(session) -> None:
    """
    Render the first-time student profile form.

    This is the ``/profile/setup`` equivalent: the dashboard is not reachable
    until a profile exists, which is what guarantees the downstream analytics
    always have income, budget and goal context to work with.
    """
    render_auth_hero(
        "Let's set up your profile",
        "A few details and Finora can personalise your budget and goals.",
    )

    if session.email:
        render_notice(f"Signed in as <b>{session.email}</b>. Your email is managed by your account — you don't need to enter it here.")

    left, right = st.columns([1.5, 1])
    with left:
        saved = _render_profile_form(session, profile=None)
    with right:
        _render_plan_preview()

    if saved is not None:
        st.session_state[SETUP_NAV_KEY] = True
        st.success("🎉 Profile created! Taking you to your dashboard…")
        st.rerun()


def _render_plan_preview() -> None:
    """Explain what Finora will do with these numbers."""
    st.markdown("<div class='form-card'>", unsafe_allow_html=True)
    st.markdown(
        "<h3 style='margin-bottom: 12px; color: #123C35; font-weight: 800;'>What Finora does with this</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
📊 **Budget tracking** — we compare your monthly spending against your budget
🎯 **Goal progress** — we work out how much to save each month to hit your deadline
💡 **Future insights** — this is the context Finora's assistant will use to answer
"Can I afford this?", "Where am I overspending?" and "Will I make my goal?"
"""
    )
    st.caption("You can change any of this later from your profile page.")
    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================================
# PROFILE PAGE  (view + edit, reachable from the sidebar)
# =====================================================================

def render_profile_page(session, profile: Profile) -> None:
    """Render the student's profile: summary, plan health, and the edit form."""
    st.markdown(
        "<h1 style='font-size: 2.5rem; font-weight: 800; color: #0B2920; margin-bottom: 2px; letter-spacing: -0.5px;'>My Profile</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color: #5C6660; font-size: 1.1rem; font-weight: 500; margin-bottom: 24px;'>Your details power every insight in Finora.</p>",
        unsafe_allow_html=True,
    )

    render_profile_identity(
        profile.name,
        f"{profile.course} · {format_study_year(profile.year)} · {profile.college}",
    )

    render_section_label("Study")
    render_profile_details([
        ("College", profile.college),
        ("Course", profile.course),
        ("Year of study", format_study_year(profile.year)),
        ("Email", profile.email or "—"),
    ])

    st.write("")
    render_section_label("Monthly money plan")
    render_profile_details([
        ("Monthly income", format_currency(profile.monthly_income)),
        ("Monthly budget", format_currency(profile.monthly_budget)),
        ("Savings target", format_currency(profile.monthly_savings_target)),
        ("Savings rate", f"{profiles_mod.monthly_plan(profile)['savings_rate_pct']:.1f}%"),
    ])

    _render_goal_progress(profile)
    _render_edit_section(session, profile)


def _render_goal_progress(profile: Profile) -> None:
    """Show the primary goal and whether the current plan reaches it in time."""
    active_goal = _find_profile_goal(profile)
    projection = profiles_mod.project_goal_completion(
        profile, saved_so_far=active_goal["saved_amount"] if active_goal else 0.0
    )

    deadline = profiles_mod.parse_date(profile.goal_deadline)
    deadline_long = deadline.strftime("%d %b %Y") if deadline else "—"
    deadline_month = deadline.strftime("%B %Y") if deadline else "your deadline"

    st.write("")
    st.markdown(f"""
    <div class="pf-goal-card">
        <div class="pf-goal-title">🎯 {profile.primary_goal}</div>
        <div style="font-size: 0.88rem; color: #42504A; font-weight: 600; margin-bottom: 10px;">
            Target {format_currency(projection['target_amount'])} · Deadline {deadline_long}
        </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    with cols[0]:
        st.markdown(
            f"<div class='metric-tile'><div class='metric-tile-label'>Saved so far</div>"
            f"<div class='metric-tile-amount'>{format_currency(projection['saved'])}</div>"
            f"<div class='metric-tile-sub'>{projection['progress_pct']:.0f}% of target</div></div>",
            unsafe_allow_html=True,
        )
    with cols[1]:
        remaining_text = (
            f"{format_currency(projection['required_per_month'])}/mo"
            if projection["required_per_month"] is not None
            else "—"
        )
        st.markdown(
            f"<div class='metric-tile'><div class='metric-tile-label'>Needed each month</div>"
            f"<div class='metric-tile-amount'>{remaining_text}</div>"
            f"<div class='metric-tile-sub'>to hit your deadline</div></div>",
            unsafe_allow_html=True,
        )
    with cols[2]:
        badge = {
            "achieved": ("#E4F7EC", "#0C6B3F", "✓ Goal reached"),
            "on_track": ("#E4F7EC", "#0C6B3F", "✓ On track"),
            "behind": ("#FFF5F4", "#AE221A", "⚠️ Needs more saving"),
            "no_deadline": ("#F3EEDC", "#7A6820", "Add a deadline"),
        }.get(projection["status"], ("#F3EEDC", "#7A6820", "—"))
        bg, fg, label = badge
        st.markdown(
            f"<div class='metric-tile'><div class='metric-tile-label'>Plan status</div>"
            f"<div style='background:{bg}; color:{fg}; border-radius:12px; padding:10px 14px; font-weight:800; font-size:1.05rem; margin-top:4px;'>{label}</div>"
            f"<div class='metric-tile-sub'>targeting {format_currency(projection['planned_per_month'])}/mo</div></div>",
            unsafe_allow_html=True,
        )

    if projection["status"] == "behind" and projection["required_per_month"]:
        render_notice(
            f"Saving {format_currency(projection['planned_per_month'])} a month won't reach "
            f"{profile.primary_goal} by {profiles_mod._parse_date(profile.goal_deadline).strftime('%B %Y') if profiles_mod._parse_date(profile.goal_deadline) else 'your deadline'}. "
            f"Aim for about {format_currency(projection['required_per_month'])} a month, or move the deadline later.",
            kind="warn",
        )


def _find_profile_goal(profile: Profile) -> Optional[Dict[str, Any]]:
    """Match the profile's primary goal against a real Bucket List goal, if any."""
    local_user_id = st.session_state.get("finora_local_user_id")
    if local_user_id is None:
        return None
    target = profile.primary_goal.strip().lower()
    for goal in get_user_goals(local_user_id):
        if goal["name"].strip().lower() == target:
            return goal
    return None


def _render_edit_section(session, profile: Profile) -> None:
    """Collapsible edit form. Saving reruns the page with fresh data."""
    st.write("")
    with st.expander("✏️ Edit profile details", expanded=False):
        st.caption("Update your college, budget, savings target or goal at any time.")
        saved = _render_profile_form(session, profile=profile)
        if saved is not None:
            st.success("✅ Profile updated.")
            st.rerun()


# =====================================================================
# SIDEBAR ACCOUNT BLOCK
# =====================================================================

def render_sidebar_account(session, profile: Optional[Profile]) -> None:
    """Render the signed-in student and a sign-out button in the sidebar."""
    if profile is None:
        return

    allocated = get_total_allocated_to_goals(st.session_state.get("finora_local_user_id", 0))
    st.markdown("---")
    st.markdown(
        f"""
        <div class="sidebar-summary-card">
            <div class="sidebar-summary-title">Student Profile</div>
            <div class="sidebar-val-group">
                <div class="sidebar-val-label">Name</div>
                <div class="sidebar-val-amount" style="font-size: 1.05rem;">{profile.name}</div>
            </div>
            <div class="sidebar-val-group">
                <div class="sidebar-val-label">{format_study_year(profile.year)} · {profile.course}</div>
            </div>
            <div class="sidebar-val-group" style="margin-bottom: 0;">
                <div class="sidebar-val-label">Monthly budget</div>
                <div class="sidebar-val-amount" style="font-size: 1.15rem;">{format_currency(profile.monthly_budget)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("👤 My Profile", use_container_width=True):
        st.session_state.nav_choice = "👤 My Profile"
        st.rerun()

    if st.button("Sign out", use_container_width=True):
        auth.sign_out()
        st.session_state.pop("finora_local_user_id", None)
        st.session_state.pop(SETUP_NAV_KEY, None)
        st.rerun()