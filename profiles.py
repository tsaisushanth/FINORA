"""
Student profile domain logic for Finora.

This module owns three things:

1. :class:`ProfileDraft` — the validated shape of the profile setup / edit form.
2. Ownership-scoped persistence. The profile id is always the Supabase user id
   from the verified session, so a profile id can never be supplied by the form.
3. Pure derived helpers (budget utilisation, affordability, goal projection).
   These exist now, without any AI, so that the later Finora assistant has clean
   numbers to reason about instead of re-deriving them from raw rows.

The raw row shape lives in :mod:`supabase_client`; this module never talks to
the network directly.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, Dict, Optional

import supabase_client as sc
from supabase_client import Profile

# Bounds used by both the form and the database CHECK constraints.
MAX_NAME_LENGTH = 80
MAX_TEXT_LENGTH = 120
MIN_YEAR = 1
MAX_YEAR = 10
MAX_DEADLINE_YEARS_AHEAD = 10

#: Suggestions offered in the profile form's "Primary Goal" dropdown.
COMMON_PRIMARY_GOALS = [
    "Buy a laptop",
    "Pay off education fees",
    "Emergency fund",
    "Trip or travel",
    "New phone",
    "Party & events",
    "Course fees / certification",
    "Hostel & living costs",
]

CUSTOM_GOAL_OPTION = "✏️ Something else"


# =====================================================================
# ERRORS
# =====================================================================

class ProfileValidationError(sc.FinoraSupabaseError):
    """One or more form fields are invalid. ``errors`` maps field -> message."""

    default_user_message = "Please fix the highlighted fields."

    def __init__(self, errors: Dict[str, str]) -> None:
        self.errors = errors
        super().__init__("Please fix the highlighted fields.")


# =====================================================================
# DRAFT + VALIDATION
# =====================================================================

@dataclass(frozen=True)
class ProfileDraft:
    """
    Raw profile form input, as strings.

    Validation happens here rather than in the widget layer so the same rules
    apply to setup, to editing, and to any future programmatic caller.
    """

    name: str = ""
    college: str = ""
    course: str = ""
    year: str = ""
    monthly_income: str = ""
    monthly_budget: str = ""
    monthly_savings_target: str = ""
    primary_goal: str = ""
    goal_amount: str = ""
    goal_deadline: str = ""

    # -- constructors ----------------------------------------------------

    @staticmethod
    def from_profile(profile: Profile) -> "ProfileDraft":
        """Build a draft pre-filled from an existing profile."""
        return ProfileDraft(
            name=profile.name,
            college=profile.college,
            course=profile.course,
            year=str(profile.year),
            monthly_income=_number_to_text(profile.monthly_income),
            monthly_budget=_number_to_text(profile.monthly_budget),
            monthly_savings_target=_number_to_text(profile.monthly_savings_target),
            primary_goal=profile.primary_goal,
            goal_amount=_number_to_text(profile.goal_amount),
            goal_deadline=profile.goal_deadline,
        )

    @staticmethod
    def from_mapping(raw: Dict[str, Any]) -> "ProfileDraft":
        """Build a draft from an arbitrary mapping (e.g. form widget values)."""
        return ProfileDraft(
            name=str(raw.get("name", "") or ""),
            college=str(raw.get("college", "") or ""),
            course=str(raw.get("course", "") or ""),
            year=str(raw.get("year", "") or ""),
            monthly_income=str(raw.get("monthly_income", "") or ""),
            monthly_budget=str(raw.get("monthly_budget", "") or ""),
            monthly_savings_target=str(raw.get("monthly_savings_target", "") or ""),
            primary_goal=str(raw.get("primary_goal", "") or ""),
            goal_amount=str(raw.get("goal_amount", "") or ""),
            goal_deadline=str(raw.get("goal_deadline", "") or ""),
        )

    # -- validation ------------------------------------------------------

    def validate(self, today: Optional[datetime.date] = None) -> Dict[str, Any]:
        """
        Return clean, typed values ready to persist.

        Raises :class:`ProfileValidationError` with a per-field message map.
        """
        today = today or datetime.date.today()
        errors: Dict[str, str] = {}

        name = self.name.strip()
        if not name:
            errors["name"] = "Please enter your name."
        elif len(name) > MAX_NAME_LENGTH:
            errors["name"] = f"Name must be {MAX_NAME_LENGTH} characters or fewer."

        college = self.college.strip()
        if not college:
            errors["college"] = "Please enter your college or university."
        elif len(college) > MAX_TEXT_LENGTH:
            errors["college"] = f"College must be {MAX_TEXT_LENGTH} characters or fewer."

        course = self.course.strip()
        if not course:
            errors["course"] = "Please enter your course."
        elif len(course) > MAX_TEXT_LENGTH:
            errors["course"] = f"Course must be {MAX_TEXT_LENGTH} characters or fewer."

        year = _parse_year(self.year)
        if year is None:
            errors["year"] = f"Enter your year of study as a number from {MIN_YEAR} to {MAX_YEAR}."
        elif not MIN_YEAR <= year <= MAX_YEAR:
            errors["year"] = f"Year must be between {MIN_YEAR} and {MAX_YEAR}."

        income = _parse_amount(self.monthly_income)
        if income is None:
            errors["monthly_income"] = "Enter your monthly income as a number."
        elif income < 0:
            errors["monthly_income"] = "Monthly income cannot be negative."

        budget = _parse_amount(self.monthly_budget)
        if budget is None:
            errors["monthly_budget"] = "Enter your monthly budget as a number."
        elif budget <= 0:
            errors["monthly_budget"] = "Monthly budget must be greater than ₹0."

        savings = _parse_amount(self.monthly_savings_target)
        if savings is None:
            errors["monthly_savings_target"] = "Enter your savings target as a number."
        elif savings < 0:
            errors["monthly_savings_target"] = "Savings target cannot be negative."

        goal = self.primary_goal.strip()
        if not goal:
            errors["primary_goal"] = "Tell us your main financial goal."
        elif len(goal) > MAX_TEXT_LENGTH:
            errors["primary_goal"] = f"Goal must be {MAX_TEXT_LENGTH} characters or fewer."

        goal_amount = _parse_amount(self.goal_amount)
        if goal_amount is None:
            errors["goal_amount"] = "Enter your goal amount as a number."
        elif goal_amount <= 0:
            errors["goal_amount"] = "Goal amount must be greater than ₹0."

        deadline = _parse_date(self.goal_deadline)
        if deadline is None:
            errors["goal_deadline"] = "Choose a target date for your goal."
        elif deadline < today:
            errors["goal_deadline"] = "Your goal date needs to be today or later."
        elif deadline > _add_years(today, MAX_DEADLINE_YEARS_AHEAD):
            errors["goal_deadline"] = f"Pick a date within the next {MAX_DEADLINE_YEARS_AHEAD} years."

        # A student cannot plan to spend and save more than they earn. Skipped
        # when income is 0, because that means "not declared yet".
        if (
            not errors
            and income is not None
            and income > 0
            and budget is not None
            and savings is not None
            and budget + savings > income
        ):
            errors["monthly_budget"] = (
                "Budget plus savings target can't be more than your monthly income. "
                "Try lowering the budget or the savings target."
            )

        if errors:
            raise ProfileValidationError(errors)

        return {
            "name": name,
            "college": college,
            "course": course,
            "year": year,
            "monthly_income": round(float(income or 0.0), 2),
            "monthly_budget": round(float(budget or 0.0), 2),
            "monthly_savings_target": round(float(savings or 0.0), 2),
            "primary_goal": goal,
            "goal_amount": round(float(goal_amount or 0.0), 2),
            "goal_deadline": deadline.strftime("%Y-%m-%d"),
        }


# =====================================================================
# PARSING HELPERS
# =====================================================================

def _parse_amount(raw: Any) -> Optional[float]:
    """Parse a money input. Returns None when it is not a usable number."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return float(raw)

    text = str(raw).strip().replace(",", "").replace("₹", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_year(raw: Any) -> Optional[int]:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _parse_date(raw: Any) -> Optional[datetime.date]:
    if raw is None:
        return None
    if isinstance(raw, datetime.datetime):
        return raw.date()
    if isinstance(raw, datetime.date):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


parse_date = _parse_date


def _add_years(base: datetime.date, years: int) -> datetime.date:
    try:
        return base.replace(year=base.year + years)
    except ValueError:  # 29 Feb
        return base.replace(year=base.year + years, day=28)


def _number_to_text(value: float) -> str:
    """Format a stored amount for round-tripping through the form."""
    amount = round(float(value or 0.0), 2)
    return str(int(amount)) if amount == int(amount) else f"{amount:.2f}"


# =====================================================================
# PERSISTENCE  (identity always comes from the verified session)
# =====================================================================

def fetch_my_profile(session) -> Optional[Profile]:
    """
    Return the signed-in student's profile, or None when setup is pending.

    Raises a FinoraSupabaseError subclass on configuration / network problems.
    """
    return sc.fetch_profile(session.access_token, session.user_id)


def create_my_profile(session, draft: ProfileDraft) -> Profile:
    """
    Validate and save a new profile for the signed-in student.

    The email comes from Supabase Auth, never from the form. The id is the
    session user id, so RLS decides whether the insert is allowed.
    """
    values = draft.validate()
    email = session.email or ""
    try:
        return sc.insert_profile(session.access_token, session.user_id, email, values)
    except sc.ProfileAlreadyExistsError:
        # Lost a race with a double submit — treat it as success.
        existing = sc.fetch_profile(session.access_token, session.user_id)
        if existing is not None:
            return existing
        raise


def update_my_profile(session, draft: ProfileDraft) -> Profile:
    """Validate and persist changes to the signed-in student's own profile."""
    values = draft.validate()
    return sc.update_profile(session.access_token, session.user_id, values)


def has_profile(session) -> bool:
    """True when the signed-in student has already completed profile setup."""
    return fetch_my_profile(session) is not None


def email_display_name(profile: Optional[Profile]) -> str:
    """Best-effort display name for greeting the student."""
    if profile and profile.name.strip():
        return profile.name.strip().split()[0]
    return "there"


# =====================================================================
# DERIVED FINANCE HELPERS
# =====================================================================
# Pure functions over a Profile. These are the building blocks the upcoming
# Finora assistant, budget warnings and forecasting will use. No AI involved.

def monthly_plan(profile: Profile) -> Dict[str, Any]:
    """Split monthly income into its planned buckets."""
    income = float(profile.monthly_income or 0.0)
    budget = float(profile.monthly_budget or 0.0)
    savings = float(profile.monthly_savings_target or 0.0)
    planned = budget + savings
    return {
        "income": round(income, 2),
        "budget": round(budget, 2),
        "savings_target": round(savings, 2),
        "planned": round(planned, 2),
        "unallocated": round(income - planned, 2),
        "savings_rate_pct": round((savings / income) * 100, 2) if income > 0 else 0.0,
        "is_balanced": income <= 0 or planned <= income,
    }


def budget_utilization(profile: Profile, spent_this_month: float) -> Dict[str, Any]:
    """How much of the monthly budget is used up. Never divides by zero."""
    budget = float(profile.monthly_budget or 0.0)
    spent = round(max(0.0, float(spent_this_month or 0.0)), 2)
    remaining = round(budget - spent, 2)

    if budget <= 0:
        pct = 0.0
    else:
        pct = round((spent / budget) * 100, 2)

    return {
        "budget": round(budget, 2),
        "spent": spent,
        "remaining": remaining,
        "used_pct": pct,
        "is_over_budget": spent > budget if budget > 0 else False,
        # A shared constant so the UI and the future assistant agree.
        "status": _budget_status(pct, budget),
    }


def _budget_status(pct: float, budget: float) -> str:
    if budget <= 0:
        return "unknown"
    if pct >= 100:
        return "over"
    if pct >= 85:
        return "warning"
    if pct >= 60:
        return "healthy"
    return "on_track"


def can_afford(
    profile: Profile,
    cost: float,
    spent_this_month: float = 0.0,
    available_balance: float = 0.0,
) -> Dict[str, Any]:
    """
    Answer "can I afford this?" using both the monthly budget and real cash.

    ``available_balance`` is the wallet balance; pass 0 when unknown, in which
    case only the budget side of the answer is used.
    """
    price = round(max(0.0, float(cost or 0.0)), 2)
    plan = monthly_plan(profile)
    budget_room = round(plan["budget"] - max(0.0, float(spent_this_month or 0.0)), 2)
    balance = round(max(0.0, float(available_balance or 0.0)), 2)

    within_budget = price <= budget_room
    within_balance = price <= balance
    can_buy = within_budget and within_balance

    if can_buy:
        reason = "This fits within your monthly budget and your wallet balance."
    elif not within_budget and not within_balance:
        reason = "This is more than your remaining budget and your wallet balance."
    elif not within_budget:
        reason = (
            f"This exceeds your remaining monthly budget of ₹{budget_room:,.0f} "
            f"for {profile.name.split()[0] if profile.name else 'you'}."
        )
    else:
        reason = f"Your wallet only has ₹{balance:,.0f} available right now."

    return {
        "cost": price,
        "can_afford": can_buy,
        "budget_room": budget_room,
        "available_balance": balance,
        "after_purchase_budget": round(budget_room - price, 2),
        "reason": reason,
    }


def project_goal_completion(
    profile: Profile,
    saved_so_far: float = 0.0,
    today: Optional[datetime.date] = None,
) -> Dict[str, Any]:
    """
    Project when the primary goal will be reached at the planned savings rate.

    Returns months remaining, the monthly amount required, and whether the
    current plan is on track.
    """
    today = today or datetime.date.today()
    target = float(profile.goal_amount or 0.0)
    saved = max(0.0, float(saved_so_far or 0.0))
    remaining = round(max(0.0, target - saved), 2)

    deadline = _parse_date(profile.goal_deadline)
    months_left: Optional[int] = None
    if deadline and deadline > today:
        months_left = (deadline.year - today.year) * 12 + (deadline.month - today.month)

    monthly_saving = float(profile.monthly_savings_target or 0.0)
    required_per_month = (
        round(remaining / months_left, 2) if months_left and remaining > 0 else None
    )
    projected_months = (
        int(-(-remaining // monthly_saving)) if monthly_saving > 0 and remaining > 0 else None
    )

    if remaining <= 0:
        on_track: Optional[bool] = True
        status = "achieved"
    elif required_per_month is None:
        on_track = None
        status = "no_deadline"
    else:
        on_track = monthly_saving >= required_per_month
        status = "on_track" if on_track else "behind"

    projected_date = None
    if projected_months:
        year = today.year + (today.month - 1 + projected_months) // 12
        month = (today.month - 1 + projected_months) % 12 + 1
        try:
            projected_date = today.replace(year=year, month=month)
        except ValueError:
            projected_date = today

    return {
        "goal": profile.primary_goal,
        "target_amount": round(target, 2),
        "saved": round(saved, 2),
        "remaining": remaining,
        "progress_pct": round((saved / target) * 100, 2) if target > 0 else 0.0,
        "months_left": months_left,
        "deadline": profile.goal_deadline,
        "required_per_month": required_per_month,
        "planned_per_month": round(monthly_saving, 2),
        "on_track": on_track,
        "status": status,
        "projected_completion": projected_date.strftime("%Y-%m-%d") if projected_date else None,
    }