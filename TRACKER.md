# Bij-Ganit — Sprint Tracker

This file is the **running log of what has been shipped** on the FastAPI +
React migration. The authoritative plan lives in `MIGRATION_ROADMAP.md`
(read-only reference) and the intern sprint task list is the GitHub
issue/message thread.

**DO NOT** modify `MIGRATION_ROADMAP.md` from this branch. Update this
tracker instead.

## How to read this file

For each completed sprint below there is a short **summary** of what
shipped, **where to look**, and **notes for the next intern**. The
*current* sprint (the one you are about to work on) is written as a
detailed task checklist with acceptance criteria.

New developers: skim Sprints 0–2 to understand the scaffolding, then jump
to the **Current Sprint** section at the bottom.

---

## Sprint 0 — Project Setup & Scaffolding — DONE

**Summary.** Stand up a FastAPI backend, a Vite/React 19 frontend, a
docker-compose stack (Postgres 15 + Redis 7 + backend + frontend), and
wire up SQLAlchemy 2.0 (async) with Alembic (sync driver). Configuration
is driven by `pydantic-settings` reading `.env`.

Key files:

* `backend/app/main.py` — FastAPI app, CORS, mounts `/api/v1`, exposes
  `GET /api/ping` → `{"success":"ok"}`.
* `backend/app/database.py` — async engine, `AsyncSessionLocal`,
  `get_db()` dependency, shared `Base`.
* `backend/app/config.py` + `backend/.env.example` — settings, async +
  sync DB URLs.
* `backend/alembic/` — Alembic is wired to the **sync** URL
  (`psycopg2`); the app itself uses the **async** URL (`asyncpg`).
* `frontend/` — Vite + React 19 + TS + Tailwind 3 + React Router v6 +
  Axios + Zustand. `vite.config.ts` proxies `/api` → `localhost:8000`.
* `docker-compose.yml` — `db`, `redis`, `backend` (runs `alembic upgrade
  head` then `uvicorn --reload`), `frontend`.

Try it:

```bash
# backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
curl http://localhost:8000/api/ping    # {"success":"ok"}

# frontend (separate shell)
cd frontend && npm install && npm run dev    # http://localhost:5173

# or everything
docker-compose up --build
```

---

## Sprint 1 — Auth + Users + Companies — DONE

**Summary.** JWT-based auth, three DB tables (`users`, `companies`,
`user_company`), CRUD endpoints for users and companies, a multi-tenancy
dependency that reads the active company from a request header, and a
React login + app shell with a company switcher.

Schema highlights (migration `0001_initial_users_companies.py`):

* `users(id, name, email UNIQUE, phone, password, role, creator_id,
  company_id, timestamps)`
* `companies(id, name, slug UNIQUE, unique_hash, owner_id, timestamps)`
  — `slug` + `owner_id` are additions beyond the Crater reference.
* `user_company(id, user_id, company_id, timestamps)` with a unique
  `(user_id, company_id)` constraint.

Backend (`backend/app/...`):

* `core/security.py` — `hash_password`, `verify_password` (passlib +
  bcrypt), `create_access_token`, `verify_token` (python-jose).
* `core/deps.py` — `get_current_user` (Bearer JWT) and
  `get_current_company` (reads the `company` header and checks ownership
  or `user_company` membership).
* `api/v1/auth.py` — `POST /auth/login`, `POST /auth/logout` (stateless),
  `GET /auth/check`.
* `api/v1/companies.py` — `GET/POST /companies`, `POST /companies/delete`
  (owner-only). Create auto-slugifies, inserts the owner + pivot row,
  and calls `services/company_defaults.setup_default_data()` (see below).
* `api/v1/users.py` — `GET/POST /users`, `PUT /users/{id}` (re-hashes
  password if present), `POST /users/delete` (can't delete self).

Frontend:

* `pages/LoginPage.tsx` — posts to `/api/v1/auth/login`, stores the JWT
  in the Zustand auth store (persisted to localStorage).
* `components/AppLayout.tsx` + `RequireAuth.tsx` — sidebar (9 nav
  links), header with a company `<select>` fed by `GET /companies` and
  backed by `stores/companyStore`. `api/client.ts` injects the active
  company id as the `company` header on every request.

Notes for the next intern:

* `services/company_defaults.py::setup_default_data` is an **intentional
  no-op**. Its call site in `POST /companies` is wired; fill in the body
  once the `payment_methods`, `units`, and `company_settings` tables
  land. The remaining ~30 settings keys live in
  `crater-master/app/Models/Company.php` lines 194-253.

Tests: `backend/tests/test_ping.py`, `backend/tests/test_security.py`
(all green under `pytest -q`).

---

## Sprint 2 — Customers + Items + Tax Types (Master Data) — DONE

**Summary.** Seeded lookup tables (currencies, countries), customer +
address models with billing/shipping, item model with per-item taxes,
tax types, full CRUD for each, lookup endpoints for the frontend, and
React list + form pages for customers and items. Everything is
company-scoped via `Depends(get_current_company)`.

Shipped in migration `0002_sprint2_master_data.py` +
`backend/app/{models,schemas,api/v1,seed_data}/...` +
`frontend/src/pages/{customers,items}/`.

Highlights:

* **Lookups.** `currencies` (153 ISO 4217 rows) and `countries` (246 ISO
  3166 rows) seeded via `op.bulk_insert` from `app/seed_data/`.
  Endpoints: `GET /api/v1/{countries,currencies,timezones,date/formats}`
  (public, no auth — matches the reference).
* **Customers + addresses.** `Customer` (name, email, phone,
  contact/company name, website, `enable_portal`, nullable hashed
  `password`, currency/company/creator FKs). `Address` keyed to
  `customer_id` with `type` enum `billing|shipping` and a `country_id`
  FK; cascade-deletes with its customer.
* **Items + units.** `Item` with BigInt `price`, `tax_per_item`,
  `unit_id`/`currency_id`/`company_id`/`creator_id`. CRUD at
  `/api/v1/items` + `/delete`, and `/api/v1/units` (inline CRUD).
  Item create/update atomically replaces linked taxes.
* **Tax types + taxes.** `TaxType` (`percent` numeric 5,2,
  `compound_tax`, `collective_tax`, `type`, `description`). `Tax` has
  polymorphic-ish FKs — `item_id` is a real FK today;
  `invoice_id`/`estimate_id` are plain nullable Integers until those
  tables land.
* **Customer CRUD.** `GET/POST/PUT /customers`, `POST /customers/delete`,
  `GET /customers/{id}`, `GET /customers/{id}/stats`. List supports
  `search` (name/contact_name/company_name ILIKE), `from_date`/`to_date`,
  `order_by`/`order`. Create/update accept nested billing + shipping
  address payloads.
* **Frontend.** `CustomersListPage` + `CustomerFormPage` (address
  sections, currency dropdown), `ItemsListPage` + `ItemFormPage` (unit +
  currency dropdowns, tax type checkboxes, currency-aware price
  formatting). Both lists support search + client-side pagination.

Notes for the next intern:

* Invoice/estimate FKs on `taxes` are **not** enforced at the DB level
  yet. Add them in a follow-up migration once those tables land in
  Sprint 3.
* `CustomerStats` currently returns `total_customers` only — the
  invoice/payment/due fields are exposed but return 0 until invoices
  exist.
* `/api/v1/currencies` returns synthetic ids (index + 1) so the frontend
  can key dropdowns; they match the auto-increment ids produced by
  `bulk_insert` in Postgres.

Tests: `pytest -q` → 12 passing (4 sprint 1 + 8 sprint 2).

---

## Current Sprint

## Sprint 3 — Invoices (Core Feature) — TODO

This sprint adds the first transactional feature. It depends on the
Sprint 2 `customers`, `items`, `tax_types`, `taxes`, `currencies`, and
`companies` tables and on the `get_current_company` dependency.

Everything below should land under:

* Migration: `backend/alembic/versions/0003_sprint3_invoices.py`
* Models: `backend/app/models/invoice.py`, `invoice_item.py`
* Schemas: `backend/app/schemas/invoice.py`
* Services: `backend/app/services/serial_number.py`,
  `backend/app/core/hashids.py`
* Routes: `backend/app/api/v1/invoices.py`

All monetary fields are **BigInt** (cents/lowest-denomination), matching
the Crater reference. Every query and write must be scoped to
`company.id` via `Depends(get_current_company)`.

### 3.1 `invoices` table migration

**Reference.** `crater-master/database/migrations/2017_04_12_090759_create_invoices_table.php`
and the subsequent `alter_*_invoices_table` migrations.

Fields:

* Identifiers + dates: `id`, `invoice_number`, `invoice_date`,
  `due_date`, `reference_number`, `sequence_number`,
  `customer_sequence_number`, `unique_hash`, `template_name`.
* Status: `status` enum `DRAFT|SENT|VIEWED|COMPLETED`, `paid_status`
  enum `UNPAID|PARTIALLY_PAID|PAID`, booleans `sent`, `viewed`,
  `overdue`.
* Flags: `tax_per_item` (YES/NO), `discount_per_item` (YES/NO),
  `discount_type` (percentage/fixed), `notes`.
* Money (all **BigInt**): `discount`, `discount_val`, `sub_total`,
  `total`, `tax`, `due_amount`, plus `base_*` columns
  (`base_discount_val`, `base_sub_total`, `base_total`, `base_tax`,
  `base_due_amount`) and `exchange_rate` for multi-currency bookkeeping.
* FKs: `currency_id`, `customer_id`, `company_id`, `creator_id`,
  `recurring_invoice_id` (nullable — the recurring_invoices table
  doesn't exist yet; make the FK nullable with no server-side enforcement
  OR defer the FK constraint to a follow-up migration, consistent with
  how Sprint 2 handled `taxes.invoice_id`).
* Sales tax: `sales_tax_type`, `sales_tax_address_type`.

Also in this migration: add the deferred `taxes.invoice_id` FK
constraint from Sprint 2.

**Acceptance.** `alembic upgrade head` runs cleanly on an empty DB and
on a DB already at revision `0002`.

### 3.2 `invoice_items` table migration

**Reference.** `crater-master/database/migrations/2017_04_12_091015_create_invoice_items_table.php`.

Fields: `id`, `name`, `description`, `discount_type`, `price` (BigInt),
`quantity` (BigInt), `discount` (BigInt), `discount_val` (BigInt), `tax`
(BigInt), `total` (BigInt), `unit_name`, `base_price`,
`base_discount_val`, `base_tax`, `base_total`, `exchange_rate`,
`invoice_id` (FK, cascade), `item_id` (FK nullable — history stays even
if the catalog item is later deleted), `company_id` (FK),
`recurring_invoice_id` (FK nullable).

**Acceptance.** Migration runs; `invoice_items.invoice_id` cascade-deletes
with its parent invoice.

### 3.3 `Invoice` + `InvoiceItem` SQLAlchemy models

**Reference.** `crater-master/app/Models/Invoice.php` lines 65-113 for
the relationship names.

Relationships on `Invoice`:

* `items` → `InvoiceItem` (one-to-many, cascade delete)
* `taxes` → `Tax` filtered by `invoice_id` (one-to-many)
* `payments` → `Payment` (one-to-many; model doesn't exist yet — declare
  the relationship with a string target and mark it as Sprint 5+ work;
  it can stay empty for now)
* `customer` → `Customer` (many-to-one)
* `currency` → `Currency` (many-to-one)
* `company` → `Company` (many-to-one)
* `creator` → `User` (many-to-one via `creator_id`)

Use SQLAlchemy 2.0 typed mappings (`Mapped[...]`, `mapped_column(...)`)
to match the style of Sprint 2 models.

**Acceptance.** `python -c "from app.models.invoice import Invoice;
print(Invoice.__table__)"` works and the relationships above are
navigable on a persisted instance in a test.

### 3.4 Serial number formatter service

**Reference.** `crater-master/app/Models/Company.php` line 239, default
format `{{SERIES:INV}}{{DELIMITER:-}}{{SEQUENCE:6}}`.

Location: `backend/app/services/serial_number.py`.

Contract: `next_invoice_number(db, company_id, customer_id) -> str` that
parses the template from `company_settings` (falling back to the
default above when the key is missing — remember `company_settings` is
still stubbed from Sprint 1.9; until that lands, use the constant
default and read the override if the row exists) and increments the
per-company and per-customer sequence counters atomically. The sequence
counter is what gets written back to
`invoices.sequence_number` + `customer_sequence_number` on the newly
created row.

**Acceptance.** Generating two invoices in sequence for the same
company yields `INV-000001` then `INV-000002`. Writing a custom format
like `{{SERIES:INV}}{{DELIMITER:/}}{{SEQUENCE:4}}` yields `INV/0001`.

### 3.5 Hashids utility

**Reference.** `crater-master/app/Models/Invoice.php` line 335.

Location: `backend/app/core/hashids.py`. Add `hashids` to
`backend/requirements.txt`.

Contract: `encode(kind: Literal["invoice","estimate","payment"], id:
int) -> str` and a matching `decode`. Each model type gets its own salt
(pull salts from `app/config.py` settings with sensible defaults) so a
leaked invoice hash can't be used to guess estimate/payment hashes.

**Acceptance.** `encode("invoice", 1)` is deterministic and round-trips
through `decode`. Different `kind`s for the same `id` produce different
hashes.

### 3.6 `POST /api/v1/invoices` — create endpoint

**Reference.** `crater-master/app/Models/Invoice.php` lines 317-364.

Request body:

* `customer_id`, `invoice_date`, `due_date`, `discount`, `discount_type`
  (`percentage|fixed`), `notes`, `reference_number`, `template_name`,
  `tax_per_item`, `discount_per_item`.
* `items: [{ item_id?, name, description?, price, quantity, discount?,
  discount_type?, unit_name?, taxes: [{ tax_type_id, amount, percent,
  compound_tax, ...}] }]`
* `taxes: [{ tax_type_id, amount, percent, compound_tax, ...}]`
  (invoice-level taxes — only present when `tax_per_item` is false).
* `custom_fields` (optional; model doesn't exist yet, skip until Sprint
  12 but accept and discard the payload shape so the frontend can send it).

Server logic (do it all inside one DB transaction):

1. Resolve the active `company` from `get_current_company`.
2. Generate the serial number via 3.4 and the `unique_hash` via 3.5
   (encode a freshly-reserved invoice id — either reserve via a sequence
   or insert the invoice row then update the hash after flush).
3. Insert the `Invoice` row. Populate the `base_*` columns and
   `exchange_rate` from the customer's currency against the company's
   base currency. If they match, `exchange_rate = 1` and each `base_*`
   equals its counterpart.
4. Insert `InvoiceItem` rows, computing each item's `total` from
   `price * quantity - discount_val + tax` and the matching `base_*`.
5. Insert per-item `taxes` rows (with `item_id` set) and invoice-level
   `taxes` rows (with `invoice_id` set) as appropriate.
6. Set `due_amount = total` (no payments exist yet at create time).
7. Respond with the hydrated invoice including items + taxes +
   customer.

**Acceptance.** Posting a valid body creates an invoice whose
`sub_total`, `tax`, `discount_val`, `total`, and `due_amount` all match
a hand-computed expectation. `invoice_number` follows the configured
template. The response includes the `unique_hash`.

### 3.7 `PUT /api/v1/invoices/{id}` — update endpoint

**Reference.** `crater-master/app/Models/Invoice.php` lines 366-439.

Rules:

* **Customer lock.** If any `payments` exist against this invoice the
  `customer_id` cannot change; return `422` if the client tries.
* **Paid floor.** The new `total` must be `>=` the sum of applied
  payments (i.e. you can't lower the invoice below what's already been
  paid). Return `422` otherwise.
* Delete the existing `invoice_items` and the invoice-level/per-item
  `taxes` rows, then recreate from the request (same transformation as
  3.6).
* Recalculate `due_amount = total - paid_amount`.
* Recompute `paid_status`:
  * `paid_amount == 0` → `UNPAID`
  * `0 < paid_amount < total` → `PARTIALLY_PAID`
  * `paid_amount >= total` → `PAID`
* Recompute `overdue` (boolean) based on `due_date < today` AND
  `paid_status != PAID`.
* Everything stays in one transaction.

**Acceptance.** Updating an invoice with payments attached preserves
the existing payments, rejects customer changes, correctly recalculates
`due_amount` and `paid_status`, and leaves item/tax rows in a consistent
state.

### Out of scope for Sprint 3 (but good to know)

* **Recurring invoices.** `recurring_invoice_id` is a nullable FK with
  no target table yet — that's Sprint 8 or similar.
* **Custom fields.** Accept-and-discard on the request body; actual
  storage is Sprint 12.
* **`company_settings`.** Still stubbed. Use the default serial number
  template for now.
* **Email / PDF rendering.** The `SENT`/`VIEWED` transitions are just
  status updates this sprint; the actual email + PDF pipeline is a
  later sprint.
* **Customer portal viewing.** Sprint 11.

### Suggested task order

1. 3.5 hashids (tiny, unblocks 3.6).
2. 3.4 serial number formatter + unit tests.
3. 3.1 + 3.2 migrations (and the deferred `taxes.invoice_id` FK).
4. 3.3 models.
5. 3.6 create endpoint + integration test.
6. 3.7 update endpoint + integration test (blocked on 3.6 being green).

Don't forget to add new `pytest` coverage alongside each step — the
repo convention is to keep `pytest -q` green at every commit.

---

## Glossary / "Why did you do X?"

* **Why async SQLAlchemy but sync Alembic?** Alembic's tooling is
  battle-tested on the sync driver (`psycopg2`); the app itself benefits
  from the async driver (`asyncpg`). Settings expose both URLs so each
  tool gets what it wants.
* **Why JWT and not Laravel Sanctum / DB-backed tokens?** Stateless
  tokens keep the FastAPI backend deployable behind any load balancer
  without sticky sessions or a shared token table. Revocation can land
  later as a Redis blacklist.
* **Why put the active company id in a header instead of the URL?** The
  reference Laravel app does the same thing (via middleware). Keeping
  it out of the URL means the same route can be bookmarked across
  tenants by the same user.
* **Why is `crater-master/` still in the repo?** It is the reference
  application. Read-only. Do not modify it and do not copy code
  verbatim — re-implement behaviour in the new stack.

## Running the full stack

```bash
# 1. Backend deps + tests
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q                       # 12 passing after Sprint 2

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
