"""
Database models for INSIDERS Dubai Proposal Generator
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Currency(db.Model):
    """Currency exchange rates"""
    __tablename__ = 'currencies'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(3), unique=True, nullable=False)  # USD, EUR, AED, GBP
    name = db.Column(db.String(100), nullable=False)
    real_rate = db.Column(db.Float, default=1.0)  # Real market rate (reference)
    custom_rate = db.Column(db.Float, nullable=False, default=1.0)  # Rate for calculations
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Currency {self.code}>'


class Hotel(db.Model):
    """Hotels offered by INSIDERS"""
    __tablename__ = 'hotels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))  # Dubai, Abu Dhabi, etc.
    description = db.Column(db.Text)
    photo_url = db.Column(db.String(500))
    website_url = db.Column(db.String(500))
    stars = db.Column(db.Integer, default=5)  # 3, 4, 5 stars
    
    # Room rates in AED (base currency)
    rate_single_aed = db.Column(db.Float, nullable=False)  # Single room per night
    rate_twin_aed = db.Column(db.Float, nullable=False)    # Twin/Double room per night
    
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Hotel {self.name}>'


class ServiceCategory(db.Model):
    """Categories for services"""
    __tablename__ = 'service_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(500))
    
    services = db.relationship('Service', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ServiceCategory {self.name}>'


class Service(db.Model):
    """Services: activities, transfers, dining, events, etc."""
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('service_categories.id'), nullable=False)
    
    # Price in AED (base currency)
    price_aed = db.Column(db.Float, nullable=False)
    
    # Unit for pricing
    unit = db.Column(db.String(50), default='per person')  # per person, per room, per event, etc.
    
    photo_url = db.Column(db.String(500))  # File path or URL
    active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Service {self.name}>'


class ProposalProgram(db.Model):
    """Program items for a proposal (day by day)"""
    __tablename__ = 'proposal_programs'
    
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.String(100))  # UUID or proposal identifier
    
    day = db.Column(db.Integer, nullable=False)  # Day 1, 2, 3, etc.
    timing = db.Column(db.String(100))  # e.g., "09:00 - 12:00" or "Morning"
    
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    service = db.relationship('Service', backref='program_items')
    
    quantity = db.Column(db.Integer, default=1)  # How many times this service
    notes = db.Column(db.Text)  # Additional notes
    
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotels.id'))  # Optional: specific hotel
    hotel = db.relationship('Hotel', backref='program_items')
    
    order = db.Column(db.Integer, default=0)  # Order within the day
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProposalProgram Day {self.day}>'


class Proposal(db.Model):
    """Main proposal record"""
    __tablename__ = 'proposals'
    
    id = db.Column(db.String(100), primary_key=True)  # UUID
    
    # Client info
    company_name = db.Column(db.String(200), nullable=False)
    group_type = db.Column(db.String(100))  # Meeting, Incentive, Conference, etc.
    industry = db.Column(db.String(100))
    pax = db.Column(db.Integer, nullable=False)  # Number of people
    
    # Dates
    arrival_date = db.Column(db.DateTime)
    departure_date = db.Column(db.DateTime)
    
    # Settings
    currency_code = db.Column(db.String(3), default='AED')
    
    # Selected items (JSON or relationships)
    hotels_selected = db.Column(db.String(500))  # Comma-separated hotel IDs
    services_selected = db.Column(db.String(1000))  # Comma-separated service IDs
    
    special_requests = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(50), default='draft')  # draft, finalized, exported
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Proposal {self.company_name}>'
