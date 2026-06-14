# AI Usage Documentation

## Overview

FairShare uses AI (Google Gemini API) as an **optional enhancement layer**. The core application works identically without AI. All AI features follow a strict principle:

> **AI enhances but never blocks.** No import decision, balance calculation, or data operation depends on AI output.

## Where AI Is Used

### 1. Anomaly Description Enhancement (`ai_service.py`)

**What**: After the deterministic anomaly detector finds issues in the CSV, each anomaly is sent to Gemini for a friendlier, more contextual explanation.

**Example**:
- Deterministic: `"Row 6: Likely duplicate of row 5. Both are 'Dinner at Marina Bites' / 'dinner - marina bites', same date (2026-02-08), same payer (Dev), same amount (3200)."`
- AI-enhanced: `"It looks like Dev's dinner at Marina Bites was logged twice on Feb 8. The second entry (row 6) has a slightly different description but the same amount and date. You probably want to keep just one — we suggest keeping row 5 (the first entry)."`

**Implementation**:
```python
# ai_service.py - enhance_anomaly_description()
prompt = f"""You are a helpful assistant for a shared flat expenses app.
A CSV import detected this data anomaly. Explain it in plain English 
for a non-technical user. Keep it to 2-3 sentences."""
```

**Fallback**: If Gemini fails, the deterministic description is used. The AI description is stored in a separate `ai_description` field on `ImportAnomaly`, never overwriting the core `description`.

### 2. Expense Categorization (`ai_service.py`)

**What**: Auto-categorize expenses by description (Rent, Groceries, Dining, Travel, etc.).

**Implementation**: Keyword-based categorization runs first (fast, reliable). AI is only called as a fallback for uncategorized expenses.

```python
# Keyword-based (always runs first)
CATEGORIES = {
    'Dining': ['dinner', 'lunch', 'pizza', 'swiggy', 'zomato', ...],
    'Travel': ['flight', 'cab', 'taxi', 'uber', 'villa', ...],
    ...
}

# AI fallback (only if keyword match fails)
if model:
    prompt = "Categorize this expense: '{description}'"
```

**Fallback**: Returns "Other" if both keyword matching and AI fail.

## AI Integration Architecture

```
CSV Upload
    │
    ▼
Phase 1: Parser (deterministic — no AI)
    │
    ▼
Phase 2: Analyzer (deterministic — no AI)
    │
    ▼
[Optional] AI Enhancement (Gemini)
    │  ├── enhance_anomaly_description() for each anomaly
    │  └── Wrapped in try/catch — silent failure
    │
    ▼
Store anomalies with both description + ai_description
    │
    ▼
Display: Show ai_description if available, else description
```

## Configuration

```bash
# Set Gemini API key (optional — app works without it)
export GEMINI_API_KEY="your-key-from-aistudio.google.com"
```

If `GEMINI_API_KEY` is not set:
- `_get_model()` returns `None`
- All AI functions return `None` / pass through unchanged
- No API calls are made
- No errors are thrown

## AI Code Locations

| File | Function | Purpose |
|------|----------|---------|
| `importer/ai_service.py` | `enhance_anomaly_description()` | AI-friendly anomaly explanation |
| `importer/ai_service.py` | `categorize_expense()` | Auto-categorize by description |
| `importer/ai_service.py` | `enhance_all_anomalies()` | Batch enhancement after analysis |
| `importer/views.py` | `ImportUploadView.post()` | Calls `enhance_all_anomalies()` |

## Responsible AI Practices

1. **Transparency**: AI descriptions are shown with a 🤖 prefix in the import report UI, clearly distinguishing them from deterministic output.
2. **No data persistence dependency**: AI output is stored in `ai_description`, separate from the core `description` field. Deleting all AI output would not affect app functionality.
3. **Minimal data sent**: Only the anomaly type, field, original/corrected values, and expense description are sent to Gemini. No user PII (names, emails, passwords) is included in prompts.
4. **Rate limiting**: Batch enhancement is called once per import session, not per-request.
