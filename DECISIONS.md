# Technical Decisions

## Architecture Decisions

### 1. Django REST Framework (not Next.js API routes)
**Decision**: Use Django + DRF as the backend.
**Why**: The JD specifically asks for Django REST APIs and Python. DRF provides battle-tested serialization, authentication (Token auth), and permission classes out of the box. ViewSets + ModelSerializers map naturally to our CRUD-heavy data model.

### 2. React + Vite (not server-rendered)
**Decision**: SPA frontend with React, Vite as build tool.
**Why**: The balance drill-down UI (Rohan's requirement) and import review flow (Meera's requirement) require rich interactivity. A SPA gives us client-side routing, state management without page reloads, and a snappy UX. Vite provides fast HMR during development.

### 3. Token Authentication (not JWT)
**Decision**: DRF's built-in TokenAuthentication.
**Why**: Simpler than JWT (no refresh token dance), persistent across browser sessions via localStorage, and sufficient for this use case. Tokens are created on login and deleted on logout.

### 4. SQLite for development (PostgreSQL-ready)
**Decision**: SQLite locally, `dj-database-url` for production PostgreSQL.
**Why**: Zero-config local development. The `dj-database-url` package makes switching to PostgreSQL (Neon/Railway) a one-line env var change: `DATABASE_URL=postgres://...`

### 5. Decimal over Float
**Decision**: Use Python `Decimal` and Django `DecimalField` for all amounts.
**Why**: Floating point arithmetic causes rounding errors in financial calculations. `₹899.995 / 4` must be predictable. All amounts are quantized to 2 decimal places.

## Data Model Decisions

### 6. Separate Settlement model (not Expense.is_settlement)
**Decision**: We have both `Expense.is_settlement` flag AND a separate `Settlement` model.
**Why**: The CSV contains settlement-like entries (row 14: "Rohan paid Aisha back", row 38: "Sam deposit share"). During import, these are detected as settlements and stored in the `Settlement` model. The `is_settlement` flag on `Expense` is a safety net for direct API creation. Balance calculation uses `Settlement` records to deduct from balances.

### 7. Membership dates on GroupMember (not just is_active)
**Decision**: Store `joined_at` and `left_at` dates, not just a boolean.
**Why**: Critical for correct balance calculation. Meera left March 31, so she shouldn't owe for April expenses. Sam joined April 8, so he shouldn't owe for March expenses. The `was_active_on(date)` method checks this per-expense.

### 8. Store amount_inr on every Expense
**Decision**: Pre-compute `amount_inr` at creation time, store as a field.
**Why**: Balance calculations must always work in INR. Converting on-the-fly would require looking up the exchange rate each time. By storing `amount_inr` and `exchange_rate` per expense, the balance service just sums pre-converted values. The Goa trip USD expenses use ₹84/USD as the fixed rate.

## Import Pipeline Decisions

### 9. 3-Phase pipeline (Parse → Analyze → Commit)
**Decision**: Separate parsing, analysis, and commitment into three distinct phases.
**Why**:
- **Phase 1 (parser.py)**: Format-level fixes (commas, dates, names). These are safe auto-fixes.
- **Phase 2 (analyzer.py)**: Business-logic anomalies (duplicates, settlements, membership). These need human review.
- **Phase 3 (importer.py)**: Database commitment after user approves.

This separation makes each phase independently testable and gives the user full control (Meera's requirement).

### 10. Store raw_data as JSON on ImportSession
**Decision**: Keep the full parsed CSV data as a JSONField.
**Why**: The user needs to review and modify data between upload and confirm. Storing as JSON means we can show the review UI without re-parsing the file. It also serves as an audit trail.

### 11. AI as enhancement, not dependency
**Decision**: Gemini API calls are wrapped in try/catch, failures are silently ignored.
**Why**: AI features (better anomaly descriptions, expense categorization) improve UX but aren't required for core functionality. If the API key is missing or the service is down, the app works identically using deterministic descriptions.

## Frontend Decisions

### 12. Vanilla CSS design system (not Tailwind/CSS-in-JS)
**Decision**: Custom CSS with CSS custom properties (design tokens).
**Why**: Full control over the premium dark theme aesthetic. CSS custom properties give us a design system (colors, spacing, typography) without runtime overhead. Glassmorphism, gradient accents, and micro-animations work naturally in vanilla CSS.

### 13. Direct API calls (not React Query/SWR)
**Decision**: Raw Axios calls in useEffect hooks.
**Why**: Simpler for the scope of this project. Each page fetches its data on mount. The app doesn't need background refetching, cache invalidation, or optimistic updates.

## Currency Handling

### 14. Fixed exchange rate (₹84/USD)
**Decision**: Use a configurable but fixed exchange rate instead of live API calls.
**Why**: The CSV has 4 USD expenses (Goa trip). A fixed rate is deterministic and testable. The rate is stored per-expense in `exchange_rate`, so it can be overridden per-entry during import review. Configurable via `USD_TO_INR_RATE` env var.
