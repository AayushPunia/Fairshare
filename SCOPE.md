# Scope Document

## What This App Does

FairShare is a shared expense tracker designed for a group of flatmates. It handles:

### Core Features
1. **User Authentication** — Token-based auth with DRF, pre-seeded demo users
2. **Group Management** — Create groups, add/remove members with join/leave dates
3. **Expense Tracking** — 4 split types (equal, unequal, percentage, shares), multi-currency
4. **CSV Import Engine** — 3-phase pipeline: Parse → Analyze → Review → Commit
5. **Anomaly Detection** — 16 anomaly types detected across format, logic, and membership
6. **Balance Calculation** — Membership-aware, multi-currency, with full drill-down
7. **Settlement Optimization** — Greedy min-transactions algorithm
8. **AI Enhancement** — Gemini API for anomaly descriptions and categorization (optional)

### Personas Addressed
- **Rohan** (Detail Checker): "If the app says I owe ₹2,300, show me exactly which expenses make that up" → Balance drill-down with expandable expense lists
- **Aisha** (Pragmatist): "One number per person — who pays whom, how much, done" → Settlement optimizer with single-view results
- **Meera** (Trust Verifier): "I want to approve anything the app deletes or changes" → Import review UI with approve/skip controls per anomaly

## What This App Does NOT Do

1. **Real-time sync** — No WebSocket/push updates. Users refresh to see changes.
2. **Multi-group balances** — Balances are per-group, not cross-group.
3. **Recurring expenses** — No auto-repeat for rent/bills. Each entry is manual or CSV-imported.
4. **Payment integration** — No UPI/bank integration. Settlements are recorded manually.
5. **Mobile native app** — Responsive web only, no iOS/Android app.
6. **Advanced permissions** — All group members can edit/delete any expense. No role-based access.
7. **Historical exchange rates** — Uses a fixed USD→INR rate (₹84), not live market rates.

## Known Limitations

- **Dev is treated as a guest**, not a permanent member. He appears in Goa trip expenses but isn't in the group membership. Guest users are auto-created during import.
- **The CSV parser assumes DD-MM-YYYY** as the dominant date format. Ambiguous dates like "04-05-2026" default to DD-MM but flag a critical anomaly for user review.
- **Percentage normalization**: If percentages sum to 110%, the importer normalizes proportionally (30/30/30/20 → 27.27/27.27/27.27/18.18).

---

## Database Schema

```
┌─────────────────────┐     ┌──────────────────────┐     ┌───────────────────┐
│       User          │     │       Group           │     │   GroupMember      │
│─────────────────────│     │──────────────────────│     │───────────────────│
│ id (PK)             │     │ id (PK)              │     │ id (PK)           │
│ username             │     │ name                 │     │ group_id (FK)     │
│ display_name         │←───│ created_by_id (FK)   │────→│ user_id (FK)      │
│ email                │     │ description          │     │ joined_at (date)  │
│ password (hashed)    │     │ default_currency     │     │ left_at (date?)   │
│ first_name           │     │ created_at           │     │ is_active (bool)  │
└─────────────────────┘     │ updated_at           │     └───────────────────┘
                             └──────────────────────┘
                                      │
                                      │ 1:N
                                      ▼
┌───────────────────────────────────────┐     ┌─────────────────────────────┐
│             Expense                    │     │       ExpenseSplit          │
│───────────────────────────────────────│     │─────────────────────────────│
│ id (PK)                               │     │ id (PK)                    │
│ group_id (FK → Group)                 │────→│ expense_id (FK → Expense)  │
│ paid_by_id (FK → User)               │     │ user_id (FK → User)        │
│ description (varchar 500)             │     │ share_amount (decimal INR) │
│ amount (decimal 12,2)                 │     │ share_percentage (decimal?) │
│ currency (INR / USD)                  │     │ share_units (int?)         │
│ amount_inr (decimal — converted)      │     └─────────────────────────────┘
│ exchange_rate (decimal, default 1.0)  │
│ split_type (equal/unequal/pct/share)  │
│ date                                  │
│ notes                                 │
│ is_settlement (bool)                  │
│ import_session_id (FK → ImportSession)│
│ created_at, updated_at               │
└───────────────────────────────────────┘

┌───────────────────────────────────────┐
│           Settlement                   │
│───────────────────────────────────────│
│ id (PK)                               │
│ group_id (FK → Group)                 │
│ from_user_id (FK → User)  ── payer    │
│ to_user_id (FK → User)   ── receiver  │
│ amount (decimal 12,2)                 │
│ currency                              │
│ date                                  │
│ notes                                 │
│ created_at                            │
└───────────────────────────────────────┘

┌───────────────────────────────────────┐     ┌──────────────────────────────┐
│         ImportSession                  │     │      ImportAnomaly           │
│───────────────────────────────────────│     │──────────────────────────────│
│ id (PK)                               │     │ id (PK)                     │
│ group_id (FK → Group)                 │────→│ import_session_id (FK)      │
│ uploaded_by_id (FK → User)            │     │ row_number (int)            │
│ filename                              │     │ field (varchar 50)          │
│ status (pending/reviewing/completed)  │     │ anomaly_type (16 types)     │
│ raw_data (JSON — full parsed CSV)     │     │ original_value (text)       │
│ total_rows                            │     │ corrected_value (text)      │
│ imported_rows                         │     │ severity (info/warn/err/crit)│
│ skipped_rows                          │     │ auto_resolved (bool)        │
│ anomalies_count                       │     │ user_action (pending/       │
│ created_at                            │     │   auto_fixed/approved/      │
│ completed_at                          │     │   modified/skipped)         │
└───────────────────────────────────────┘     │ description (text)          │
                                               │ ai_description (text)       │
                                               │ related_row (int?)          │
                                               └──────────────────────────────┘
```

### Key Design Choices

| Decision | Why |
|---|---|
| `amount_inr` on every Expense | Pre-computed INR amount avoids repeated conversion during balance calculations |
| `joined_at` + `left_at` on GroupMember | Enables membership-aware balance calculation (Meera left March 31, Sam joined April 8) |
| Separate `Settlement` model | Clean separation between shared expenses and inter-person payments |
| `raw_data` as JSON on ImportSession | Preserves full CSV data for review UI without re-parsing the file |
| `ai_description` separate from `description` | AI output never overwrites deterministic descriptions — full fallback support |

---

## Anomaly Log — Every Data Problem in the CSV

### Format-Level Issues (Auto-Fixed by Parser)

| Row | Field | Problem | How We Handled It |
|-----|-------|---------|-------------------|
| 7 | amount | Comma in amount: `"1,200"` | Stripped comma → `1200`. Standard spreadsheet artifact. |
| 9 | paid_by | Lowercase: `priya` | Normalized to `Priya` via known-names lookup. |
| 10 | amount | Excessive decimals: `899.995` | Rounded to `900.00` (2-decimal currency standard). |
| 11 | paid_by | Name variant: `Priya S` | Mapped to `Priya` via variant lookup table. |
| 26 | amount | Negative: `-30` USD | Kept as refund/credit. Context: "one slot got cancelled". |
| 27 | date | Non-standard: `Mar-14` | Parsed as `2026-03-14`. Year inferred from context. |
| 27 | paid_by | Trailing space: `rohan ` | Stripped + normalized → `Rohan`. |
| 28 | currency | Missing currency field | Defaulted to `INR` (group's default). |
| 42 | split_type | Conflicting: `equal` with share details `1;1;1;1` | Honored `split_type=equal` since shares are all equal anyway. |

### Business-Logic Issues (Flagged for User Review)

| Row | Problem | Severity | How We Handled It |
|-----|---------|----------|-------------------|
| 6 | **Duplicate**: Same dinner (Marina Bites) logged twice by Dev, same date + amount | Warning | Skipped Row 6, kept Row 5 (first entry). Fuzzy match score: 73%. |
| 13 | **Missing payer**: "House cleaning supplies" — `paid_by` is empty | Critical | Flagged for manual assignment. Notes: "can't remember who paid". |
| 14 | **Settlement as expense**: "Rohan paid Aisha back" ₹5,000 | Warning | Detected via keywords ("paid back") + missing split_type. Imported as Settlement record. |
| 15 | **Percentage sum = 110%**: 30+30+30+20 ≠ 100 | Warning | Normalized proportionally → 27.27/27.27/27.27/18.18. Preserves original ratios. |
| 23 | **Non-member**: "Dev's friend Kabir" | Warning | Created as guest participant for this expense only. |
| 24–25 | **Duplicate conflict**: Thalassa dinner logged by two people with different amounts | Warning | User chose Row 24 (Aisha, ₹2,400). Row 25 skipped. |
| 31 | **Zero amount**: "Dinner order Swiggy" for ₹0 | Warning | Skipped. Notes: "counted twice earlier — fixing later". |
| 32 | **Percentage sum = 110%**: Same 30/30/30/20 pattern | Warning | Same proportional normalization as Row 15. |
| 34 | **Ambiguous date**: `04-05-2026` — April 5 or May 4? | Critical | Defaulted to DD-MM (May 4). 41/43 rows use DD-MM consistently. User confirmed. |
| 36 | **Departed member**: Meera in April 2 expense, but she left March 31 | Warning | Removed Meera from split. Amount re-divided among 3 members. |
| 38 | **Settlement as expense**: "Sam deposit share" ₹15,000 to Aisha | Warning | Detected via keywords ("deposit share"). Imported as Settlement record. |

### Anomaly Type Inventory (16 Types)

| # | Type | Category | Count in CSV |
|---|------|----------|-------------|
| 1 | `format_amount` | Format | 1 |
| 2 | `format_date` | Format | 1 |
| 3 | `name_case` | Format | 2 |
| 4 | `name_variant` | Format | 1 |
| 5 | `missing_currency` | Format | 1 |
| 6 | `decimal_precision` | Format | 1 |
| 7 | `negative_amount` | Format | 1 |
| 8 | `zero_amount` | Logic | 1 |
| 9 | `missing_payer` | Logic | 1 |
| 10 | `duplicate` | Logic | 1 |
| 11 | `duplicate_conflict` | Logic | 1 |
| 12 | `settlement_as_expense` | Logic | 2 |
| 13 | `percentage_sum` | Logic | 2 |
| 14 | `non_member` | Membership | 1 |
| 15 | `departed_member` | Membership | 1 |
| 16 | `date_ambiguous` | Logic | 1 |
| | `conflicting_split` | Logic | 1 |
