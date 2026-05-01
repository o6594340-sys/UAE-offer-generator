import json
import os
import anthropic


SUGGEST_SYSTEM_PROMPT = """You are a senior program planner at INSIDERS Tourism Dubai, a UAE destination management company.
You create tailored event programs for corporate and leisure groups visiting the UAE.
Return ONLY valid JSON, no explanation outside the JSON."""

SUGGEST_PROMPT = """Based on the client brief below, select the most suitable services from our catalog and create a recommended program.

CLIENT BRIEF:
- Group type: {group_type}
- Industry: {industry}
- Number of people: {pax}
- Duration: {nights} nights
- Special requests: {special_requests}

AVAILABLE SERVICES (format: [ID] Name | Category | Price | Unit):
{services_list}

IMPORTANT — Special requests are the HIGHEST PRIORITY:
- If special requests mention a specific service ("add yacht", "desert safari on day 2", "gala dinner on last evening") — that service MUST be included if available in the catalog
- If special requests mention timing ("day 1 — transfer, day 2 — city tour") — follow that structure exactly
- If special requests say "no X" or "without X" — exclude that type of service
- Only after satisfying all special requests, fill remaining days with sensible defaults

Default logic (apply only where special requests don't specify):
- Always include airport transfers if available (arrival + departure)
- For Incentive/Meeting groups: teambuilding, gala dinner, city tour
- For Leisure groups: excursions, dining, leisure activities
- For longer stays (3+ nights): include more variety across days
- Match the industry feel: Finance/Pharma = premium, Tech = active/modern
- Don't include Accommodation category (hotels are selected separately)
- Select 4-10 services total

Return ONLY valid JSON:
{{
  "program_summary": "2-3 sentences explaining the overall concept and why it suits this group.",
  "itinerary": [
    {{
      "day": 1,
      "label": "Arrival Day",
      "items": [
        {{"service_id": 1, "timing": "14:00", "note": "Airport pickup, coach to hotel"}},
        {{"service_id": 8, "timing": "19:00", "note": "Welcome dinner"}}
      ]
    }},
    {{
      "day": 2,
      "label": "City Exploration",
      "items": [
        {{"service_id": 5, "timing": "09:00", "note": ""}},
        {{"service_id": 12, "timing": "20:00", "note": "Gala dinner"}}
      ]
    }}
  ]
}}

Rules for itinerary:
- Create one entry per day (day 1 = arrival, last day = departure)
- Each item must reference a valid service_id from the catalog above
- timing is HH:MM format or empty string
- note is a short optional comment (1 sentence max)
- Respect special requests for specific days first, then fill rest logically"""


def suggest_program(group_type: str, industry: str, pax: int, nights: int,
                    special_requests: str, services: list) -> dict:
    api_key = os.getenv('ANTHROPIC_API_KEY', '')
    if not api_key or api_key == 'your-api-key-here':
        return {"error": "ANTHROPIC_API_KEY not configured"}

    services_list = '\n'.join(
        f"[{s['id']}] {s['name']} | {s['category']} | {s['price']} USD | {s['unit']}"
        for s in services
    )

    prompt = SUGGEST_PROMPT.format(
        group_type=group_type or 'Incentive',
        industry=industry or 'Not specified',
        pax=pax or 1,
        nights=nights or 3,
        special_requests=special_requests or 'None',
        services_list=services_list or 'No services available',
    ).replace('{{', '{').replace('}}', '}')

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SUGGEST_SYSTEM_PROMPT,
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

    return {"error": "Could not parse AI response"}


UPDATE_SYSTEM_PROMPT = """You are a senior program planner at INSIDERS Tourism Dubai.
You update existing event itineraries based on manager's change requests.
Return ONLY valid JSON, no explanation outside the JSON."""

UPDATE_PROMPT = """Here is the current program itinerary and a change request from the manager.
Apply the changes and return the updated itinerary.

CURRENT ITINERARY (JSON):
{current_itinerary}

AVAILABLE SERVICES (ID | Name | Category):
{services_list}

MANAGER'S CHANGE REQUEST:
"{change_request}"

Rules:
- Apply EXACTLY what the manager requested — this is top priority
- If they say "add X on day N" — add that service to that day
- If they say "remove X" or "replace X with Y" — do exactly that
- If they mention a service not in the catalog, add it with service_id: null and service_name equal to what they said
- Keep all other days and items unchanged
- Keep the same JSON structure

Return ONLY valid JSON:
{{
  "itinerary": [
    {{
      "day": 1,
      "label": "Day label",
      "items": [
        {{"service_id": 5, "service_name": "Service name", "timing": "09:00", "note": ""}}
      ]
    }}
  ]
}}"""


def update_itinerary(current: list, change_request: str, services: list) -> dict:
    api_key = os.getenv('ANTHROPIC_API_KEY', '')
    if not api_key or api_key == 'your-api-key-here':
        return {"error": "ANTHROPIC_API_KEY not configured"}

    services_list = '\n'.join(f"{s['id']} | {s['name']} | {s['category']}" for s in services)
    prompt = UPDATE_PROMPT.format(
        current_itinerary=json.dumps(current, ensure_ascii=False, indent=2),
        services_list=services_list,
        change_request=change_request,
    ).replace('{{', '{').replace('}}', '}')

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=UPDATE_SYSTEM_PROMPT,
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

    return {"error": "Could not parse AI response"}


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

    try:
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

        return {"error": "Could not parse AI response", "hotels": [], "services": []}
    except Exception as e:
        return {"error": f"AI extraction failed: {str(e)}", "hotels": [], "services": []}


def extract_from_pptx_text(text: str) -> dict:
    api_key = os.getenv('ANTHROPIC_API_KEY', '')
    if not api_key or api_key == 'your-api-key-here':
        return {"error": "ANTHROPIC_API_KEY not configured", "hotels": [], "services": []}

    try:
        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": EXTRACTION_PROMPT.replace('{text}', text)
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

        return {"error": "Could not parse AI response", "hotels": [], "services": []}
    except Exception as e:
        return {"error": f"AI extraction failed: {str(e)}", "hotels": [], "services": []}
