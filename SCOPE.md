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
