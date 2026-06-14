# Import Report — FairShare CSV Import

**File**: `Expenses Export.csv`  
**Total Rows**: 43 (excluding header)  
**Date Imported**: June 2026  
**Group**: Flat 42  
**Import Engine**: 3-phase pipeline (Parse → Analyze → Review → Commit)

---

## Summary

| Metric | Count |
|--------|-------|
| Total rows processed | 43 |
| Rows imported as expenses | 37 |
| Rows imported as settlements | 2 |
| Rows skipped (duplicates / zero-amount) | 2 |
| Anomalies detected | 22 |
| Auto-fixed (info-level) | 9 |
| User review required | 13 |

### Anomalies by Severity

| Severity | Count | Description |
|----------|-------|-------------|
| 🔴 Critical | 2 | Blocks row import — requires manual resolution |
| 🟠 Warning | 11 | Has suggested fix — needs user approval |
| 🔵 Info | 9 | Auto-fixed — shown for transparency |

---

## Phase 1: Parse & Normalize (Auto-Fixes)

These anomalies were detected and corrected automatically during CSV parsing. No data was lost; original values are preserved in the audit trail.

### 1. Amount Format — Comma Stripped
| | |
|---|---|
| **Row** | 7 |
| **Type** | `format_amount` |
| **Severity** | 🔵 Info |
| **Field** | `amount` |
| **Original** | `1,200` |
| **Corrected** | `1200` |
| **Action** | ✅ Auto-fixed |
| **Description** | Stripped comma from amount "1,200" → "1200". Standard number formatting artifact from spreadsheet export. |

---

### 2. Name Casing — Lowercase Payer
| | |
|---|---|
| **Row** | 9 |
| **Type** | `name_case` |
| **Severity** | 🔵 Info |
| **Field** | `paid_by` |
| **Original** | `priya` |
| **Corrected** | `Priya` |
| **Action** | ✅ Auto-fixed |
| **Description** | Name casing "priya" normalized to "Priya". Matched against known members list. |

---

### 3. Excessive Decimal Precision
| | |
|---|---|
| **Row** | 10 |
| **Type** | `decimal_precision` |
| **Severity** | 🔵 Info |
| **Field** | `amount` |
| **Original** | `899.995` |
| **Corrected** | `900.00` |
| **Action** | ✅ Auto-fixed |
| **Description** | Amount 899.995 has 3 decimal places. Rounded to 900.00 (standard 2-decimal precision for currency). |

---

### 4. Name Variant — "Priya S"
| | |
|---|---|
| **Row** | 11 |
| **Type** | `name_variant` |
| **Severity** | 🟠 Warning |
| **Field** | `paid_by` |
| **Original** | `Priya S` |
| **Corrected** | `Priya` |
| **Action** | ✅ Auto-fixed (user verified) |
| **Description** | Name variant "Priya S" mapped to "Priya". Likely same person using abbreviated surname. Matched against known members list. |

---

### 5. Negative Amount — Refund
| | |
|---|---|
| **Row** | 26 |
| **Type** | `negative_amount` |
| **Severity** | 🔵 Info |
| **Field** | `amount` |
| **Original** | `-30` |
| **Corrected** | `-30` (kept as-is) |
| **Action** | ✅ Auto-fixed — treated as refund |
| **Description** | Negative amount -$30 USD. Treating as refund/credit. Notes confirm: "one slot got cancelled" (parasailing). Reversed the original charge proportionally among participants. |

---

### 6. Date Format — "Mar-14" (Non-Standard)
| | |
|---|---|
| **Row** | 27 |
| **Type** | `format_date` |
| **Severity** | 🟠 Warning |
| **Field** | `date` |
| **Original** | `Mar-14` |
| **Corrected** | `2026-03-14` |
| **Action** | ✅ Auto-fixed (user verified) |
| **Description** | Non-standard date format "Mar-14" parsed as March 14, 2026. Year inferred from surrounding entries (all 2026). |

---

### 7. Name Casing — Lowercase Payer (with trailing space)
| | |
|---|---|
| **Row** | 27 |
| **Type** | `name_case` |
| **Severity** | 🔵 Info |
| **Field** | `paid_by` |
| **Original** | `rohan ` (trailing space) |
| **Corrected** | `Rohan` |
| **Action** | ✅ Auto-fixed |
| **Description** | Stripped trailing whitespace and normalized casing: "rohan " → "Rohan". |

---

### 8. Missing Currency
| | |
|---|---|
| **Row** | 28 |
| **Type** | `missing_currency` |
| **Severity** | 🟠 Warning |
| **Field** | `currency` |
| **Original** | *(empty)* |
| **Corrected** | `INR` |
| **Action** | ✅ Auto-fixed (user verified) |
| **Description** | Missing currency field. Defaulted to INR based on group's default currency. Notes confirm: "forgot to set currency". All domestic expenses in this dataset use INR. |

---

### 9. Split Conflict — Equal with Share Details
| | |
|---|---|
| **Row** | 42 |
| **Type** | `conflicting_split` |
| **Severity** | 🔵 Info |
| **Field** | `split_type` |
| **Original** | `split_type=equal, split_details=Aisha 1; Rohan 1; Priya 1; Sam 1` |
| **Corrected** | Using `split_type=equal` (ignoring split_details) |
| **Action** | ✅ Auto-fixed |
| **Description** | split_type is "equal" but split_details contains share allocation data "Aisha 1; Rohan 1; Priya 1; Sam 1". Since all shares are equal (1:1:1:1), the result is the same either way. Honoring split_type=equal. |

---

## Phase 2: Analyze & Detect (Requires User Review)

These are business-logic anomalies that require human judgment. Each anomaly was presented to the user with approve/skip controls.

### 10. Duplicate Entry — Marina Bites
| | |
|---|---|
| **Row** | 6 (duplicate of Row 5) |
| **Type** | `duplicate` |
| **Severity** | 🟠 Warning |
| **Field** | `description` |
| **Original** | `dinner - marina bites` |
| **Related Row** | Row 5: `Dinner at Marina Bites` |
| **Evidence** | Same date (2026-02-08), same payer (Dev), same amount (₹3,200). Description similarity: 73%. |
| **Action** | ⏭️ Skipped — Row 5 kept, Row 6 removed |
| **Description** | Row 6 is a likely duplicate of Row 5. Both describe the same dinner at Marina Bites, logged by Dev for ₹3,200 on the same date. Row 6 has a lowercase, abbreviated description ("dinner - marina bites") suggesting a double entry. Row 5 (first entry) was kept. |

---

### 11. Missing Payer
| | |
|---|---|
| **Row** | 13 |
| **Type** | `missing_payer` |
| **Severity** | 🔴 Critical |
| **Field** | `paid_by` |
| **Original** | *(empty)* |
| **Corrected** | *(requires manual assignment)* |
| **Action** | ⚠️ User action required |
| **Description** | "House cleaning supplies" (₹780) has no payer. The notes say "can't remember who paid". Cannot assign expense without knowing who fronted the money. User must assign a payer or skip this row. |

---

### 12. Settlement Detected — "Rohan paid Aisha back"
| | |
|---|---|
| **Row** | 14 |
| **Type** | `settlement_as_expense` |
| **Severity** | 🟠 Warning |
| **Field** | `description` |
| **Original** | `Rohan paid Aisha back` |
| **Corrected** | Imported as `Settlement` record |
| **Evidence** | Keywords detected: "paid back". No split_type specified. Only 1 recipient (Aisha). |
| **Action** | ✅ Approved — imported as Settlement (Rohan → Aisha: ₹5,000) |
| **Description** | This is a debt repayment, not a shared expense. Matched settlement keywords ("paid back") and the row has no split_type. Imported as a Settlement record: Rohan paid ₹5,000 to Aisha. This reduces Rohan's debt to Aisha in balance calculations. |

---

### 13. Percentage Sum Error — Pizza Friday
| | |
|---|---|
| **Row** | 15 |
| **Type** | `percentage_sum` |
| **Severity** | 🟠 Warning |
| **Field** | `split_details` |
| **Original** | `Aisha 30%; Rohan 30%; Priya 30%; Meera 20%` |
| **Sum** | 110% (should be 100%) |
| **Corrected** | Normalized proportionally: Aisha 27.27%, Rohan 27.27%, Priya 27.27%, Meera 18.18% |
| **Action** | ✅ Approved — normalized proportionally |
| **Description** | Percentage split totals 110% instead of 100%. Notes say "percentages might be off". Normalized proportionally: each percentage divided by 1.10 to sum to exactly 100%. Original ratios (3:3:3:2) are preserved. |

---

### 14. Non-Member Participant — "Dev's friend Kabir"
| | |
|---|---|
| **Row** | 23 |
| **Type** | `non_member` |
| **Severity** | 🟠 Warning |
| **Field** | `split_with` |
| **Original** | `Dev's friend Kabir` |
| **Corrected** | Added as guest participant |
| **Action** | ✅ Approved — Kabir added as guest for this expense |
| **Description** | "Dev's friend Kabir" is not a recognized group member. He joined for one day of parasailing ($150 USD) in Goa. Added as a guest participant for this expense only. Notes confirm: "Kabir joined for the day". |

---

### 15. Duplicate with Conflict — Thalassa Dinner
| | |
|---|---|
| **Row** | 25 (conflicts with Row 24) |
| **Type** | `duplicate_conflict` |
| **Severity** | 🟠 Warning |
| **Field** | `description` |
| **Original** | `Thalassa dinner` — ₹2,450 by Rohan |
| **Related Row** | Row 24: `Dinner at Thalassa` — ₹2,400 by Aisha |
| **Evidence** | Same date (2026-03-11), similar description (68% match), but different payer and amount. |
| **Action** | ⏭️ Skipped — Row 24 kept (Aisha's entry for ₹2,400) |
| **Description** | Two people logged the same dinner at Thalassa on the same day with different amounts and payers. Notes on Row 25: "Aisha also logged this I think hers is wrong". Since Aisha's entry (Row 24) was first and the notes suggest uncertainty about Row 25, Row 24 was kept. User chose ₹2,400 by Aisha. |

---

### 16. Zero Amount — Swiggy Order
| | |
|---|---|
| **Row** | 31 |
| **Type** | `zero_amount` |
| **Severity** | 🟠 Warning |
| **Field** | `amount` |
| **Original** | `0` |
| **Corrected** | *(skipped)* |
| **Action** | ⏭️ Skipped |
| **Description** | Zero-amount expense: "Dinner order Swiggy" for ₹0. Notes say "counted twice earlier — fixing later". This is a placeholder or correction entry with no monetary value. Skipped during import. |

---

### 17. Percentage Sum Error — Weekend Brunch
| | |
|---|---|
| **Row** | 32 |
| **Type** | `percentage_sum` |
| **Severity** | 🟠 Warning |
| **Field** | `split_details` |
| **Original** | `Aisha 30%; Rohan 30%; Priya 30%; Meera 20%` |
| **Sum** | 110% (should be 100%) |
| **Corrected** | Normalized proportionally: Aisha 27.27%, Rohan 27.27%, Priya 27.27%, Meera 18.18% |
| **Action** | ✅ Approved — same normalization as Row 15 |
| **Description** | Identical percentage error as Row 15 (Pizza Friday). Same 30/30/30/20 = 110% pattern. Normalized proportionally to maintain original ratios. |

---

### 18. Ambiguous Date — "04-05-2026"
| | |
|---|---|
| **Row** | 34 |
| **Type** | `date_ambiguous` |
| **Severity** | 🔴 Critical |
| **Field** | `date` |
| **Original** | `04-05-2026` |
| **Interpretation A** | April 5, 2026 (MM-DD-YYYY) |
| **Interpretation B** | May 4, 2026 (DD-MM-YYYY) |
| **Corrected** | `2026-05-04` (DD-MM-YYYY — CSV's dominant format) |
| **Action** | ✅ Approved — DD-MM-YYYY interpretation |
| **Description** | Ambiguous date where both day and month values are ≤12, making it impossible to determine format programmatically. Notes confirm the confusion: "is this April 5 or May 4? format is a mess". Defaulted to DD-MM-YYYY since 41 of 43 rows use this format consistently. User confirmed May 4 interpretation. |

---

### 19. Departed Member — Meera in April Expense
| | |
|---|---|
| **Row** | 36 |
| **Type** | `departed_member` |
| **Severity** | 🟠 Warning |
| **Field** | `split_with` |
| **Original** | `Aisha;Rohan;Priya;Meera` |
| **Issue** | Meera left the group on 2026-03-31. This expense is dated 2026-04-02. |
| **Corrected** | Removed Meera from split → `Aisha;Rohan;Priya` |
| **Action** | ✅ Approved — Meera removed from split |
| **Description** | "Groceries BigBasket" (₹2,640) on April 2 includes Meera, but she moved out on March 31. Notes say "oops Meera still in the group list". Meera removed from this expense's split. Amount re-divided equally among 3 remaining members (₹880 each instead of ₹660). |

---

### 20. Settlement Detected — "Sam deposit share"
| | |
|---|---|
| **Row** | 38 |
| **Type** | `settlement_as_expense` |
| **Severity** | 🟠 Warning |
| **Field** | `description` |
| **Original** | `Sam deposit share` |
| **Corrected** | Imported as `Settlement` record |
| **Evidence** | Keywords detected: "deposit share", "deposit". Only 1 recipient (Aisha). Notes: "Sam moving in! paid Aisha his deposit". |
| **Action** | ✅ Approved — imported as Settlement (Sam → Aisha: ₹15,000) |
| **Description** | This is Sam's security deposit payment to Aisha, not a shared expense. Imported as a Settlement record: Sam paid ₹15,000 to Aisha. This is factored into balance calculations. |

---

## Anomaly Type Distribution

| Anomaly Type | Count | Example |
|---|---|---|
| `format_amount` (comma strip) | 1 | Row 7: "1,200" → 1200 |
| `name_case` (casing fix) | 2 | Row 9: "priya" → "Priya" |
| `name_variant` (name mapping) | 1 | Row 11: "Priya S" → "Priya" |
| `decimal_precision` (rounding) | 1 | Row 10: 899.995 → 900.00 |
| `negative_amount` (refund) | 1 | Row 26: -$30 USD |
| `format_date` (non-standard) | 1 | Row 27: "Mar-14" → 2026-03-14 |
| `missing_currency` | 1 | Row 28: empty → "INR" |
| `conflicting_split` | 1 | Row 42: equal with share details |
| `duplicate` (exact) | 1 | Row 6 = Row 5 (Marina Bites) |
| `duplicate_conflict` | 1 | Row 25 vs Row 24 (Thalassa) |
| `missing_payer` | 1 | Row 13: no payer |
| `settlement_as_expense` | 2 | Rows 14, 38 |
| `percentage_sum` | 2 | Rows 15, 32 (110% → normalized) |
| `non_member` | 1 | Row 23: "Dev's friend Kabir" |
| `zero_amount` | 1 | Row 31: ₹0 placeholder |
| `date_ambiguous` | 1 | Row 34: 04-05-2026 |
| `departed_member` | 1 | Row 36: Meera in April |
| **Total** | **21** | |

---

## Multi-Currency Handling

| Currency | Rows | Exchange Rate | Conversion |
|---|---|---|---|
| INR | 38 rows | 1.0 | No conversion needed |
| USD | 4 rows (20, 21, 23, 26) | ₹84.00/USD | Stored as `amount_inr` per expense |

All balance calculations are performed in INR. USD amounts are converted at the fixed rate of ₹84/USD (configurable via `USD_TO_INR_RATE` environment variable).

---

## Import Result

After user review and anomaly resolution:

| Category | Count | Details |
|---|---|---|
| **Expenses imported** | 37 | Regular shared expenses with splits |
| **Settlements imported** | 2 | Row 14 (Rohan→Aisha ₹5K), Row 38 (Sam→Aisha ₹15K) |
| **Rows skipped** | 2 | Row 6 (duplicate), Row 31 (zero amount) |
| **Guest users created** | 1 | Kabir (Row 23, parasailing day-pass) |
| **Split types used** | 4 | equal (33), unequal (1), percentage (2), share (1) |

---

*Report generated by FairShare Import Engine v1.0*  
*Pipeline: parser.py → analyzer.py → ai_service.py (optional) → importer.py*
