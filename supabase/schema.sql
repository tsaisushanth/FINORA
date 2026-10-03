-- ============================================================================
-- Finora — Student Profile schema (Supabase / PostgreSQL)
-- ----------------------------------------------------------------------------
-- Apply this in the Supabase SQL Editor (Dashboard -> SQL Editor -> New query),
-- or via `supabase db push`. It is idempotent: safe to run more than once.
--
-- Design rules (do not change without updating profiles.py):
--   1. profiles.id IS auth.users.id. There is no separate auth identity.
--   2. Email is owned by auth.users and copied in by trigger — the app never
--      accepts an email from the profile form.
--   3. Row Level Security makes every row private to its owner. The browser /
--      Streamlit client can only ever touch the row where auth.uid() = id.
--   4. No DELETE policy is created on purpose: a profile is removed by deleting
--      the auth.users row, which cascades.
-- ============================================================================

create extension if not exists "pgcrypto";


-- ---------------------------------------------------------------------------
-- Table
-- ---------------------------------------------------------------------------
create table if not exists public.profiles (
    id                    uuid primary key references auth.users (id) on delete cascade,

    -- Student details
    name                  text        not null check (char_length(btrim(name)) > 0
                                            and char_length(name) <= 80),
    email                 text        not null,
    college               text        not null check (char_length(btrim(college)) > 0
                                            and char_length(college) <= 120),
    course                text        not null check (char_length(btrim(course)) > 0
                                            and char_length(course) <= 120),
    year                  integer     not null check (year between 1 and 10),

    -- Monthly money plan. All amounts are non-negative rupees.
    monthly_income        numeric(12, 2) not null check (monthly_income >= 0),
    monthly_budget        numeric(12, 2) not null check (monthly_budget > 0),
    monthly_savings_target numeric(12, 2) not null check (monthly_savings_target >= 0),

    -- Primary savings goal
    primary_goal          text        not null check (char_length(btrim(primary_goal)) > 0
                                            and char_length(primary_goal) <= 120),
    goal_amount           numeric(12, 2) not null check (goal_amount > 0),
    goal_deadline         date        not null,

    created_at            timestamptz not null default now(),
    updated_at            timestamptz not null default now(),

    -- A student cannot plan to save more than they earn.
    constraint profiles_monthly_plan_balanced
        check (monthly_income = 0 or monthly_budget + monthly_savings_target <= monthly_income)
);

comment on table public.profiles is
    'One student profile per authenticated Finora user. id mirrors auth.users.id; RLS restricts access to the owner.';


-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.profiles force row level security;

-- Read only your own profile.
drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own"
    on public.profiles
    for select
    using (auth.uid() = id);

-- Create only your own profile (id must equal your auth user id).
drop policy if exists "profiles_insert_own" on public.profiles;
create policy "profiles_insert_own"
    on public.profiles
    for insert
    with check (auth.uid() = id);

-- Update only your own profile, and you may not re-point it at another id.
drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own"
    on public.profiles
    for update
    using (auth.uid() = id)
    with check (auth.uid() = id);


-- ---------------------------------------------------------------------------
-- Triggers
-- ---------------------------------------------------------------------------

-- Keep profiles.updated_at fresh on every write.
create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists profiles_touch_updated_at on public.profiles;
create trigger profiles_touch_updated_at
    before update on public.profiles
    for each row
    execute function public.touch_updated_at();


-- Keep profiles.email aligned with the authoritative auth.users email.
-- Profiles are deliberately NOT auto-created here: creation stays behind the
-- "profiles_insert_own" policy so the app performs an explicit, auditable
-- profile-setup step and "does the user have a profile?" stays answerable.
create or replace function public.sync_profile_email()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    update public.profiles
       set email = new.email
     where id = new.id;
    return new;
end;
$$;

drop trigger if exists auth_users_sync_profile_email on auth.users;
create trigger auth_users_sync_profile_email
    after update of email on auth.users
    for each row
    execute function public.sync_profile_email();


-- ---------------------------------------------------------------------------
-- Verification queries (run after applying, as the signed-in user)
-- ---------------------------------------------------------------------------
-- select * from public.profiles;                 -- expect at most your own row
-- set role anon;                                 -- then the same query must fail