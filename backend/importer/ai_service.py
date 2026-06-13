"""
AI Service — Gemini integration for smart anomaly descriptions.

Uses Google's Gemini API to generate human-friendly explanations of
data anomalies and auto-categorize expenses.

Design principle: AI enhances but never blocks.
- If Gemini API fails, we fall back to the deterministic descriptions
- AI output is stored in ai_description field, separate from core description
- No import decisions depend on AI output
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import google.generativeai, gracefully degrade if not available
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning('google-generativeai not installed. AI features disabled.')


def _get_model():
    """Initialize and return Gemini model."""
    if not GENAI_AVAILABLE or not settings.GEMINI_API_KEY:
        return None
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel('gemini-2.0-flash')


def enhance_anomaly_description(anomaly_data):
    """
    Use Gemini to generate a friendly, detailed explanation of an anomaly.

    Args:
        anomaly_data: dict with keys: type, row, original, corrected, details, notes

    Returns:
        Enhanced description string, or None if AI unavailable.
    """
    model = _get_model()
    if not model:
        return None

    try:
        prompt = f"""You are a helpful assistant for a shared flat expenses app.
A CSV import detected this data anomaly. Explain it in plain English for a non-technical user.
Keep it to 2-3 sentences. Be specific. Suggest what the user should do.

Anomaly type: {anomaly_data.get('type', 'unknown')}
Row number: {anomaly_data.get('row', '?')}
Field: {anomaly_data.get('field', '?')}
Original value: {anomaly_data.get('original', '')}
Corrected value: {anomaly_data.get('corrected', '')}
Row notes: {anomaly_data.get('notes', '')}
Context: {anomaly_data.get('context', '')}

Response (2-3 sentences, no markdown):"""

        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f'Gemini API error: {e}')
        return None


def categorize_expense(description):
    """
    Auto-categorize an expense based on its description.

    Uses keyword matching first (fast, reliable), then falls back to AI.
    Categories: Rent, Groceries, Utilities, Dining, Travel, Entertainment,
    Household, Personal, Other.
    """
    desc_lower = description.lower()

    # Keyword-based categorization (reliable, fast, no API call)
    CATEGORIES = {
        'Rent': ['rent'],
        'Groceries': ['groceries', 'bigbasket', 'dmart', 'd-mart', 'grocer'],
        'Utilities': ['wifi', 'electricity', 'water', 'gas', 'cylinder', 'bill'],
        'Dining': ['dinner', 'lunch', 'breakfast', 'pizza', 'restaurant', 'swiggy',
                   'zomato', 'cafe', 'brunch', 'snacks', 'drinks', 'shack', 'thalassa'],
        'Travel': ['flight', 'cab', 'taxi', 'uber', 'ola', 'airport', 'scooter',
                   'rental', 'villa', 'booking', 'hotel'],
        'Entertainment': ['movie', 'parasailing', 'adventure', 'party', 'housewarming'],
        'Household': ['cleaning', 'maid', 'furniture', 'supplies', 'deep clean'],
        'Celebration': ['birthday', 'cake', 'farewell', 'celebration'],
    }

    for category, keywords in CATEGORIES.items():
        if any(kw in desc_lower for kw in keywords):
            return category

    # Fallback to AI if available
    model = _get_model()
    if model:
        try:
            prompt = f"""Categorize this shared flat expense into exactly one category.
Categories: Rent, Groceries, Utilities, Dining, Travel, Entertainment, Household, Celebration, Other.

Expense: "{description}"

Reply with just the category name, nothing else."""
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            pass

    return 'Other'


def enhance_all_anomalies(anomalies, rows):
    """
    Batch-enhance anomaly descriptions using AI.
    Called once after analysis, results cached in ImportAnomaly.ai_description.
    """
    model = _get_model()
    if not model:
        return anomalies  # Return unchanged if AI unavailable

    for anomaly in anomalies:
        # Find corresponding row for context
        row_data = next(
            (r for r in rows if r['row_number'] == anomaly['row_number']),
            {}
        )

        ai_desc = enhance_anomaly_description({
            'type': anomaly.get('anomaly_type', ''),
            'row': anomaly.get('row_number', ''),
            'field': anomaly.get('field', ''),
            'original': anomaly.get('original_value', ''),
            'corrected': anomaly.get('corrected_value', ''),
            'notes': row_data.get('notes', ''),
            'context': row_data.get('description', ''),
        })

        if ai_desc:
            anomaly['ai_description'] = ai_desc

    return anomalies
