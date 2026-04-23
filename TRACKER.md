# Bij-Ganit — Sprint Tracker

This file is the **running log of what has been shipped** on the FastAPI +
React migration.  The authoritative plan lives in `MIGRATION_ROADMAP.md`
(on the `devin/1776936387-migration-roadmap` branch) and the intern sprint
task list is the GitHub issue/message thread.

**DO NOT** modify `MIGRATION_ROADMAP.md` from this branch — treat it as read
only reference. Update this tracker instead.

## How to read this file

For each sprint I list:

* **What shipped** — a short bullet list of the files/endpoints that landed.
* **Where to look** — the concrete files a new developer should open first.
* **How to try it** — 1-2 commands to verify the work locally.
* **Notes for the next intern** — assumptions, intentional TODOs, gotchas.

New developers: start at Sprint 0 and walk down.  Everything in a later
sprint builds on the scaffolding of an earlier one.

---

## Sprint 0 — Project Setup & Scaffolding

### 0.1 FastAPI backend scaffold — DONE

What shipped:

* `backend/app/main.py` — FastAPI app, CORS middleware, mounts the v1 router
  under `/api/v1`, and exposes `GET /api/ping` returning `{"success": "ok"}`
  (matches the task spec; the Laravel reference returned
  `crater-self-hosted`, we standardised on `ok`).
* `backend/requirements.txt` — pinned runtime deps.
* `backend/Dockerfile` — production-ish image used by docker-compose.
* `backend/tests/test_ping.py` — smoke test (`pytest -q` → 4 passing).

Where to look: `backend/app/main.py`, `backend/app/api/v1/__init__.py`.

How to try it:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# in another shell:
curl http://localhost:8000/api/ping      # -> {"success":"ok"}
```

### 0.2 React frontend scaffold — DONE

What shipped:

* `frontend/` — Vite + React 19 + TypeScript.
* Tailwind CSS 3 configured (`tailwind.config.js`, `postcss.config.js`,
  `src/index.css`).
* React Router v6 for routing, Axios for HTTP, Zustand for client state.
* `vite.config.ts` proxies `/api` to `http://localhost:8000` so the frontend
  can use relative URLs everywhere.

Where to look: `frontend/src/App.tsx`, `frontend/src/api/client.ts`,
`frontend/src/stores/`.

How to try it:

```bash
cd frontend
npm install
npm run dev          # -> http://localhost:5173
```

### 0.3 Docker Compose — DONE

What shipped:

* `docker-compose.yml` at the repo root with four services:
  * `db` — Postgres 15 (user/pass/db all `bijganit`, port 5432)
  * `redis` — Redis 7 (port 6379)
  * `backend` — runs `alembic upgrade head` then `uvicorn --reload`
  * `frontend` — node:22-alpine running `npm install && npm run dev`

How to try it:

```bash
docker-compose up --build
# wait for the four services; then
curl http://localhost:8000/api/ping
# and open http://localhost:5173
```

### 0.4 SQLAlchemy 2.0 + Alembic — DONE

What shipped:

* `backend/app/database.py` — async engine + `AsyncSessionLocal` +
  `get_db()` FastAPI dependency + shared `Base`.
* `backend/alembic.ini`, `backend/alembic/env.py`,
  `backend/alembic/script.py.mako` — Alembic wired to use the sync URL from
  `app.config` (alembic doesn't play well with async engines).
* `backend/alembic/versions/0001_initial_users_companies.py` — the initial
  migration (see Sprint 1.1-1.3 below).

How to try it:

```bash
cd backend
source .venv/bin/activate
# once a postgres is reachable at DATABASE_URL_SYNC:
alembic upgrade head
```

### 0.5 Pydantic config — DONE

What shipped:

* `backend/app/config.py` with a `Settings` class using `pydantic-settings`.
  Reads `.env` in development.  Exposes both an async DB URL (for the app)
  and a sync DB URL (for Alembic).
* `backend/.env.example` — copy to `.env` and fill in.

---

## Sprint 1 — Auth + Users + Companies

### 1.1 – 1.3 Migrations (users / companies / user_company) — DONE

Landed together in `backend/alembic/versions/0001_initial_users_companies.py`
so a single `alembic upgrade head` stands up all three tables with their FKs
resolved.

Schema highlights (slightly trimmed vs the Laravel reference, as per the
task spec):

* `users(id, name, email UNIQUE, phone, password, role, creator_id→users,
  company_id→companies, created_at, updated_at)`
* `companies(id, name, slug UNIQUE, unique_hash, owner_id→users,
  created_at, updated_at)` — `slug` + `owner_id` are additions beyond the
  2014-era Crater migration.
* `user_company(id, user_id→users, company_id→companies, created_at,
  updated_at)` with a uniqueness constraint on `(user_id, company_id)`.

### 1.4 SQLAlchemy models — DONE

* `backend/app/models/user.py` — `User` with `companies` (many-to-many),
  `owned_companies`, and `creator` relationships.
* `backend/app/models/company.py` — `Company` with `owner`, `users`,
  and the `UserCompany` pivot model.

### 1.5 JWT auth utilities — DONE

* `backend/app/core/security.py` — `hash_password`, `verify_password`
  (passlib + bcrypt), `create_access_token`, `verify_token` (python-jose).
* `backend/app/core/deps.py` — `get_current_user` reads the
  `Authorization: Bearer …` header, decodes the JWT and loads the user.

Unit tests: `backend/tests/test_security.py` (`pytest -q` → all green).

### 1.6 Auth endpoints — DONE

* `POST /api/v1/auth/login`   — `{email, password}` → `{type:"Bearer", token}`
* `POST /api/v1/auth/logout`  — stateless; requires a valid token, returns
  `{success:true}`.  JWTs are stateless so the client just drops the token.
* `GET  /api/v1/auth/check`   — verifies the current token and returns
  `{authenticated:true, user_id}`.

Where to look: `backend/app/api/v1/auth.py`.

### 1.7 Company CRUD endpoints — DONE

* `POST /api/v1/companies` — creates a company, auto-slugifies the name if
  the caller doesn't supply a slug, attaches the caller as the owner AND
  inserts a `user_company` membership row, then calls
  `setup_default_data()` (Sprint 1.9).
* `GET  /api/v1/companies` — lists the calling user's companies via the
  `user_company` pivot.
* `POST /api/v1/companies/delete` — bulk delete by ids; only the owner may
  delete a given company.

Where to look: `backend/app/api/v1/companies.py`.

### 1.8 Company multi-tenancy dependency — DONE

* `backend/app/core/deps.py::get_current_company` — reads the `company`
  request header, validates the user belongs to that company (either by
  ownership or via `user_company`), and returns the `Company` object.
* Tenant-scoped endpoints in later sprints will
  `Depends(get_current_company)` and filter their queries on `company.id` —
  the FastAPI equivalent of Laravel's `scopeWhereCompany`.

### 1.9 Company default data — STUB (intentional)

`backend/app/services/company_defaults.py` defines the three default sets
(4 payment methods, 11 units, ~20 settings) but leaves `setup_default_data`
as a **no-op** because the target tables (`payment_methods`, `units`,
`company_settings`) don't exist yet — they belong to Sprint 4 / 12.  The
call site (`POST /companies`) already calls into it so the next intern only
has to fill in the body once those models land.

Notes for the next intern:

* Copy the remaining ~30 settings keys out of
  `crater-master/app/Models/Company.php` lines 194-253 (address formats,
  email bodies, currency id, etc.) when you flesh this out.

### 1.10 Login page — DONE

`frontend/src/pages/LoginPage.tsx`: email + password form, posts to
`/api/v1/auth/login`, stores the JWT in the Zustand auth store (which
persists to localStorage via zustand/persist), then redirects to the
originally requested route (or `/dashboard`).

### 1.11 App layout + sidebar — DONE

`frontend/src/components/AppLayout.tsx` + `RequireAuth.tsx`:

* Sidebar with the 9 nav links from the spec (Dashboard, Customers, Items,
  Invoices, Estimates, Expenses, Payments, Recurring Invoices, Settings).
* Header with a company switcher `<select>` that populates from
  `GET /api/v1/companies` and writes the active id into the Zustand
  `companyStore`.
* The shared axios client in `frontend/src/api/client.ts` then injects the
  active company id as the `company` header on every subsequent request, so
  the backend's `get_current_company` dependency just works.
* Logout button calls `POST /api/v1/auth/logout` (best-effort) and clears
  the local token.

### 1.12 Users CRUD endpoints — DONE

* `GET  /api/v1/users` — list all users (auth required).
* `POST /api/v1/users` — create; password is bcrypt hashed; 409 on duplicate
  email.
* `PUT  /api/v1/users/{id}` — partial update; if `password` is provided it
  is re-hashed.
* `POST /api/v1/users/delete` — bulk delete; callers can't delete
  themselves.

Where to look: `backend/app/api/v1/users.py`.

---

## Sprint 2 — Customers + Items + Tax Types (Master Data)

Shipped in `backend/alembic/versions/0002_sprint2_master_data.py` +
`backend/app/{models,schemas,api/v1,seed_data}/...` +
`frontend/src/pages/{customers,items}/`. Everything is company-scoped via
the existing `Depends(get_current_company)` guard.

What shipped:

* **2.1 Lookup tables + seed data** — `currencies` (153 ISO 4217 rows) and
  `countries` (246 ISO 3166 rows) seeded inside the Alembic migration via
  `op.bulk_insert`. Source data lives in `app/seed_data/` so the same
  list powers both the migration and the `GET /api/v1/{currencies,countries}`
  endpoints.
* **2.2 / 2.3 `customers` + `addresses`** — `Customer` (name, email, phone,
  contact/company name, website, `enable_portal`, `password` nullable,
  currency/company/creator FKs). `Address` keys to `customer_id` (+
  `company_id`), with `type` enum `"billing"|"shipping"` and a
  `country_id` FK. Addresses cascade-delete with their customer.
* **2.4 Customer CRUD** — `GET/POST/PUT /api/v1/customers`,
  `POST /api/v1/customers/delete`, `GET /api/v1/customers/{id}`,
  `GET /api/v1/customers/{id}/stats`. List supports `search`
  (name/contact_name/company_name ILIKE), `from_date`/`to_date`,
  `order_by`/`order`. Create/update accept nested `billing` + `shipping`
  address payloads.
* **2.5 / 2.6 `items` + `units`** — `Item` has BigInt `price`,
  `tax_per_item`, `unit_id`/`currency_id`/`company_id`/`creator_id`. Per-item
  taxes live in the `taxes` table with `item_id` set. CRUD at
  `/api/v1/items` (+ `/delete` bulk) and `/api/v1/units` (inline CRUD). Item
  create/update replaces linked taxes atomically.
* **2.7 / 2.8 `tax_types` + `taxes`** — `TaxType` has `percent` (numeric
  5,2), `compound_tax`, `collective_tax`, `type`, `description`.
  `Tax` has polymorphic nullable FKs — `item_id` is a real FK today,
  `invoice_id`/`estimate_id` are plain nullable Integers until those tables
  land in later sprints. CRUD at `/api/v1/tax-types` (+ `/delete`).
* **2.9 / 2.10 React pages** — `CustomersListPage` + `CustomerFormPage`
  (billing/shipping address sections, currency dropdown),
  `ItemsListPage` + `ItemFormPage` (unit + currency dropdowns, tax type
  checkboxes, currency-aware price formatting). List pages support search
  + client-side pagination.
* **2.11 Lookup endpoints** — `GET /api/v1/countries`, `/currencies`,
  `/timezones`, `/date/formats`. Public (no auth) to mirror the reference
  behaviour. Data served from `app/seed_data/`.

Where to look:

* Migration: `backend/alembic/versions/0002_sprint2_master_data.py`
* Models: `backend/app/models/{currency,country,customer,address,unit,item,tax}.py`
* Routes: `backend/app/api/v1/{customers,items,units,tax_types,lookups}.py`
* Frontend: `frontend/src/pages/{customers,items}/` +
  `frontend/src/types/masterData.ts`

How to try it:

```bash
cd backend && source .venv/bin/activate
pytest -q                             # 12 passing (4 sprint 1 + 8 sprint 2)
alembic upgrade head                  # creates Sprint 2 tables + seeds
```

Notes for the next intern:

* Invoice/estimate FKs on `taxes` are intentionally *not* enforced at the
  DB level yet — add them in a follow-up migration once those tables land.
* Customer passwords are hashed with the existing `hash_password` helper;
  the portal login flow itself is Phase 11 work.
* `CustomerStats` currently returns `total_customers` only. The
  invoice/payment/due fields are exposed but return 0 until Sprint 4+.
* `/api/v1/currencies` returns synthetic ids (index + 1) so the frontend
  can key dropdowns — these match the auto-increment ids produced by
  `bulk_insert` in Postgres.

---

## Glossary / "Why did you do X?"

* **Why async SQLAlchemy but sync Alembic?** Alembic's tooling is
  battle-tested on the sync driver (`psycopg2`), the app itself benefits
  from the async driver (`asyncpg`).  We expose both URLs in settings so
  each gets what it wants.
* **Why JWT and not Laravel Sanctum / DB-backed tokens?** Stateless tokens
  keep the FastAPI backend deployable behind any load balancer without
  sticky sessions or a shared token table.  If we later need revocation we
  can add a small "token blacklist" table in Redis.
* **Why put the active company id in a header instead of the URL?** The
  reference Laravel app does the same thing (via a request header read in
  middleware).  Keeping it out of the URL means the same route can be
  bookmarked across tenants by the same user.
* **Why is `crater-master/` still in the repo?** It is the reference
  application.  Read-only.  Do not modify it and do not copy code verbatim
  — re-implement behaviour in the new stack.

## Running the full stack

```bash
# 1. Backend deps + tests
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q                       # 12 passing

# 2. Frontend deps + production build
cd ../frontend
npm install
npm run build                   # vite builds -> dist/

# 3. Everything together
cd ..
docker-compose up --build
```

Then visit `http://localhost:5173` (frontend) and
`http://localhost:8000/docs` (FastAPI Swagger).
