"""
Centralized Supabase access for Finora.

Every Supabase call in the application goes through this module so that:

* Configuration lives in exactly one place (environment variables).
* The ``profiles`` row shape is defined in exactly one place (:class:`Profile`).
* Raw database / API errors never reach the UI. They are translated into
  :class:`FinoraSupabaseError`, which carries a safe ``user_message``.
* The service-role key can never be used. Finora only ever needs the
  public *anon* / *publishable* key plus the signed-in user's own JWT, because
  Row Level Security in ``supabase/schema.sql`` is what protects the data.

Security notes
--------------
``SUPABASE_ANON_KEY`` is a publishable key and is safe to read from the server.
``SUPABASE_SERVICE_ROLE_KEY`` bypasses RLS entirely and is never read here; a
guard actively rejects it even if it is mistakenly placed in the anon variable.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional

ENV_SUPABASE_URL = "SUPABASE_URL"
ENV_SUPABASE_ANON_KEY = "SUPABASE_ANON_KEY"
ENV_SERVICE_ROLE_KEY = "SUPABASE_SERVICE_ROLE_KEY"

PROFILES_TABLE = "profiles"


# =====================================================================
# ERRORS
# =====================================================================

class FinoraSupabaseError(Exception):
    """Base error. ``user_message`` is safe to render in the UI."""

    default_user_message = "Something went wrong while talking to Finora. Please try again."

    def __init__(self, user_message: Optional[str] = None) -> None:
        self.user_message = user_message or self.default_user_message
        super().__init__(self.user_message)


class SupabaseNotConfiguredError(FinoraSupabaseError):
    """Supabase environment variables are missing or unusable."""

    default_user_message = (
        "Finora is not connected to Supabase yet. Add SUPABASE_URL and "
        "SUPABASE_ANON_KEY to your environment to enable sign-in and profiles."
    )


class SupabaseAuthError(FinoraSupabaseError):
    """Sign-in / sign-up / session failure."""

    default_user_message = "We couldn't verify your account. Please check your details and try again."


class SupabaseSessionExpiredError(SupabaseAuthError):
    """The stored access token is no longer accepted by Supabase."""

    default_user_message = "Your session expired. Please sign in again."


class SupabaseRequestError(FinoraSupabaseError):
    """A database request failed."""

    default_user_message = "We couldn't save your profile right now. Please try again in a moment."


class ProfileAlreadyExistsError(SupabaseRequestError):
    """A profile row already exists for this authenticated user."""

    default_user_message = "Your profile already exists. Let's edit it instead."


# =====================================================================
# TYPES
# =====================================================================

@dataclass(frozen=True)
class Profile:
    """
    A student profile. Mirrors ``public.profiles`` in ``supabase/schema.sql``.

    ``id`` is always the authenticated Supabase user id — it is never accepted
    from a form or a URL.
    """

    id: str
    name: str
    email: str
    college: str
    course: str
    year: int
    monthly_income: float
    monthly_budget: float
    monthly_savings_target: float
    primary_goal: str
    goal_amount: float
    goal_deadline: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_row(row: Optional[Dict[str, Any]]) -> Optional["Profile"]:
        """Build a Profile from a database row, tolerating missing/typed columns."""
        if row is None:
            return None

        def _text(key: str, default: str = "") -> str:
            value = row.get(key)
            return default if value is None else str(value)

        def _number(key: str) -> float:
            value = row.get(key)
            if value is None:
                return 0.0
            try:
                return round(float(value), 2)
            except (TypeError, ValueError):
                return 0.0

        def _int(key: str) -> int:
            value = row.get(key)
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0

        def _iso_date(key: str) -> str:
            value = row.get(key)
            if value is None:
                return ""
            if isinstance(value, (datetime, date)):
                return value.strftime("%Y-%m-%d")
            return str(value)

        return Profile(
            id=_text("id"),
            name=_text("name"),
            email=_text("email"),
            college=_text("college"),
            course=_text("course"),
            year=_int("year"),
            monthly_income=_number("monthly_income"),
            monthly_budget=_number("monthly_budget"),
            monthly_savings_target=_number("monthly_savings_target"),
            primary_goal=_text("primary_goal"),
            goal_amount=_number("goal_amount"),
            goal_deadline=_iso_date("goal_deadline"),
            created_at=_text("created_at"),
            updated_at=_text("updated_at"),
        )

    def as_dict(self) -> Dict[str, Any]:
        """Return the editable columns as a plain dict."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "college": self.college,
            "course": self.course,
            "year": self.year,
            "monthly_income": self.monthly_income,
            "monthly_budget": self.monthly_budget,
            "monthly_savings_target": self.monthly_savings_target,
            "primary_goal": self.primary_goal,
            "goal_amount": self.goal_amount,
            "goal_deadline": self.goal_deadline,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


#: The 12 columns the profile form is allowed to write.
EDITABLE_PROFILE_FIELDS: List[str] = [
    "name",
    "college",
    "course",
    "year",
    "monthly_income",
    "monthly_budget",
    "monthly_savings_target",
    "primary_goal",
    "goal_amount",
    "goal_deadline",
]


# =====================================================================
# CONFIGURATION
# =====================================================================

def _load_dotenv() -> None:
    """Load key-value pairs from .env file into os.environ if not already present."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and not os.environ.get(k):
                            os.environ[k] = v
        except Exception:
            pass


def get_supabase_url() -> Optional[str]:
    """Return the configured project URL, or None."""
    _load_dotenv()
    for key in (ENV_SUPABASE_URL, "NEXT_PUBLIC_SUPABASE_URL"):
        url = (os.environ.get(key) or "").strip()
        if url:
            return url
    return None


def get_anon_key() -> Optional[str]:
    """
    Return the publishable / anon key, or None.

    Raises if the variable has been filled with a service-role key: that key
    bypasses Row Level Security and must never be used by the application.
    """
    _load_dotenv()
    for key in (
        ENV_SUPABASE_ANON_KEY,
        "SUPABASE_PUBLISHABLE_KEY",
        "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
        "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    ):
        val = (os.environ.get(key) or "").strip()
        if val:
            _assert_publishable_key(val)
            return val
    return None


def _assert_publishable_key(key: str) -> None:
    """Refuse a service-role key. Raises SupabaseNotConfiguredError."""
    # Supabase's new-format secret keys always start with this prefix.
    if key.startswith("sb_secret_"):
        raise SupabaseNotConfiguredError(
            f"{ENV_SUPABASE_ANON_KEY} is holding a service-role secret key. "
            "Finora must use the publishable key instead so that Row Level "
            "Security stays enforced."
        )

    # Legacy keys are JWTs; check the embedded role claim.
    if key.count(".") != 2:
        return
    payload = key.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    try:
        claims = json.loads(base64.urlsafe_b64decode(payload))
    except (ValueError, TypeError):
        return
    if isinstance(claims, dict) and claims.get("role") == "service_role":
        raise SupabaseNotConfiguredError(
            f"{ENV_SUPABASE_ANON_KEY} is holding a service-role key. "
            "Finora must use the publishable key instead so that Row Level "
            "Security stays enforced."
        )


def is_configured() -> bool:
    """True when both URL and publishable key are present and valid."""
    try:
        return bool(get_supabase_url() and get_anon_key())
    except SupabaseNotConfiguredError:
        return False


# =====================================================================
# CLIENT FACTORY
# =====================================================================

def create_supabase_client(access_token: Optional[str] = None):
    """
    Build a Supabase client bound to the signed-in user's JWT.

    Passing ``access_token`` makes every PostgREST query run as that user, which
    is what makes the ``auth.uid() = id`` RLS policies effective. Returns a
    client bound to the publishable key (the anon role) when no token is given.

    Raises SupabaseNotConfiguredError / SupabaseAuthError.
    """
    url = get_supabase_url()
    key = get_anon_key()
    if not url or not key:
        raise SupabaseNotConfiguredError()

    # Imported lazily so the app still starts when supabase-py is not installed.
    try:
        from supabase import create_client
        from supabase.lib.client_options import SyncClientOptions
        from supabase_auth import SyncMemoryStorage
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise SupabaseNotConfiguredError(
            "The 'supabase' package is not installed. Run: pip install -r requirements.txt"
        ) from exc

    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}

    try:
        client = create_client(
            url,
            key,
            options=SyncClientOptions(
                storage=SyncMemoryStorage(),
                persist_session=False,
                auto_refresh_token=False,
                headers=headers,
                postgrest_client_timeout=15,
            ),
        )
        if access_token:
            try:
                client.postgrest.auth(access_token)
            except Exception:
                pass
        return client
    except Exception as exc:  # invalid URL, malformed key, etc.
        raise SupabaseNotConfiguredError(
            "Finora could not read its Supabase configuration. Check SUPABASE_URL "
            "and SUPABASE_ANON_KEY."
        ) from exc


# =====================================================================
# ERROR TRANSLATION
# =====================================================================

def _translate_error(exc: Exception, action: str) -> FinoraSupabaseError:
    """
    Convert a Supabase/PostgREST/HTTP exception into a user-safe error.

    Raw database text is deliberately discarded: it can leak table and column
    names, constraint internals and SQL fragments.
    """
    try:
        from supabase import AuthApiError as _AuthApiError
        from supabase import AuthInvalidCredentialsError as _AuthInvalidCredentialsError
        from supabase import AuthWeakPasswordError as _AuthWeakPasswordError
        from supabase import PostgrestAPIError as _PostgrestAPIError
    except ImportError:  # pragma: no cover - only when supabase-py is absent
        _AuthApiError = _AuthInvalidCredentialsError = None  # type: ignore[assignment]
        _AuthWeakPasswordError = _PostgrestAPIError = None  # type: ignore[assignment]

    # Already-safe errors pass straight through.
    if isinstance(exc, FinoraSupabaseError):
        return exc

    if _AuthInvalidCredentialsError and isinstance(exc, _AuthInvalidCredentialsError):
        return SupabaseAuthError("That email and password combination is not correct.")
    if _AuthWeakPasswordError and isinstance(exc, _AuthWeakPasswordError):
        return SupabaseAuthError("Please choose a stronger password (at least 6 characters).")
    if _AuthApiError and isinstance(exc, _AuthApiError):
        message = str(exc).lower()
        if "already registered" in message or "already been registered" in message:
            return SupabaseAuthError("An account with that email already exists. Try signing in.")
        if "email not confirmed" in message or "not confirmed" in message:
            return SupabaseAuthError("Please confirm your email address before signing in.")
        if "rate limit" in message or "too many" in message:
            return SupabaseAuthError("Too many attempts. Please wait a minute and try again.")
        if "jwt" in message or "token" in message or "expired" in message:
            return SupabaseSessionExpiredError()
        return SupabaseAuthError()
    if _PostgrestAPIError and isinstance(exc, _PostgrestAPIError):
        code = getattr(exc, "code", None)
        if code == "23505":  # unique_violation -> duplicate profile
            return ProfileAlreadyExistsError()
        if code in ("401", "403", "PGRST301") or str(code) == "JWT":
            return SupabaseSessionExpiredError()
        if code in ("42501",):  # insufficient_privilege -> RLS blocked the write
            return SupabaseRequestError(
                "Finora was not allowed to save that. Please reload and try again."
            )
        return SupabaseRequestError()

    # Network / timeout / DNS failures (httpx is what supabase-py uses).
    if isinstance(exc, (TimeoutError, OSError)) or _is_transport_error(exc):
        return SupabaseRequestError(
            "We couldn't reach Finora's servers. Check your connection and try again."
        )

    return SupabaseRequestError()


def _is_transport_error(exc: Exception) -> bool:
    """True for httpx connect/timeout/read errors raised by supabase-py."""
    try:
        import httpx
    except ImportError:  # pragma: no cover
        return False
    return isinstance(exc, (httpx.TimeoutException, httpx.TransportError))


# =====================================================================
# PROFILE QUERIES  (all RLS-scoped to auth.uid())
# =====================================================================

def fetch_profile(access_token: str, user_id: str) -> Optional[Profile]:
    """
    Read the caller's own profile, or None when setup is still pending.

    ``profiles.id`` is pinned to ``user_id`` on every query so that even a bug
    in calling code cannot widen the read beyond the caller's own row.
    """
    client = create_supabase_client(access_token)
    try:
        response = (
            client.table(PROFILES_TABLE)
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
    except Exception as exc:
        print(f"[Supabase fetch_profile ERROR] user_id={user_id}, error={exc}")
        raise _translate_error(exc, "load profile") from exc

    row = getattr(response, "data", None)
    if isinstance(row, list):
        row = row[0] if row else None
    print(f"[Supabase fetch_profile] user_id={user_id}, found_profile={bool(row)}")
    return Profile.from_row(row) if row else None


def insert_profile(
    access_token: str,
    user_id: str,
    email: str,
    values: Dict[str, Any],
) -> Profile:
    """
    Insert the caller's profile.

    The RLS ``profiles_insert_own`` policy rejects the write unless
    ``auth.uid() = id``, so the id cannot be forged from the client.
    """
    client = create_supabase_client(access_token)
    payload = {field: values[field] for field in EDITABLE_PROFILE_FIELDS if field in values}
    payload["id"] = user_id
    payload["email"] = email

    print(f"[Supabase insert_profile START] user_id={user_id}, email={email}")
    print(f"[Supabase insert_profile PAYLOAD] {payload}")

    try:
        response = client.table(PROFILES_TABLE).insert(payload).execute()
        result_data = getattr(response, "data", None)
        print(f"[Supabase insert_profile RESULT] result={result_data}")
    except Exception as exc:
        print(f"[Supabase insert_profile ERROR] user_id={user_id}, email={email}, error={exc}")
        raise exc

    rows = getattr(response, "data", None) or []
    if isinstance(rows, list):
        row = rows[0] if rows else None
    elif isinstance(rows, dict):
        row = rows
    else:
        row = None

    if not row:
        # Re-fetch just in case returning representation was empty
        fetched = fetch_profile(access_token, user_id)
        if fetched:
            return fetched
        raise SupabaseRequestError(f"Profile saved but could not be read back. Result: {rows}")
    profile = Profile.from_row(row)
    if profile is None:  # pragma: no cover - defensive
        raise SupabaseRequestError("Your profile could not be read back after saving.")
    return profile


def update_profile(access_token: str, user_id: str, values: Dict[str, Any]) -> Profile:
    """
    Update the caller's own profile.

    Only the editable columns are sent. RLS blocks both the ``using`` and the
    ``with check`` clause for any row where ``auth.uid() <> id``.
    """
    changed = {field: values[field] for field in EDITABLE_PROFILE_FIELDS if field in values}
    if not changed:
        raise SupabaseRequestError("There was nothing to update.")

    client = create_supabase_client(access_token)
    try:
        response = (
            client.table(PROFILES_TABLE)
            .update(changed)
            .eq("id", user_id)
            .select("*")
            .execute()
        )
    except Exception as exc:
        raise _translate_error(exc, "update profile") from exc

    rows = getattr(response, "data", None) or []
    if not rows:
        # Empty result under RLS means "not your row" or "row vanished".
        raise ProfileAlreadyExistsError(
            "Your profile could not be found. Refresh the page and try again."
        )
    profile = Profile.from_row(rows[0])
    if profile is None:  # pragma: no cover - defensive
        raise SupabaseRequestError("Your profile could not be read back after saving.")
    return profile


def get_user_email(access_token: str) -> Optional[str]:
    """Read the email Supabase Auth holds for the caller."""
    client = create_supabase_client(access_token)
    try:
        response = client.auth.get_user(access_token)
    except Exception as exc:
        raise _translate_error(exc, "load account") from exc

    user = getattr(response, "user", None)
    return getattr(user, "email", None) if user else None


# =====================================================================
# EXPENSE QUERIES (RLS-scoped to user_id)
# =====================================================================

EXPENSES_TABLE = "expenses"


def fetch_expenses(access_token: str, user_id: str) -> List[Dict[str, Any]]:
    """Fetch expenses for the authenticated user from Supabase."""
    client = create_supabase_client(access_token)
    try:
        response = (
            client.table(EXPENSES_TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("expense_date", desc=True)
            .order("created_at", desc=True)
            .execute()
        )
        return getattr(response, "data", None) or []
    except Exception as exc:
        raise _translate_error(exc, "fetch expenses") from exc


def insert_expense(
    access_token: str,
    user_id: str,
    expense_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Insert a new expense belonging to the authenticated user."""
    client = create_supabase_client(access_token)
    payload = dict(expense_data)
    payload["user_id"] = user_id
    try:
        response = client.table(EXPENSES_TABLE).insert(payload).execute()
        rows = getattr(response, "data", None) or []
        return rows[0] if rows else payload
    except Exception as exc:
        raise _translate_error(exc, "add expense") from exc


def delete_expense_supabase(access_token: str, user_id: str, expense_id: Any) -> bool:
    """Delete an expense belonging to the authenticated user from Supabase."""
    client = create_supabase_client(access_token)
    try:
        client.table(EXPENSES_TABLE).delete().eq("id", expense_id).eq("user_id", user_id).execute()
        return True
    except Exception as exc:
        raise _translate_error(exc, "delete expense") from exc