# INSIDERS Dubai - Commercial Proposal Generator

Professional web-based proposal generator for INSIDERS Tourism Dubai. Managers can create customized commercial proposals (PDF/Excel/PPT) with multi-currency support.

## Features

✅ **Admin Panel** - Manage hotels, services, and currencies
✅ **Hotel Management** - Add hotels with photos, descriptions, room rates (in AED)
✅ **Services Catalog** - Create service categories (activities, transfers, dining, events)
✅ **Multi-Currency** - USD, EUR, AED, GBP with custom exchange rates
✅ **Proposal Generation** - Create proposals with hybrid approach (Manager + Claude AI)
✅ **Excel Export** - Multi-sheet budgets (one sheet per hotel)
✅ **PPT Presentation** - Beautiful presentations with INSIDERS branding
✅ **English Interface** - All in English for international clients

## Quick Start

### Prerequisites
- Python 3.9+
- pip (Python package manager)

### Installation (Windows)

1. **Download and Extract** the project
2. **Double-click** `start.bat`
3. **Open browser** → `http://localhost:5000`
4. **Admin panel** → `http://localhost:5000/admin`

### Installation (Manual)

```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

## First Setup

1. Go to **Admin Dashboard** → `/admin`
2. Click **"Initialize Currencies"** to setup USD, EUR, AED, GBP
3. Add your hotels under **Hotels** section
4. Create service categories under **Categories**
5. Add services (excursions, transfers, dining, events)
6. Set custom exchange rates for each currency

## Project Structure

```
insiders-dubai-proposal-generator/
├── app.py                    # Main Flask application
├── config.py                 # Configuration & settings
├── models.py                 # Database models (SQLAlchemy)
│
├── admin/                    # Admin panel
│   ├── __init__.py          # Admin routes
│   └── templates/           # Admin HTML templates
│       ├── dashboard.html   # Admin home
│       ├── hotels.html      # Hotel list
│       ├── hotel_form.html  # Add/edit hotel
│       ├── services.html    # Service list
│       ├── service_form.html # Add/edit service
│       ├── currencies.html  # Currency rates
│       └── categories.html  # Service categories
│
├── proposal/                 # Proposal generator
│   ├── __init__.py          # Proposal routes
│   └── templates/           # Proposal templates
│
├── templates/
│   └── base.html            # Base template
│
├── uploads/                 # Photos & files
│   ├── hotels/
│   └── services/
│
└── instance/
    └── insiders.db          # SQLite database
```

## Admin Panel Usage

### 1. Add Hotel

- Name: Hotel name (e.g., "Atlantis The Palm")
- Location: City (Dubai, Abu Dhabi)
- Stars: 3-5
- Single room rate: Price per night in AED
- Twin room rate: Price per night in AED
- Photo: Upload hotel image (JPG, PNG)

### 2. Create Service Categories

Common categories:
- Accommodation
- Transfers & Transport
- Activities & Excursions
- Dining & Catering
- Events & Entertainment
- Additional Services

### 3. Add Services

- Name: Service name (e.g., "Desert Safari")
- Category: Select from dropdown
- Description: What the service includes
- Price (AED): Base price in AED
- Unit: per person, per room, per event, per day, per group, or fixed
- Photo: Upload service image

### 4. Manage Currencies

- **Real Rate**: Reference (informational only)
- **Custom Rate**: Rate used for calculations
- **Active**: Toggle to show/hide in proposals

Example:
```
USD: Custom Rate = 1.0 (base currency)
AED: Custom Rate = 3.67
EUR: Custom Rate = 0.93
GBP: Custom Rate = 0.81
```

> Prices are entered in USD by default. The system converts USD into AED, EUR, or GBP for proposal output.

## Workflow: Creating a Proposal

1. **Manager fills Brief Form**
   - Company name, dates, number of people
   - Select currency (USD/EUR/AED/GBP)
   - Select hotels
   - Select services
   - Add special requests

2. **System generates Program** (Day by day)
   - Shows selected services organized by day
   - Manager can edit/add/remove services

3. **Export Files**
   - **Excel**: Multi-sheet budget (one per hotel)
   - **PPT**: Beautiful presentation with branding

## API Endpoints

### Admin
- `GET /admin/` - Dashboard
- `GET/POST /admin/hotels` - Manage hotels
- `GET/POST /admin/services` - Manage services
- `GET/POST /admin/currencies` - Manage currencies
- `GET /admin/categories` - Manage categories

### Proposal
- `GET/POST /brief` - Proposal brief form
- `POST /generate` - Generate proposal files

## Database Models

### Hotel
```python
- id, name, location, description
- rate_single_aed, rate_twin_aed (prices in AED)
- stars, photo_url
- active, created_at, updated_at
```

### Service
```python
- id, name, description, category_id
- price_aed (base price)
- unit (per person, per room, per event, etc.)
- photo_url, active
- created_at, updated_at
```

### Currency
```python
- code (USD, EUR, AED, GBP)
- name, real_rate, custom_rate
- active, updated_at
```

## Configuration

Edit `.env` file to customize:

```env
FLASK_ENV=development          # development or production
SECRET_KEY=your-secret-key     # Change in production!
ANTHROPIC_API_KEY=sk-...       # For Claude AI integration
PORT=5000                      # Server port
```

## Deployment (Railway.app)

1. Push to GitHub
2. Connect Railway to repository
3. Set Root Directory: `./`
4. Add environment variables:
   - `ANTHROPIC_API_KEY`
   - `SECRET_KEY`
5. Deploy!

## Technology Stack

- **Backend**: Flask 3.1.3
- **Database**: SQLite/PostgreSQL
- **ORM**: SQLAlchemy
- **Frontend**: HTML5, CSS3, Vanilla JS
- **File Generation**: openpyxl (Excel), python-pptx (PowerPoint)
- **AI**: Claude API (Anthropic)
- **Deployment**: Railway, Docker-ready

## Troubleshooting

### Port 5000 already in use
```bash
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Database errors
Delete `instance/insiders.db` and restart

### No photos showing
Check `uploads/` folder permissions and file paths

## Next Steps

- [ ] Implement proposal form (brief)
- [ ] Add Claude AI integration for program generation
- [ ] Build Excel multi-sheet generator
- [ ] Create PPT generator with branding
- [ ] Add user authentication
- [ ] Mobile-responsive design

## Support

For issues or feature requests, contact: ahmed@insiders-uae.com

## License

© 2026 INSIDERS Tourism Dubai. All rights reserved.
