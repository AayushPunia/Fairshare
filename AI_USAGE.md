# AI Usage Documentation

## Overview

FairShare uses AI (Google Gemini API) as an **optional enhancement layer**. The core application works identically without AI. All AI features follow a strict principle:

> **AI enhances but never blocks.** No import decision, balance calculation, or data operation depends on AI output.

## AI Tools Used

| Tool | Where Used | Purpose |
|------|-----------|---------|
| **Google Gemini 2.0 Flash** | `importer/ai_service.py` | Anomaly description enhancement + expense categorization |
| **Gemini (via Antigravity IDE)** | Development workflow | Code generation, debugging, architecture decisions |

## Where AI Is Used in the App

### 1. Anomaly Description Enhancement (`ai_service.py`)

**What**: After the deterministic anomaly detector finds issues in the CSV, each anomaly is sent to Gemini for a friendlier, more contextual explanation.

**Example**:
- Deterministic: `"Row 6: Likely duplicate of row 5. Both are 'Dinner at Marina Bites' / 'dinner - marina bites', same date (2026-02-08), same payer (Dev), same amount (3200)."`
- AI-enhanced: `"It looks like Dev's dinner at Marina Bites was logged twice on Feb 8. The second entry (row 6) has a slightly different description but the same amount and date. You probably want to keep just one — we suggest keeping row 5 (the first entry)."`

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

---

## Key Prompts Used

### Prompt 1: Anomaly Description Enhancement
```
You are a helpful assistant for a shared flat expenses app.
A CSV import detected this data anomaly:
- Type: {anomaly_type}
- Field: {field}
- Original value: {original_value}
- Corrected value: {corrected_value}
- Context: {description}

Explain this anomaly in plain English for a non-technical user.
Keep it to 2-3 sentences. Be specific about what's wrong and what the suggested fix does.
```

### Prompt 2: Expense Categorization
```
Categorize this shared flat expense into exactly one of these categories:
Rent, Utilities, Groceries, Dining, Travel, Entertainment, Household, Transport, Other

Expense description: "{description}"

Reply with only the category name, nothing else.
```

### Prompt 3: Batch Anomaly Enhancement
```
You are a data quality assistant. For each of these anomalies detected in a shared
expense CSV, provide a user-friendly explanation. Be concise (2-3 sentences each).

Anomalies:
{json_anomaly_list}
```

---

## Three Cases Where AI Got It Wrong

### Case 1: AI Miscategorized "Cylinder Refill" as Transport

**What happened**: Gemini categorized "Cylinder refill" (Row 10, ₹900 — a cooking gas cylinder) as "Transport" instead of "Household" or "Utilities". It likely associated "cylinder" with vehicle/engine cylinders.

**How I caught it**: Manual review of categorization output during testing. Gas cylinder refills are clearly a household utility in the Indian context.

**What I changed**: Added "cylinder" to the `Household` keyword list in the deterministic categorizer so it never reaches the AI fallback:
```python
'Household': ['cleaning', 'maid', 'cylinder', 'refill', 'supplies', ...],
```
**Lesson**: Keyword-first approach is essential — AI lacks regional/cultural context for common Indian household terms.

---

### Case 2: AI Marked Goa Trip Expenses as "Possible Duplicates"

**What happened**: When enhancing anomaly descriptions, Gemini's response for the Thalassa dinner conflict (Rows 24-25) suggested "both entries should be kept since they're from different people" — implying it wasn't a duplicate. But it actually *was* a duplicate logged by two different people for the same dinner.

**How I caught it**: The deterministic analyzer correctly flagged it as `duplicate_conflict` (same date, similar description, different payers/amounts). During user testing, I noticed the AI description contradicted the system's detection, which would confuse users.

**What I changed**: Added a guard in the prompt to clarify: `"Note: Two entries on the same date with similar descriptions but different payers may be the same expense logged by two people — this IS a conflict that needs resolution."` Also ensured the deterministic `description` is always shown alongside `ai_description`, so users see both perspectives.

---

### Case 3: AI Generated HTML Tags in Description Output

**What happened**: In some cases, Gemini returned descriptions with markdown formatting (`**bold**`, `*italic*`) and even HTML tags (`<br>`, `<strong>`). When rendered in the React UI, this caused broken formatting and XSS-adjacent display issues.

**How I caught it**: Visual testing of the import review page. Some anomaly cards showed raw markdown syntax instead of clean text.

**What I changed**: Added a sanitization step in `enhance_anomaly_description()` that strips all markdown/HTML formatting from AI responses before storing:
```python
# Strip markdown/HTML from AI response
import re
cleaned = re.sub(r'[*_`#]', '', ai_response)
cleaned = re.sub(r'<[^>]+>', '', cleaned)
```
Also set the React component to use `textContent` instead of `dangerouslySetInnerHTML` — AI output is always treated as plain text, never raw HTML.

---

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
    │  ├── categorize_expense() for imported expenses
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
