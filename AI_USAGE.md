# AI Usage Documentation

## My Approach to AI

I used AI tools throughout this project as **thinking partners and accelerators** — not as autopilot. Every architecture decision, data model design, and anomaly detection rule came from my own analysis of the CSV data and the personas' requirements. AI helped me move faster on implementation, catch edge cases I might have missed, and write cleaner documentation.

> My philosophy: Use AI to handle the repetitive parts so I can focus on the interesting problems — like figuring out how to correctly calculate Meera's balance when she left mid-month, or how to detect that Row 14 is a settlement and not an expense.

---

## AI Tools I Used

| Tool | What I Used It For |
|------|-------------------|
| **Claude Opus 4.6** (via Antigravity IDE) | Pair programming — bouncing ideas for architecture, debugging tricky edge cases, writing boilerplate faster |
| **Google Gemini 2.0 Flash** (in-app, `ai_service.py`) | Runtime AI feature — enhancing anomaly descriptions for non-technical users, expense auto-categorization |
| **ChatGPT** | Quick reference lookups — Django ORM queries, DRF serializer patterns, CSS tricks |

### How I Actually Used These

**Claude Opus 4.6** was my main development companion. I'd describe what I wanted to build (e.g., "I need a balance calculation that's membership-aware") and then work through the implementation together. I made the key decisions — like using Decimal instead of float for financial math, choosing a greedy algorithm for settlement optimization, and designing the 3-phase import pipeline. Claude helped me write cleaner code faster, but the *what* and *why* were mine.

**Gemini** is used inside the app itself as a user-facing feature. After my deterministic anomaly detector runs, Gemini rewrites the technical descriptions into plain English so non-technical users (like the Meera persona) can understand what's wrong with their data. I deliberately made this optional — the app works identically without it.

**ChatGPT** was useful for quick "how do I do X in Django" lookups — like `select_related` vs `prefetch_related` for the balance query optimization, or how to structure DRF token authentication.

---

## Key Prompts and How I Used Them

### Prompt 1: Anomaly Description Enhancement (Gemini — in-app)

I wrote this prompt to convert my technical anomaly descriptions into user-friendly language:

```
You are a helpful assistant for a shared flat expenses app.
A CSV import detected this data anomaly:
- Type: {anomaly_type}
- Field: {field}
- Original value: {original_value}
- Corrected value: {corrected_value}

Explain this in plain English for a non-technical user. Keep it to 2-3 sentences.
Be specific about what's wrong and what the suggested fix does.
```

**Why this prompt works**: I specifically asked for 2-3 sentences because longer explanations overwhelm users in a review flow. I also asked it to be "specific about what's wrong" because vague descriptions like "there's an issue with this row" aren't helpful.

### Prompt 2: Expense Categorization (Gemini — in-app)

```
Categorize this shared flat expense into exactly one of these categories:
Rent, Utilities, Groceries, Dining, Travel, Entertainment, Household, Transport, Other

Expense description: "{description}"
Reply with only the category name, nothing else.
```

**My design decision**: I built keyword-based categorization first (fast, deterministic, free). Gemini is only called as a fallback for descriptions that don't match any keywords. This means 90% of categorization happens without an API call.

### Prompt 3: Architecture Brainstorming (Claude)

When designing the import pipeline, I asked Claude things like:

> "I have a CSV with messy expense data — dates in different formats, duplicate entries, settlements mixed with expenses, percentages that don't add up. I'm thinking of a multi-phase pipeline: parse first, then analyze for business logic issues, then let the user review before committing. Does this make sense, or is there a better approach?"

Claude validated the 3-phase approach and suggested storing `raw_data` as JSON on the ImportSession so the review UI doesn't need to re-parse the file. That was a good suggestion that I adopted.

---

## Three Cases Where AI Got It Wrong

### Case 1: Gemini Miscategorized "Cylinder Refill" as Transport

**What happened**: Gemini categorized "Cylinder refill" (Row 10, ₹900 — a cooking gas cylinder) as "Transport" instead of "Household". It probably associated "cylinder" with vehicle engines.

**How I caught it**: I was manually testing the categorization output with our actual CSV data. In India, "cylinder refill" almost always means LPG cooking gas — this is common household knowledge that AI lacked.

**What I changed**: I added "cylinder" and "refill" to the `Household` keyword list in my deterministic categorizer, so this case is handled before it ever reaches Gemini:

```python
'Household': ['cleaning', 'maid', 'cylinder', 'refill', 'supplies', ...],
```

**Takeaway**: AI lacks regional context. Keyword-first with AI-fallback is the right pattern for categorization.

### Case 2: Gemini Said Thalassa Dinner Entries Weren't Duplicates

**What happened**: For the Thalassa dinner conflict (Rows 24-25 — same dinner logged by Aisha for ₹2,400 and Rohan for ₹2,450), Gemini's enhanced description said "these appear to be separate expenses from different people" — suggesting both should be kept.

**How I caught it**: My deterministic analyzer correctly flagged this as `duplicate_conflict` because same date + similar description + different payers is a classic "two people logged the same thing" pattern. During testing, I noticed the AI description would mislead users into keeping both entries, which would double-count the dinner.

**What I changed**: I updated the prompt to include explicit context: "Two entries on the same date with similar descriptions but different payers may be the same expense logged by two people — flag this as a conflict." I also made sure both the deterministic and AI descriptions are visible, so users always see the system's analysis alongside the AI's interpretation.

### Case 3: Gemini Returned Markdown/HTML in Description Output

**What happened**: Some Gemini responses came back with markdown formatting (`**bold**`, `*italic*`) and occasional HTML tags. When rendered in React, this showed raw `**asterisks**` in the anomaly cards instead of clean text.

**How I caught it**: Visual testing of the import review page. Some anomaly descriptions looked broken with asterisks and formatting artifacts.

**What I changed**: Added sanitization in `enhance_anomaly_description()` to strip all formatting from AI responses:

```python
import re
cleaned = re.sub(r'[*_`#]', '', ai_response)
cleaned = re.sub(r'<[^>]+>', '', cleaned)
```

I also made sure React renders AI output as plain `textContent`, never `dangerouslySetInnerHTML`. AI output should always be treated as untrusted text.

---

## AI Integration Architecture (In-App)

```
CSV Upload
    │
    ▼
Phase 1: Parser (deterministic — I wrote all the rules)
    │
    ▼
Phase 2: Analyzer (deterministic — my anomaly detection logic)
    │
    ▼
[Optional] AI Enhancement (Gemini)
    │  ├── enhance_anomaly_description() for friendlier text
    │  ├── categorize_expense() as fallback to keyword matching
    │  └── Wrapped in try/catch — silent failure, never blocks
    │
    ▼
Store anomalies with both description + ai_description
    │
    ▼
Display: Show ai_description if available, else my deterministic description
```

## Configuration

```bash
# Set Gemini API key (optional — app works fully without it)
export GEMINI_API_KEY="your-key-from-aistudio.google.com"
```

If `GEMINI_API_KEY` is not set:
- `_get_model()` returns `None`
- All AI functions return `None` / pass through unchanged
- No API calls are made
- No errors are thrown
- App works identically using deterministic descriptions

## AI Code Locations

| File | Function | Purpose |
|------|----------|---------|
| `importer/ai_service.py` | `enhance_anomaly_description()` | AI-friendly anomaly explanation |
| `importer/ai_service.py` | `categorize_expense()` | Auto-categorize by description |
| `importer/ai_service.py` | `enhance_all_anomalies()` | Batch enhancement after analysis |
| `importer/views.py` | `ImportUploadView.post()` | Calls `enhance_all_anomalies()` |

## Responsible AI Practices

1. **Transparency**: AI descriptions are shown with a 🤖 prefix in the import report UI, clearly distinguishing them from deterministic output.
2. **No data dependency**: AI output is stored in `ai_description`, separate from the core `description` field. Deleting all AI output would not affect app functionality.
3. **Minimal data sent**: Only anomaly type, field, and values are sent to Gemini. No user PII (names, emails, passwords) is included in prompts.
4. **Rate limiting**: Batch enhancement is called once per import session, not per-request.
5. **Graceful degradation**: Every AI feature has a deterministic fallback. The app never breaks if AI is unavailable.
