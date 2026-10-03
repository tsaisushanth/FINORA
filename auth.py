"""
Authentication for Finora, backed by Supabase Auth.

Responsibilities
----------------
* Sign up / sign in / sign out against Supabase Auth.
* Hold the session in ``st.session_state`` and expose the access token.
* Resolve the authenticated Supabase user to the local ``users`` row that the
  rest of Finora already uses, so expenses, wallet and goals keep working
  unchanged.

Ownership rule
--------------
The profile id is always the Supabase user id taken from the *verified session*.
It is never read from a form, a query string or any other client input.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import streamlit as st

import supabase_client as sc
from database import (
    get_local_user_id_for_auth_account,
    link_auth_account_to_local_user,
)

SESSION_USER_KEY = "finora_auth_user"
SESSION_TOKEN_KEY = "finora_access_token"
SESSION_REFRESH_KEY = "finora_refresh_token"


# =====================================================================
# TYPES
# =====================================================================

@dataclass(frozen=True)
class AuthSession:
    """A verified Supabase session."""

    user_id: str
    email: str
    access_token: str
    refresh_token: str
    local_user_id: int

    @property
    def is_expired(self) -> bool:
        return not self.access_token


# =====================================================================
# SESSION PLUMBING
# =====================================================================

def get_authenticated_user_id() -> Optional[str]:
    """Return the Supabase user id for the current session, or None."""
    user = st.session_state.get(SESSION_USER_KEY)
    if isinstance(user, dict):
        return user.get("id")
    return None


def get_access_token() -> Optional[str]:
    """Return the caller's access token, or None when signed out."""
    return st.session_state.get(SESSION_TOKEN_KEY) or None


def is_authenticated() -> bool:
    return bool(get_authenticated_user_id() and get_access_token())


def clear_session() -> None:
    """Drop every trace of the session from Streamlit state."""
    for key in (SESSION_USER_KEY, SESSION_TOKEN_KEY, SESSION_REFRESH_KEY):
        st.session_state.pop(key, None)


def _store_session(user: Any, session: Any) -> None:
    user_id = getattr(user, "id", None)
    access_token = getattr(session, "access_token", None)
    refresh_token = getattr(session, "refresh_token", None)
    if not user_id or not access_token:
        raise sc.SupabaseAuthError(
            "Sign-in did not return a usable session. Please try again."
        )
    st.session_state[SESSION_USER_KEY] = {
        "id": user_id,
        "email": getattr(user, "email", "") or "",
    }
    st.session_state[SESSION_TOKEN_KEY] = access_token
    st.session_state[SESSION_REFRESH_KEY] = refresh_token or ""


# =====================================================================
# EMAIL / PASSWORD VALIDATION
# =====================================================================

MIN_PASSWORD_LENGTH = 6


def validate_credentials(email: str, password: str, confirm_password: Optional[str] = None) -> Dict[str, str]:
    """
    Validate sign-in / sign-up input before any network call.

    Returns a ``{field: message}`` map; an empty map means the input is valid.
    """
    errors: Dict[str, str] = {}
    cleaned_email = (email or "").strip()

    if not cleaned_email:
        errors["email"] = "Please enter your email address."
    elif "@" not in cleaned_email or "." not in cleaned_email.split("@")[-1]:
        errors["email"] = "That doesn't look like a valid email address."

    if not password:
        errors["password"] = "Please enter your password."
    elif len(password) < MIN_PASSWORD_LENGTH:
        errors["password"] = f"Password must be at least {MIN_PASSWORD_LENGTH} characters."

    if confirm_password is not None and password != confirm_password:
        errors["confirm_password"] = "Both passwords need to match."

    return errors


# =====================================================================
# SIGN UP / SIGN IN / SIGN OUT
# =====================================================================

def sign_up(email: str, password: str, confirm_password: str) -> AuthSession:
    """
    Create a Supabase account and sign in.

    Raises ``sc.SupabaseAuthError`` with a user-safe message on failure.
    """
    errors = validate_credentials(email, password, confirm_password)
    if errors:
        raise sc.SupabaseAuthError(next(iter(errors.values())))

    client = sc.create_supabase_client()
    try:
        response = client.auth.sign_up(
            {"email": (email or "").strip(), "password": password}
        )
    except Exception as exc:
        raise sc._translate_error(exc, "sign up") from exc

    user = getattr(response, "user", None)
    session = getattr(response, "session", None)
    if user is None:
        raise sc.SupabaseAuthError("We couldn't create your account. Please try again.")
    if session is None:
        # Common when "Confirm email" is enabled in Supabase.
        raise sc.SupabaseAuthError(
            "Almost there — check your inbox and confirm your email, then sign in."
        )

    _store_session(user, session)
    return get_current_session()


def sign_in(email: str, password: str) -> AuthSession:
    """Sign in with email + password."""
    errors = validate_credentials(email, password)
    if errors:
        raise sc.SupabaseAuthError(next(iter(errors.values())))

    client = sc.create_supabase_client()
    try:
        response = client.auth.sign_in_with_password(
            {"email": (email or "").strip(), "password": password}
        )
    except Exception as exc:
        raise sc._translate_error(exc, "sign in") from exc

    user = getattr(response, "user", None)
    session = getattr(response, "session", None)
    if user is None or session is None:
        raise sc.SupabaseAuthError("We couldn't sign you in. Please try again.")

    print(f"[Supabase Auth sign_in] SUCCESS -> user.id: {user.id}, email: {user.email}")
    _store_session(user, session)
    return get_current_session()


def sign_out() -> None:
    """Invalidate the Supabase session and clear local state."""
    refresh_token = st.session_state.get(SESSION_REFRESH_KEY)
    if refresh_token:
        try:
            client = sc.create_supabase_client()
            client.auth.sign_out()
        except Exception:
            # Local sign-out must succeed even if the network call does not.
            pass
    clear_session()


# =====================================================================
# CURRENT SESSION
# =====================================================================

def get_current_session(verify: bool = True) -> Optional[AuthSession]:
    """
    Return the active session, re-verifying it against Supabase by default.

    An expired or revoked token clears the local session and returns None so the
    UI can fall back to the sign-in screen instead of erroring.
    """
    user = st.session_state.get(SESSION_USER_KEY)
    access_token = st.session_state.get(SESSION_TOKEN_KEY)
    if not isinstance(user, dict) or not user.get("id") or not access_token:
        return None

    if verify:
        try:
            client = sc.create_supabase_client(access_token)
            response = client.auth.get_user(access_token)
        except Exception:
            # Network trouble should not sign the user out; trust the token and
            # let individual requests surface their own errors.
            response = None

        verified = getattr(response, "user", None) if response is not None else None
        if response is not None and verified is None:
            clear_session()
            return None
        if verified is not None:
            user_id = getattr(verified, "id", None)
            if not user_id or user_id != user.get("id"):
                # Token no longer matches the stored identity.
                clear_session()
                return None
            user = {
                "id": user_id,
                "email": getattr(verified, "email", "") or user.get("email", ""),
            }
            st.session_state[SESSION_USER_KEY] = user

    local_user_id = get_local_user_id_for_auth_account(user["id"])

    return AuthSession(
        user_id=user["id"],
        email=user.get("email", "") or "",
        access_token=access_token,
        refresh_token=st.session_state.get(SESSION_REFRESH_KEY) or "",
        local_user_id=local_user_id,
    )


def require_session() -> Optional[AuthSession]:
    """Return the active session, or ``None`` after clearing a dead one."""
    session = get_current_session()
    if session is None and get_authenticated_user_id():
        clear_session()
    return session


def ensure_local_identity(session: AuthSession) -> int:
    """
    Guarantee a local ``users`` row exists for this Supabase account.

    Expenses, the wallet and the Bucket List are all scoped to ``users.id``, so
    a brand-new account needs a matching local identity before it can record
    anything. The link is persisted, so returning users keep their data.
    """
    return link_auth_account_to_local_user(session.user_id, session.email)