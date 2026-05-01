import json
import os
import anthropic


BRIEF_SYSTEM_PROMPT = """You are an expert assistant for a UAE destination management company (DMC).
You extract client brief information from documents or emails to prefill a proposal form.
Return ONLY valid JSON, no explanation."""

BRIEF_EXTRACTION_PROMPT = """Extract the client brief details from the text below.

Return ONLY valid JSON in this exact format:
{
  "company_name": "Company or client name",
  "group_type": "Meeting",
  "industry": "Industry or sector",
  "pax": 0,
  "arrival_date": "YYYY-MM-DD",
  "departure_date": "YYYY-MM-DD",
  "currency": "USD",
  "special_requests": "Any special requirements, notes, preferences"
}

Rules:
- group_type must be one of: "Meeting", "Incentive", "Conference", "Exhibition", "Team Building", "Leisure", "Wedding", "Other"
- currency must be one of: "USD", "EUR", "AED", "GBP"
- pax is the number of people (integer). If not mentioned use 0
- If dates are not mentioned, use empty string ""
- If a field is not mentioned, use empty string "" or 0 for numbers
- special_requests: combine ALL notes, wishes, dietary requirements, room preferences, etc.

Brief text:
{text}"""


def extract_from_brief_text(text: str) -> dict:
    api_key = os.getenv('ANTHROPIC_API_KEY', '')
    if not api_key or api_key == 'your-api-key-here':
        return {"error": "ANTHROPIC_API_KEY not configured"}

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=BRIEF_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": BRIEF_EXTRACTION_PROMPT.format(text=text)
        }]
    )

    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    start = response_text.find('{')
    end = response_text.rfind('}') + 1
    if start >= 0 and end > start:
        try:
            return json.loads(response_text[start:end])
        except json.JSONDecodeError:
            pass

    return {"error": "Could not parse AI response"}

SYSTEM_PROMPT = """You are an expert at extracting structured tourism product data from PowerPoint presentations for a UAE destination management company.

You will receive text extracted slide-by-slide from one or more presentations. Your job is to identify all hotels, restaurants, activities, transfers, and events mentioned and return them in a strict JSON format.

Rules:
- Extract EVERY distinct hotel, restaurant, activity, transfer, or event you find
- One PPT may contain multiple hotels or services — find them all
- If a price is not mentioned, use 0
- If hotel star rating is not mentioned, use 5
- If location is unclear, use "Dubai"
- For services, pick the best matching category from the allowed list
- Return ONLY the JSON object, no explanation or markdown"""

EXTRACTION_PROMPT = """Extract all hotels and services from the following presentation text.

Return ONLY valid JSON in this exact format:
{
  "hotels": [
    {
      "name": "Hotel name",
      "location": "City name",
      "stars": 5,
      "description": "What makes this hotel special, amenities, highlights",
      "rate_single_aed": 0,
      "rate_twin_aed": 0
    }
  ],
  "services": [
    {
      "name": "Service name",
      "category": "Activities & Excursions",
      "description": "Full description of what is included",
      "price_aed": 0,
      "unit": "per person"
    }
  ]
}

Allowed categories: "Accommodation", "Transfers & Transport", "Activities & Excursions", "Dining & Catering", "Events & Entertainment", "Additional Services"
Allowed units: "per person", "per room", "per event", "per day", "per group", "fixed"

Restaurants and dining venues → category "Dining & Catering"
Desert safaris, city tours, cruises → category "Activities & Excursions"
Airport transfers, bus, limo → category "Transfers & Transport"
Gala dinners, teambuilding → category "Events & Entertainment"

Presentation text:
{text}"""


EXCEL_SYSTEM_PROMPT = """You are an expert at extracting structured tourism service data from Excel price lists for a UAE destination management company.
Return ONLY valid JSON, no explanation."""

EXCEL_EXTRACTION_PROMPT = """Extract all services and prices from the following Excel spreadsheet data.

Return ONLY valid JSON in this exact format:
{{
  "services": [
    {{
      "name": "Service name",
      "category": "Activities & Excursions",
      "description": "Description if available, else empty string",
      "price_aed": 0,
      "unit": "per person"
    }}
  ]
}}

Allowed categories: "Accommodation", "Transfers & Transport", "Activities & Excursions", "Dining & Catering", "Events & Entertainment", "Additional Services"
Allowed units: "per person", "per room", "per event", "per day", "per group", "fixed"

Rules:
- Extract EVERY distinct service/activity/transfer that has a name
- price_aed field stores the price value (use whatever numeric price you find in the spreadsheet)
- If price is missing, use 0
- If unit is not specified, guess from context or use "per person"
- Pick the best matching category based on service type
- Restaurants/dining → "Dining & Catering", transfers/buses → "Transfers & Transport", tours/excursions → "Activities & Excursions", galas/teambuilding → "Events & Entertainment"

Spreadsheet data:
{{text}}"""


def extract_services_from_excel_text(text: str) -> dict:
    api_key = os.getenv('ANTHROPIC_API_KEY', '')
    if not api_key or api_key == 'your-api-key-here':
        return {"error": "ANTHROPIC_API_KEY not configured", "services": []}

    client = anthropic.Anthropic(api_key=api_key)

    prompt = EXCEL_EXTRACTION_PROMPT.replace('{{text}}', text).replace('{{', '{').replace('}}', '}')

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        system=EXCEL_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    start = response_text.find('{')
    end = response_text.rfind('}') + 1
    if start >= 0 and end > start:
        try:
            return json.loads(response_text[start:end])
        except json.JSONDecodeError:
            pass

    return {"error": "Could not parse AI response", "services": []}


def extract_from_pptx_text(text: str) -> dict:
    api_key = os.getenv('ANTHROPIC_API_KEY', '')
    if not api_key or api_key == 'your-api-key-here':
        return {"error": "ANTHROPIC_API_KEY not configured", "hotels": [], "services": []}

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": EXTRACTION_PROMPT.format(text=text)
        }]
    )

    response_text = message.content[0].text.strip()

    # Strip markdown code fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    start = response_text.find('{')
    end = response_text.rfind('}') + 1
    if start >= 0 and end > start:
        try:
            return json.loads(response_text[start:end])
        except json.JSONDecodeError:
            pass

    return {"error": "Could not parse AI response", "hotels": [], "services": []}
