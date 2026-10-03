import datetime
from typing import Dict, List, Optional

from utils import format_currency, get_goal_category_icon


# ---------------------------------------------------------------------
# CALCULATION HELPERS
# ---------------------------------------------------------------------

def calculate_goal_progress(goal: Dict) -> float:
    """Return progress percentage (0-100), never exceeding 100."""
    target = float(goal.get("target_amount") or 0.0)
    saved = float(goal.get("saved_amount") or 0.0)
    if target <= 0:
        return 0.0
    pct = (saved / target) * 100
    return max(0.0, min(100.0, pct))


def calculate_remaining_amount(goal: Dict) -> float:
    """Return remaining amount to reach the target, never negative."""
    target = float(goal.get("target_amount") or 0.0)
    saved = float(goal.get("saved_amount") or 0.0)
    return max(0.0, target - saved)


def calculate_required_monthly_saving(goal: Dict) -> Optional[float]:
    """
    Compute approximately how much to save per month to hit the target by the
    target date. Returns None if no target date, no remaining amount, or invalid date.
    """
    target_date_str = goal.get("target_date")
    if not target_date_str:
        return None
    try:
        target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

    remaining = calculate_remaining_amount(goal)
    if remaining <= 0:
        return None

    today = datetime.date.today()
    if target_date <= today:
        return None

    months_left = (target_date.year - today.year) * 12 + (target_date.month - today.month)
    if months_left <= 0:
        months_left = 1

    return remaining / months_left


def days_remaining(goal: Dict) -> Optional[int]:
    """Return full days until the target date, or None if not set / invalid / past."""
    target_date_str = goal.get("target_date")
    if not target_date_str:
        return None
    try:
        target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    today = datetime.date.today()
    if target_date <= today:
        return None
    return (target_date - today).days


def format_target_date(goal: Dict) -> str:
    """Human-friendly target date string (e.g. 'December 2026')."""
    target_date_str = goal.get("target_date")
    if not target_date_str:
        return ""
    try:
        target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
        return target_date.strftime("%B %Y")
    except (ValueError, TypeError):
        return ""


def format_target_date_short(goal: Dict) -> str:
    """Short target date string (e.g. 'Dec 2026')."""
    target_date_str = goal.get("target_date")
    if not target_date_str:
        return ""
    try:
        target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
        return target_date.strftime("%b %Y")
    except (ValueError, TypeError):
        return ""


def get_goal_summary(goals: List[Dict]) -> Dict:
    """Compute summary statistics across a list of goals."""
    total_goals = len(goals)
    active = sum(1 for g in goals if g.get("status") == "Active")
    completed = sum(1 for g in goals if g.get("status") == "Completed")
    total_target = sum(float(g.get("target_amount") or 0.0) for g in goals if g.get("status") != "Archived")
    total_saved = sum(float(g.get("saved_amount") or 0.0) for g in goals if g.get("status") != "Archived")
    paused = sum(1 for g in goals if g.get("status") == "Paused")
    total_remaining = max(0.0, total_target - total_saved)
    overall_progress = (total_saved / total_target * 100) if total_target > 0 else 0.0

    top_priority = None
    closest_goal = None
    for g in goals:
        if g.get("status") == "Completed" or g.get("status") == "Archived":
            continue
        progress = calculate_goal_progress(g)
        if top_priority is None or _priority_rank(g.get("priority")) > _priority_rank(top_priority.get("priority")):
            top_priority = g
        if closest_goal is None or progress > calculate_goal_progress(closest_goal):
            closest_goal = g

    return {
        "total_goals": total_goals,
        "active": active,
        "paused": paused,
        "completed": completed,
        "total_target": total_target,
        "total_saved": total_saved,
        "total_remaining": total_remaining,
        "overall_progress": overall_progress,
        "top_priority": top_priority,
        "closest_goal": closest_goal,
    }


def _priority_rank(priority: Optional[str]) -> int:
    return {"High": 3, "Medium": 2, "Low": 1}.get(priority, 0)


# ---------------------------------------------------------------------
# COLOR-CODED PROGRESS STAGES
# ---------------------------------------------------------------------

def progress_stage(progress: float) -> Dict:
    """
    Map a progress percentage to a visual stage.
    Returns dict with 'stage' (CSS class suffix), 'label',
    'bar' (bar colour) and 'text' (text colour, dark enough for white bg).
    """
    if progress >= 100:
        return {"stage": "5", "label": "Completed", "bar": "#16A34A", "text": "#137A47"}
    if progress >= 76:
        return {"stage": "4", "label": "Almost there", "bar": "#8B5CF6", "text": "#6D28D9"}
    if progress >= 51:
        return {"stage": "3", "label": "Good progress", "bar": "#2BB3A3", "text": "#0D7D6C"}
    if progress >= 26:
        return {"stage": "2", "label": "Progressing", "bar": "#4F8BFF", "text": "#3557C7"}
    if progress > 0:
        return {"stage": "1", "label": "Just started", "bar": "#8AA0B5", "text": "#5B6B7B"}
    return {"stage": "0", "label": "Not started", "bar": "#D3D9D5", "text": "#56635D"}


# ---------------------------------------------------------------------
# RENDERING HELPERS
# ---------------------------------------------------------------------

def render_progress_bar(progress: float, show_caption: bool = True) -> str:
    """Render a color-coded, accessible progress bar with percentage label."""
    pct = max(0.0, min(100.0, float(progress)))
    stage = progress_stage(pct)
    fill = f'<div class="g-fill g-stage-{stage["stage"]}" style="width: {pct}%;"></div>'
    caption = (
        f'<div class="g-progress-caption"><span>{stage["label"]}</span>'
        f'<b>{pct:.0f}%</b></div>'
    ) if show_caption else ""
    return (
        f'<div class="g-bar">{fill}</div>'
        f'{caption}'
    )


def render_goal_summary(summary: Dict) -> str:
    """Render the five summary stat cards for the Bucket List header."""
    return f"""
    <div class="g-stats">
        <div class="g-stat">
            <div class="g-stat-head">
                <span class="g-stat-label">Total Goals</span>
                <span class="g-stat-icon">🎯</span>
            </div>
            <div class="g-stat-value">{summary['total_goals']}</div>
            <div class="g-stat-sub">{summary['active']} active · {summary['completed']} done</div>
        </div>
        <div class="g-stat">
            <div class="g-stat-head">
                <span class="g-stat-label">Total Saved</span>
                <span class="g-stat-icon">🐷</span>
            </div>
            <div class="g-stat-value" style="color:#0F7A4F;">{format_currency(summary['total_saved'])}</div>
            <div class="g-stat-sub">Kept safe toward goals</div>
        </div>
        <div class="g-stat">
            <div class="g-stat-head">
                <span class="g-stat-label">Total Target</span>
                <span class="g-stat-icon">📌</span>
            </div>
            <div class="g-stat-value">{format_currency(summary['total_target'])}</div>
            <div class="g-stat-sub">Across all goals</div>
        </div>
        <div class="g-stat">
            <div class="g-stat-head">
                <span class="g-stat-label">Remaining</span>
                <span class="g-stat-icon">⏳</span>
            </div>
            <div class="g-stat-value">{format_currency(summary['total_remaining'])}</div>
            <div class="g-stat-sub">Still to save</div>
        </div>
        <div class="g-stat">
            <div class="g-stat-head">
                <span class="g-stat-label">Overall Progress</span>
                <span class="g-stat-icon">📈</span>
            </div>
            <div class="g-stat-value">{summary['overall_progress']:.0f}%</div>
            <div class="g-stat-sub">Saved toward targets</div>
        </div>
    </div>
    """


def render_goal_card(goal: Dict) -> str:
    """Build a polished, accessible HTML card for a single goal."""
    progress = calculate_goal_progress(goal)
    remaining = calculate_remaining_amount(goal)
    saved = float(goal.get("saved_amount") or 0.0)
    target = float(goal.get("target_amount") or 0.0)
    status = goal.get("status", "Active")
    priority = goal.get("priority", "Medium")

    icon = get_goal_category_icon(goal.get("category", "Other"))
    stage = progress_stage(progress)

    card_class = "goal-card"
    if status == "Completed":
        card_class += " completed"
    elif status == "Paused":
        card_class += " paused"

    # Status + priority badges
    gb_status = f"gb-{status.lower()}"
    gb_pri = f"gb-{priority.lower()}"
    badges = (
        f'<span class="gb {gb_status}">{status.upper()}</span>'
        f'<span class="gb {gb_pri}">{priority} priority</span>'
    )

    progress_html = render_progress_bar(progress)

    # Deadline strip: target date, days left, monthly saving
    deadline_parts = []
    target_short = format_target_date_short(goal)
    days = days_remaining(goal)
    if target_short:
        deadline_parts.append(f"🗓 Target: <b>{target_short}</b>")
    if days is not None:
        deadline_parts.append(f"⏳ <b>{days} days</b> left")
    if status == "Active":
        monthly = calculate_required_monthly_saving(goal)
        if monthly is not None:
            deadline_parts.append(f"💡 Save <b>{format_currency(round(monthly))}/mo</b>")

    deadline_html = ""
    if deadline_parts:
        deadline_html = (
            '<div class="g-deadline">' + "".join(f"<span>{p}</span>" for p in deadline_parts) + "</div>"
        )

    completed_html = ""
    if status == "Completed":
        completed_html = (
            '<div class="goal-completed-flag">✓ Goal Completed — 🎉 You reached this goal!</div>'
        )

    paused_html = ""
    if status == "Paused":
        paused_html = '<div class="goal-paused-flag">⏸ This goal is paused. Resume to keep saving.</div>'

    desc_html = ""
    if goal.get("description"):
        desc_html = f'<div class="g-desc">{goal["description"]}</div>'

    return f"""
    <div class="{card_class}">
        <div class="goal-card-top">
            <div class="g-icon">{icon}</div>
            <div>
                <div class="goal-card-name">{goal['name']}</div>
                <div class="goal-card-cat">{icon} {goal.get('category', 'Other')}</div>
            </div>
            <div class="g-badges">{badges}</div>
        </div>
        <div class="goal-amount">
            <span class="g-saved">{format_currency(saved)}</span>
            <span class="g-target">/ {format_currency(target)}</span>
            <span class="g-percent" style="color: {stage['text']};">{progress:.0f}%</span>
        </div>
        <div class="g-remaining">Remaining: <b>{format_currency(remaining)}</b></div>
        {progress_html}
        {deadline_html}
        {completed_html}
        {paused_html}
        {desc_html}
    </div>
    """


def generate_goal_insights(goals: List[Dict]) -> List[str]:
    """
    Generate simple, understandable insights using the user's actual goal data.
    Avoids unrealistic financial predictions.
    """
    insights: List[str] = []
    active_goals = [g for g in goals if g.get("status") == "Active"]

    if not goals:
        return insights

    # Progress toward a specific goal
    for g in goals:
        progress = calculate_goal_progress(g)
        if 0 < progress < 25 and g.get("status") == "Active":
            insights.append(
                f"🎯 **{g['name']}** — You are {progress:.0f}% of the way toward this goal. Every contribution counts. Keep going!"
            )
        elif 25 <= progress < 75 and g.get("status") == "Active":
            insights.append(
                f"🎯 **{g['name']}** — You are **{progress:.0f}%** of the way toward your {g['name']} goal. Great momentum!"
            )
        elif progress >= 75 and progress < 100 and g.get("status") == "Active":
            remaining = calculate_remaining_amount(g)
            insights.append(
                f"🔥 **Almost there!** — You need **{format_currency(remaining)}** more to complete your {g['name']} goal."
            )

    if not active_goals:
        completed_count = sum(1 for g in goals if g.get("status") == "Completed")
        if completed_count:
            insights.append(
                f"🏆 You have completed **{completed_count}** goal{'s' if completed_count != 1 else ''}. Time to celebrate your savings wins!"
            )
        else:
            insights.append(
                "💡 Create your first goal to start saving toward something you want."
            )
        return insights

    # Multiple active goals and prioritization
    if len(active_goals) >= 3:
        high_count = sum(1 for g in active_goals if g.get("priority") == "High")
        if high_count:
            insights.append(
                f"📌 You have **{len(active_goals)} active goals**, including **{high_count} High priority** goal{'s' if high_count != 1 else ''}. Consider focusing your contributions on the highest priority one first."
            )
        else:
            insights.append(
                f"📌 You have **{len(active_goals)} active goals**. Try focusing on one goal at a time for faster progress."
            )

    # Closest to completion nudge
    closest = None
    for g in active_goals:
        if g.get("status") != "Active":
            continue
        p = calculate_goal_progress(g)
        if closest is None or p > closest[1]:
            closest = (g, p)
    if closest and closest[1] > 0:
        insights.append(
            f"⚡ Your **closest goal** is **{closest[0]['name']}** at **{closest[1]:.0f}%** — a little more and it's done!"
        )

    # Monthly saving suggestion (only with a real target date)
    suggested_goals = []
    for g in active_goals:
        monthly = calculate_required_monthly_saving(g)
        if monthly is not None:
            suggested_goals.append((g, monthly))
    if suggested_goals:
        g, monthly = min(suggested_goals, key=lambda x: x[1])
        insights.append(
            f"🗓 To reach **{g['name']}** by its target date, save about **{format_currency(round(monthly))}/month**."
        )

    return insights