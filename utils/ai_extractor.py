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


EXCEL_SYSTEM_PROMPT = """You are an expert at extracting structured hotel and tourism service data from Excel price lists for a UAE destination management company.
Return ONLY valid JSON, no explanation."""

EXCEL_EXTRACTION_PROMPT = """Extract hotels and services from the following Excel spreadsheet data.

The spreadsheet is usually a price list for ONE specific hotel. Columns are typically:
  Service | Qty | Frequency | Price per unit | Total | Comments

STEP 1 — Find the hotel name and website:
- Look in header rows (top of sheet) for a hotel name field like "Hotel Name:", or a prominent hotel name cell
- Look for "Hotel website:", "Website:", or any cell containing "http" / "www" near the hotel name
- If no hotel name is found, use "Unknown Hotel"
- If no website is found, use empty string ""

STEP 2 — Room rates → extract as a HOTEL (not a service):
- "Room Single" / "ROH Single Room" / "Single Room" → hotel.rate_single_aed = Price per unit
- "Room Double/Twin" / "ROH Double" / "Twin Room" / "Double Room" → hotel.rate_twin_aed = Price per unit
- Return one hotel object with both rates filled in

STEP 3 — Everything else → SERVICES:
- Hotel meal supplements ("Half Board Supplement", "Full Board", "Breakfast") → category "Dining & Catering", APPEND " - [hotel name]" to the name
- Transfers/buses → "Transfers & Transport"
- Tours, excursions, safaris → "Activities & Excursions"
- Gala dinners, teambuilding → "Events & Entertainment"
- Management fees, booking fees → "Additional Services"
- Skip rows that are totals, grand totals, dates, or blank section headers

CRITICAL PRICE RULE — read carefully:
- The "Total" / "Grand Total" column is ALWAYS 0 in a template (formula with qty=0) — IGNORE IT
- Use ONLY the "Price per unit" column (4th or 5th column typically)
- Extract the number from cells like "USD 150", "150 USD", "150/pax" → 150
- Only set price to 0 if there is truly no unit price anywhere on that row

Return ONLY valid JSON:
{{
  "hotels": [
    {{
      "name": "JA Lake View Hotel",
      "location": "Dubai",
      "stars": 5,
      "description": "",
      "website_url": "https://www.jaresortshotels.com",
      "rate_single_aed": 254,
      "rate_twin_aed": 282
    }}
  ],
  "services": [
    {{
      "name": "Half Board Supplement - JA Lake View Hotel",
      "category": "Dining & Catering",
      "description": "",
      "price_aed": 50,
      "unit": "per person"
    }}
  ]
}}

Allowed categories: "Accommodation", "Transfers & Transport", "Activities & Excursions", "Dining & Catering", "Events & Entertainment", "Additional Services"
Allowed units: "per person", "per room", "per event", "per day", "per group", "fixed"

Spreadsheet data:
{{text}}"""


def extract_services_from_excel_text(text: str) -> dict:
    api_key = os.getenv('ANTHROPIC_API_KEY', '')
    if not api_key or api_key == 'your-api-key-here':
        return {"error": "ANTHROPIC_API_KEY not configured", "hotels": [], "services": []}

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
