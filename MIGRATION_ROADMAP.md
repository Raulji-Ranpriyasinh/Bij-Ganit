# Migration Roadmap: Crater (Laravel + Vue) → FastAPI + React

This document is a **step-by-step roadmap for interns** to migrate the reference
application under `crater-master/` (a Laravel 8 + Vue 3 invoicing/estimate
application) to a new stack using **Python FastAPI** for the backend and
**React** for the frontend.

> **Licensing note:** The code in `crater-master/` is under its original
> license. Treat it strictly as **reference / inspiration**. Do **not** copy
> code verbatim. Re-implement features by reading the reference, understanding
> the behaviour, and writing fresh code in the new stack.

---

## Table of contents

1. [Overall goal](#1-overall-goal)
2. [Target architecture](#2-target-architecture)
3. [How to use this roadmap](#3-how-to-use-this-roadmap)
4. [Phase 0 — Project bootstrap](#phase-0--project-bootstrap)
5. [Phase 1 — Backend foundations (FastAPI)](#phase-1--backend-foundations-fastapi)
6. [Phase 2 — Frontend foundations (React)](#phase-2--frontend-foundations-react)
7. [Phase 3 — Auth & company setup](#phase-3--auth--company-setup)
8. [Phase 4 — Core domain: customers, items, taxes](#phase-4--core-domain-customers-items-taxes)
9. [Phase 5 — Estimates](#phase-5--estimates)
10. [Phase 6 — Invoices](#phase-6--invoices)
11. [Phase 7 — Payments](#phase-7--payments)
12. [Phase 8 — Expenses](#phase-8--expenses)
13. [Phase 9 — Recurring invoices & scheduled jobs](#phase-9--recurring-invoices--scheduled-jobs)
14. [Phase 10 — Reports & dashboard](#phase-10--reports--dashboard)
15. [Phase 11 — Customer portal](#phase-11--customer-portal)
16. [Phase 12 — Settings, custom fields, notes](#phase-12--settings-custom-fields-notes)
17. [Phase 13 — PDF, email, file storage](#phase-13--pdf-email-file-storage)
18. [Phase 14 — Hardening & release](#phase-14--hardening--release)
19. [Milestones & checkpoints](#milestones--checkpoints)
20. [Task dependency graph](#task-dependency-graph)
21. [Definition of Done (per task)](#definition-of-done-per-task)

---

## 1. Overall goal

Re-implement the reference invoicing application as two independently
deployable services:

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2,
  PostgreSQL, Redis, Celery (or ARQ), pytest.
- **Frontend:** React 18+, Vite, TypeScript, React Router, TanStack Query for
  server state, Zustand (or Redux Toolkit) for client state, a component
  library (MUI / Chakra / shadcn/ui — pick one and stay consistent), React
  Hook Form + Zod for forms, Vitest + React Testing Library.

The migrated application must preserve the **core business behaviour** of the
reference app (customers, items, estimates, invoices, payments, expenses,
recurring invoices, reports, customer portal, settings) while being idiomatic
for the new stack.

Scope **excluded** from v1 (can be revisited later): mobile apps, the modules
plugin system, blockchain/Web3 items, Laravel-specific tooling (artisan,
Tinker, Horizon, etc.).

## 2. Target architecture

```
repo/
├── backend/                 # FastAPI service
│   ├── app/
│   │   ├── api/             # Routers (v1/admin, v1/customer, v1/webhook)
│   │   ├── core/            # config, security, deps
│   │   ├── db/              # session, base, migrations (alembic/)
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── workers/         # Celery/ARQ tasks
│   │   └── main.py
│   ├── tests/
│   ├── pyproject.toml
│   └── alembic.ini
├── frontend/                # React + Vite app
│   ├── src/
│   │   ├── api/             # API client (axios/fetch) + TanStack Query hooks
│   │   ├── components/      # Reusable UI
│   │   ├── features/        # Feature folders (invoices, estimates, …)
│   │   ├── routes/          # Route definitions
│   │   ├── stores/          # Zustand stores
│   │   ├── lib/             # utils, i18n, auth helpers
│   │   └── main.tsx
│   ├── tests/
│   └── package.json
├── docker-compose.yml       # postgres, redis, backend, frontend (dev)
└── crater-master/           # Reference-only, do not modify
```

**Contract-first rule:** the backend is the source of truth. Every frontend
task must be preceded by a defined, documented (OpenAPI) endpoint on the
backend. Generate a typed client (e.g. via `openapi-typescript` or
`orval`) from the FastAPI OpenAPI schema so the frontend stays in sync.

## 3. How to use this roadmap

- Work **phase by phase**, top to bottom. A phase is ready to start only when
  all tasks in the previous phase have reached Definition of Done.
- Inside a phase, tasks are sequential **unless explicitly marked**
  "can run in parallel with".
- Each task is small enough for **one intern to finish in roughly half a day
  to two days**. If it feels bigger, break it down further in the issue
  tracker before starting.
- Every task must:
  1. Link to the reference file(s) under `crater-master/` it was inspired by.
  2. Ship with tests.
  3. Be merged behind a PR that passes CI and lint.
- Progress tracking: tick the boxes below as tasks merge to `main`.

---

## Phase 0 — Project bootstrap

**Goal:** a running, empty skeleton with CI, linting, and Docker Compose.

- [ ] **0.1** Create `backend/` skeleton with `pyproject.toml` (poetry or uv),
  FastAPI, Uvicorn, Ruff, mypy, pytest. Expose `GET /health` returning
  `{"status":"ok"}`.
- [ ] **0.2** Create `frontend/` skeleton with Vite + React + TypeScript,
  ESLint, Prettier, Vitest. Render a placeholder `App.tsx`.
- [ ] **0.3** Add `docker-compose.yml` with services: `postgres:15`,
  `redis:7`, `backend`, `frontend`. `make up` / `make down` convenience
  targets.
- [ ] **0.4** Add GitHub Actions CI: one workflow per service running lint +
  tests on PRs.
- [ ] **0.5** Commit a `CONTRIBUTING.md` describing branch naming, PR
  template, commit style, and how to run the stack locally.
- [ ] **0.6** Add an intern-friendly `README.md` at the repo root that links
  back to this roadmap.

**Checkpoint 0 ✅:** A new clone + `docker compose up` boots backend and
frontend, `/health` returns OK, and CI is green on an empty PR.

---

## Phase 1 — Backend foundations (FastAPI)

**Reference:** `crater-master/app/`, `crater-master/config/`,
`crater-master/database/migrations/`.

- [ ] **1.1** Configure settings via Pydantic Settings (`backend/app/core/config.py`).
  Support `.env` + env vars for DB URL, secret key, CORS origins, file
  storage, mail, etc.
- [ ] **1.2** Add SQLAlchemy 2.x async engine + session, `Base` declarative
  class, and a `get_db` dependency.
- [ ] **1.3** Wire Alembic with an initial empty migration. Document
  `alembic revision --autogenerate` workflow.
- [ ] **1.4** Add structured logging (e.g. `structlog`), a global exception
  handler, and a consistent error response schema
  (`{"detail": "...", "code": "..."}`).
- [ ] **1.5** Add CORS middleware gated by config; add request-id middleware.
- [ ] **1.6** Scaffold `app/api/v1/` with sub-routers: `admin/`, `customer/`,
  `webhook/` (empty for now). Mount under `/api/v1`.
- [ ] **1.7** Add a `pytest` fixture that boots the app with a throwaway
  Postgres schema (testcontainers or a disposable DB) and a factory-boy /
  polyfactory setup for fixtures.

**Checkpoint 1 ✅:** Backend boots, migrations run, tests run, OpenAPI
schema is visible at `/docs`.

---

## Phase 2 — Frontend foundations (React)

**Reference:** `crater-master/resources/scripts/`,
`crater-master/resources/scripts/admin/`,
`crater-master/resources/scripts/customer/`.

- [ ] **2.1** Pick and install a component library (recommended: MUI or
  shadcn/ui) and a styling solution. Document the choice.
- [ ] **2.2** Set up React Router with two shells — `AdminLayout` and
  `CustomerLayout` (mirrors `admin-router.js` / `customer-router.js` in
  the reference).
- [ ] **2.3** Add a typed API client in `src/api/client.ts` (axios or
  fetch wrapper) with interceptors for auth tokens and error handling.
- [ ] **2.4** Add TanStack Query provider and a `useApi` hook pattern.
- [ ] **2.5** Add Zustand store skeletons for cross-cutting state
  (`useAuthStore`, `useCompanyStore`, `useUiStore`).
- [ ] **2.6** Add i18n (`react-i18next`). Copy **keys only** (not
  translations) from `crater-master/resources/scripts/locales/en.json` to
  scope the namespace.
- [ ] **2.7** Set up the OpenAPI → TypeScript client generation script
  (`npm run gen:api`) and commit the generated types under
  `frontend/src/api/generated/`.

**Checkpoint 2 ✅:** Running the frontend shows placeholder Admin and
Customer shells, a login page skeleton, and types are generated from the
backend OpenAPI.

---

## Phase 3 — Auth & company setup

**Reference:** `app/Http/Controllers/V1/Admin/Auth/`,
`app/Http/Controllers/V1/Admin/Company/`,
`app/Http/Controllers/V1/Admin/Mobile/AuthController.php`,
`app/Models/User.php`, `app/Models/Company.php`, `app/Models/CompanySetting.php`.

> Dependencies: Phase 1 + Phase 2.

### Backend

- [ ] **3.1** Models + migrations for `User`, `Company`, `CompanyUser` (pivot),
  `Role`, `Permission` (a minimal RBAC — you do **not** need to port
  Bouncer's full feature set), `CompanySetting`.
- [ ] **3.2** Password hashing with `passlib[bcrypt]`. Seed an admin user.
- [ ] **3.3** `POST /api/v1/auth/login` → JWT access + refresh tokens.
  `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`.
- [ ] **3.4** `POST /api/v1/auth/password/forgot` and
  `POST /api/v1/auth/password/reset` (email token flow; email sending can
  stub to logs until Phase 13).
- [ ] **3.5** `GET /api/v1/me`, `PUT /api/v1/me` (profile), password change.
- [ ] **3.6** Companies CRUD + "current company" selection. Enforce
  multi-tenant scoping on every subsequent query via a FastAPI dependency.
- [ ] **3.7** Installation wizard endpoints (app name, admin creation,
  initial company) — mirrors `Controllers/V1/Admin/Installation/`.
- [ ] **3.8** Tests: registration, login, refresh, RBAC decorator,
  multi-tenant isolation.

### Frontend

- [ ] **3.9** Login page, forgot-password, reset-password pages.
- [ ] **3.10** Auth store: persist access token in memory + refresh token in
  httpOnly cookie (preferred) or secure storage. Handle 401 → refresh.
- [ ] **3.11** Installation wizard UI (only shown when backend reports
  `not_installed`).
- [ ] **3.12** Company switcher in the top bar.
- [ ] **3.13** Profile page.

**Checkpoint 3 ✅:** A fresh user can install the app, log in, switch
companies, and edit their profile. All protected endpoints require auth.

---

## Phase 4 — Core domain: customers, items, taxes

**Reference:** `app/Http/Controllers/V1/Admin/Customer/`,
`app/Http/Controllers/V1/Admin/Item/`,
`app/Http/Controllers/V1/Admin/CustomField/`,
`app/Models/Customer.php`, `app/Models/Item.php`, `app/Models/Tax.php`,
`app/Models/TaxType.php`, `app/Models/Unit.php`, `app/Models/Address.php`,
`app/Models/Currency.php`.

> Dependencies: Phase 3.

### Backend (can be split per resource, run in parallel once models land)

- [ ] **4.1** Migrations & models for `Currency`, `Country`, `Address`,
  `TaxType`, `Unit`. Seed currencies + countries from a fixtures file.
- [ ] **4.2** `Customer` model + CRUD endpoints + list filters (search,
  pagination, sort) + `CustomerStats`.
- [ ] **4.3** `Item` model + CRUD endpoints + list filters + units endpoint.
- [ ] **4.4** `TaxType` CRUD endpoints.
- [ ] **4.5** `CustomField` CRUD + attachment to Customer / Item / Invoice /
  Estimate / Expense / Payment.
- [ ] **4.6** Shared `SearchController`-style endpoint (`GET /api/v1/search`)
  returning grouped results (customers, invoices, estimates).
- [ ] **4.7** Tests for each resource incl. tenant isolation, custom field
  values, address serialisation.

### Frontend (one intern per feature is fine)

- [ ] **4.8** Customers list, create/edit, detail with tabs (stats,
  invoices, estimates, payments).
- [ ] **4.9** Items list, create/edit.
- [ ] **4.10** Tax types and units admin screens (under Settings).
- [ ] **4.11** Custom fields admin screen + a reusable
  `<CustomFieldsInput />` used across forms.
- [ ] **4.12** Global search dropdown in the top bar.

**Checkpoint 4 ✅:** Admin can manage customers, items, taxes, units, and
custom fields end-to-end.

---

## Phase 5 — Estimates

**Reference:** `app/Http/Controllers/V1/Admin/Estimate/`,
`app/Models/Estimate.php`, `app/Models/EstimateItem.php`,
`resources/scripts/admin/views/estimates/`,
`resources/scripts/admin/stores/estimate.js`.

> Dependencies: Phase 4.

### Backend

- [ ] **5.1** Models: `Estimate`, `EstimateItem`, status enum, number
  generator (`NextNumberController` pattern).
- [ ] **5.2** CRUD + list (with filters: customer, status, date range).
- [ ] **5.3** Status change endpoint (draft → sent → accepted / rejected).
- [ ] **5.4** Convert-to-invoice endpoint.
- [ ] **5.5** Send estimate endpoint + preview endpoint (email body +
  rendered preview).
- [ ] **5.6** Estimate templates endpoint.
- [ ] **5.7** Clone endpoint.
- [ ] **5.8** Tests: creation with items + taxes + discounts, totals
  correctness, status transitions, conversion.

### Frontend

- [ ] **5.9** Estimates list with filters.
- [ ] **5.10** Estimate create/edit form (line items, taxes, discounts,
  custom fields, notes).
- [ ] **5.11** Estimate detail view with status actions and PDF preview
  iframe (PDF comes in Phase 13 — render a placeholder until then).
- [ ] **5.12** "Send estimate" modal + preview.
- [ ] **5.13** Convert-to-invoice action.

**Checkpoint 5 ✅:** Estimates can be created, edited, sent (stub email),
accepted/rejected, and converted to invoices.

---

## Phase 6 — Invoices

**Reference:** `app/Http/Controllers/V1/Admin/Invoice/`,
`app/Models/Invoice.php`, `app/Models/InvoiceItem.php`,
`resources/scripts/admin/views/invoices/`,
`resources/scripts/admin/stores/invoice.js`.

> Dependencies: Phase 5 (share the line-item / tax / totals logic from
> Phase 5 — extract it into a shared `line_items` service on the backend
> and a `<LineItemsEditor />` component on the frontend).

### Backend

- [ ] **6.1** Models: `Invoice`, `InvoiceItem`. Status enum including
  `draft`, `sent`, `viewed`, `due`, `overdue`, `completed`.
- [ ] **6.2** CRUD + list + filters.
- [ ] **6.3** Change status, clone, send, preview endpoints.
- [ ] **6.4** Invoice templates endpoint.
- [ ] **6.5** Overdue/due computation (a scheduled task to flip status —
  real scheduling wired in Phase 9).
- [ ] **6.6** Tests.

### Frontend

- [ ] **6.7** Reuse `<LineItemsEditor />` and totals calculator.
- [ ] **6.8** Invoice list, create/edit, detail.
- [ ] **6.9** Send invoice modal + preview.
- [ ] **6.10** Clone and status actions.

**Checkpoint 6 ✅:** Invoice lifecycle is functional; conversion from
estimate produces a valid invoice.

---

## Phase 7 — Payments

**Reference:** `app/Http/Controllers/V1/Admin/Payment/`,
`app/Models/Payment.php`, `app/Models/PaymentMethod.php`,
`app/Models/Transaction.php`.

> Dependencies: Phase 6.

### Backend

- [ ] **7.1** Models: `Payment`, `PaymentMethod`. Link payment → invoice and
  update invoice paid status / due amount.
- [ ] **7.2** CRUD + list + filters + send-payment-receipt endpoint.
- [ ] **7.3** Stripe integration (optional for v1 but scaffold the
  `webhook/` router and a `PaymentProvider` abstraction).
- [ ] **7.4** Tests incl. over-payment / partial-payment edge cases.

### Frontend

- [ ] **7.5** Payments list + create/edit + detail.
- [ ] **7.6** "Record payment" modal from an invoice detail page.
- [ ] **7.7** Payment methods admin screen (under Settings).

**Checkpoint 7 ✅:** Admin can record payments, see invoice balances update,
and send receipts.

---

## Phase 8 — Expenses

**Reference:** `app/Http/Controllers/V1/Admin/Expense/`,
`app/Models/Expense.php`, `app/Models/ExpenseCategory.php`.

> Dependencies: Phase 4 (for custom fields + currency).

- [ ] **8.1** Models: `Expense`, `ExpenseCategory`.
- [ ] **8.2** CRUD + filters + receipt upload endpoint (temporary local
  storage until Phase 13).
- [ ] **8.3** Expenses list + form + detail in the frontend.
- [ ] **8.4** Expense categories settings screen.
- [ ] **8.5** Tests.

**Checkpoint 8 ✅:** Expense tracking works, including receipt upload and
categorisation.

---

## Phase 9 — Recurring invoices & scheduled jobs

**Reference:** `app/Http/Controllers/V1/Admin/RecurringInvoice/`,
`app/Models/RecurringInvoice.php`, `app/Console/`, `app/Jobs/`.

> Dependencies: Phase 6.

- [ ] **9.1** Set up Celery + Redis (or ARQ). Add a `worker` service to
  `docker-compose.yml`.
- [ ] **9.2** Model + CRUD for `RecurringInvoice` (cron expression,
  start/end, status).
- [ ] **9.3** Scheduled task that generates invoices from recurring
  definitions and emits "send invoice" jobs.
- [ ] **9.4** Scheduled task that flips invoice status to `overdue`.
- [ ] **9.5** Frontend list, create/edit, detail for recurring invoices.
- [ ] **9.6** Tests with a frozen clock.

**Checkpoint 9 ✅:** Recurring invoices generate on schedule in a test run.

---

## Phase 10 — Reports & dashboard

**Reference:** `app/Http/Controllers/V1/Admin/Report/`,
`app/Http/Controllers/V1/Admin/Dashboard/`,
`resources/scripts/admin/views/dashboard/`,
`resources/scripts/admin/views/reports/`.

- [ ] **10.1** Dashboard aggregate endpoint (totals, chart data by month,
  recent invoices / estimates).
- [ ] **10.2** Sales / expense / profit-loss / tax reports (JSON output now;
  PDF export comes in Phase 13).
- [ ] **10.3** Dashboard page on the frontend with charts (Recharts /
  Chart.js).
- [ ] **10.4** Reports pages with filters (date range, customer).
- [ ] **10.5** Tests: deterministic aggregate tests with seeded data.

**Checkpoint 10 ✅:** Dashboard and report screens render real data.

---

## Phase 11 — Customer portal

**Reference:** `app/Http/Controllers/V1/Customer/`,
`resources/scripts/customer/`.

> Dependencies: Phases 5–7.

- [ ] **11.1** Separate auth flow for customers (magic-link or
  email+password; mirror the reference).
- [ ] **11.2** Customer-scoped endpoints: own invoices, estimates,
  payments, profile.
- [ ] **11.3** Accept / reject estimate endpoint.
- [ ] **11.4** Pay invoice endpoint (stub until Stripe is live).
- [ ] **11.5** Customer portal UI (list screens, detail screens, pay
  action, accept/reject buttons).
- [ ] **11.6** Tests incl. strict authorisation: a customer can only see
  their own data.

**Checkpoint 11 ✅:** Customer portal is usable end-to-end.

---

## Phase 12 — Settings, custom fields, notes

**Reference:** `app/Http/Controllers/V1/Admin/Settings/`,
`app/Http/Controllers/V1/Admin/General/NotesController.php`,
`resources/scripts/admin/views/settings/`.

- [ ] **12.1** Company settings endpoints (preferences, notifications,
  numbering, address formats, etc.).
- [ ] **12.2** Notes templates CRUD.
- [ ] **12.3** File disks settings (local / S3 / Dropbox — only implement
  local + S3 for v1).
- [ ] **12.4** Mail driver settings.
- [ ] **12.5** Settings UI (tabbed page under `/admin/settings`).
- [ ] **12.6** Tests.

**Checkpoint 12 ✅:** All tabs under `/admin/settings` are implemented.

---

## Phase 13 — PDF, email, file storage

- [ ] **13.1** PDF rendering: pick one of `WeasyPrint`, `ReportLab`, or
  headless-Chrome via `playwright`. Document the trade-off. Generate
  invoice, estimate, and payment-receipt PDFs.
- [ ] **13.2** Swap stub email sending for a real mailer (`fastapi-mail` or
  direct SMTP). Support per-company templates.
- [ ] **13.3** Swap local-disk uploads for a pluggable storage backend
  (local + S3). Signed URLs for downloads.
- [ ] **13.4** Wire PDF preview into the frontend invoice / estimate /
  payment detail pages.
- [ ] **13.5** Tests (snapshot-test the PDFs by hashing rendered output).

**Checkpoint 13 ✅:** Emails go out with real PDF attachments; uploaded
receipts are served from S3 in staging.

---

## Phase 14 — Hardening & release

- [ ] **14.1** OWASP top-10 review: rate limiting, CSRF strategy (cookies
  vs. tokens), input validation audit, password policy.
- [ ] **14.2** Performance pass: N+1 queries via `sqlalchemy` eager loading,
  frontend code-splitting, React Query cache tuning.
- [ ] **14.3** E2E tests with Playwright for the golden paths: login →
  create customer → create invoice → record payment.
- [ ] **14.4** Staging deploy pipeline. Database migration strategy
  (blue-green or expand-contract) documented.
- [ ] **14.5** Production deploy + runbook.
- [ ] **14.6** Write a migration / data-import script for teams moving from
  the reference app (schema mapping).

**Checkpoint 14 ✅:** v1.0.0 tagged and deployed to production.

---

## Milestones & checkpoints

| Milestone | Covers phases | What "done" looks like |
|-----------|---------------|------------------------|
| **M0 — Skeleton**        | 0           | Docker Compose boots both services, CI is green. |
| **M1 — Platform ready**  | 1–2         | Backend + frontend skeletons with auth-less routing, typed API client. |
| **M2 — Auth & tenants**  | 3           | Install wizard, login, multi-company switching. |
| **M3 — Core domain**     | 4           | Customers, items, taxes, custom fields. |
| **M4 — Billing**         | 5–7         | Estimates, invoices, and payments end-to-end. |
| **M5 — Business ops**    | 8–10        | Expenses, recurring invoices, dashboard, reports. |
| **M6 — Customer-facing** | 11–13       | Customer portal, full settings, PDFs, email, S3. |
| **M7 — Release**         | 14          | v1.0.0 in production. |

Track milestones in the issue tracker; close a milestone only when every
task inside it is merged **and** its checkpoint acceptance criteria pass.

---

## Task dependency graph

```
Phase 0
  └── Phase 1 ─┐
  └── Phase 2 ─┤
               └── Phase 3 ── Phase 4 ─┬── Phase 5 ── Phase 6 ── Phase 7
                                       ├── Phase 8
                                       └── Phase 12
                                  (Phase 6) ── Phase 9
                                  (Phase 6) ── Phase 10
                               (Phases 5-7) ── Phase 11
                                  (all) ── Phase 13 ── Phase 14
```

Interpretation:

- Phases 1 and 2 can run **in parallel** after Phase 0.
- Phase 4 is a fan-out point: once it's done, Phase 8 and Phase 12 can run
  in parallel with the 5 → 6 → 7 chain.
- Phases 9, 10, and 11 all depend on the Phase 5–7 chain being complete.
- Phase 13 can start incrementally as soon as any feature needs PDFs or
  email, but its completion is a prerequisite for Phase 14.

---

## Definition of Done (per task)

A task is only considered **done** when **all** of the following hold:

1. Code is merged to `main` via a reviewed PR.
2. CI is green (lint + type check + unit tests + build).
3. New behaviour has automated tests (backend: pytest; frontend: Vitest +
   React Testing Library).
4. The PR description links to the reference file(s) in `crater-master/`
   that inspired the task and notes any intentional divergence.
5. No copy-pasted code from the reference (license compliance).
6. OpenAPI schema is up to date and the frontend's generated types have
   been regenerated.
7. Manual smoke test in `docker compose up` confirms the user-visible
   behaviour described in the task.

---

*Last updated: 2026-04-23. Edit this file in a PR whenever scope changes or
a milestone closes.*
