# INSIDERS Dubai — Commercial Proposal Generator

Web application for INSIDERS Tourism Dubai. Managers create tailored event proposals for corporate and leisure groups visiting the UAE. AI assists at every step — from brief extraction to day-by-day program planning.

**Live app:** https://uae-offer-generator-production.up.railway.app

---

## Features

### Admin Panel
- **Hotels** — add hotels with photos, room rates, website links, star rating
- **Services** — manage catalog: activities, transfers, dining, events, extras
- **Categories** — organize services into categories
- **Currencies** — USD, EUR, AED, GBP with custom rates; one-click refresh from European Central Bank (ECB)
- **AI Import** — upload PPTX, PDF, or Excel price lists; AI extracts hotels and services automatically. Duplicates are highlighted with a warning badge — admin decides to update or skip.

### Proposal Workflow
1. **Brief** — fill client details (company, group type, industry, dates, pax, currency, special requests)
2. **Parse Brief** — paste a client email or document; AI fills the form automatically
3. **Select Hotels & Services** — choose from catalog
4. **AI Program** — Claude generates a day-by-day itinerary based on the brief and selected services
5. **Edit Program** — manager adjusts the program; AI can apply text-based changes ("add yacht on day 2")
6. **Export Excel** — multi-sheet budget (one sheet per hotel), day-by-day service breakdown with dates and timing
7. **Export PPT** — branded presentation with hotel and service details

### Data Persistence
- Production uses **PostgreSQL** on Railway — data never lost on redeploy
- Local development uses SQLite

---

## Technology Stack

| Layer | Tech |
|---|---|
| Backend | Flask 3.1 + SQLAlchemy |
| Database | PostgreSQL (production) / SQLite (local) |
| AI | Claude API — `claude-sonnet-4-6` |
| Excel | openpyxl |
| PowerPoint | python-pptx |
| PDF | pypdf |
| Deployment | Railway + Docker |

---

## Local Development

### Requirements
- Python 3.11+
- Anthropic API key

### Setup

```bash
# Clone
git clone https://github.com/o6594340-sys/UAE-offer-generator.git
cd UAE-offer-generator

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY
```

### .env file

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=sk-ant-...
```

### Run

```bash
python app.py
```

Open: http://localhost:5000/admin

---

## First Setup (after launch)

1. `/admin` → **Currencies** → click **Initialize Currencies**
2. `/admin` → **Currencies** → click **Refresh Real Rates** (pulls live ECB rates)
3. `/admin` → **Import** → upload hotel/service PPTX or Excel files
4. Review extracted items, uncheck duplicates if needed, click **Save Selected**
5. Start creating proposals at `/brief`

---

## Railway Deployment

1. Push to GitHub (`master` branch)
2. Create project on [railway.app](https://railway.app)
3. Connect GitHub repository → select `master` branch
4. Add **PostgreSQL** addon (New → Database → PostgreSQL)
5. In your service **Variables**, click "Add Variable" to link `DATABASE_URL` from Postgres
6. Add variables:
   - `ANTHROPIC_API_KEY` — your Claude API key
   - `SECRET_KEY` — any random string
7. Deploy

Railway auto-deploys on every push to `master`.

---

## AI Import — Supported File Types

| Type | What AI extracts |
|---|---|
| `.pptx` / `.ppt` | Hotels, activities, restaurants, transfers, events |
| `.pdf` | Same as PPTX (text-based PDFs) |
| `.xlsx` / `.xls` | Hotel name, room rates, services with unit prices |

**Duplicate handling:** if a hotel or service with the same name already exists, the card is marked with ⚠️. Keep checked → updates price/description. Uncheck → skips.

---

## Excel Export Structure

Each hotel gets its own sheet with:
- Header: proposal details, client name, dates
- **Day-by-day breakdown** with date (e.g. `Day 1  |  12.05.2026  — Arrival Day`)
- Services listed in program order with timing
- Per-hotel totals and grand total
- All amounts in selected currency

---

## Currency Logic

- Prices are stored in **USD**
- Custom rates (set by admin) are used for all calculations
- Real rates (from ECB via frankfurter.app) are shown for reference
- Admin can refresh real rates at any time with one click

---

## Support

For issues: contact the development team or open a GitHub issue.

© 2026 INSIDERS Tourism Dubai. All rights reserved.
