"""
Demo data initialization for INSIDERS Dubai
Run this to populate the database with sample data
"""
from models import db, Hotel, Service, ServiceCategory, Currency
from app import create_app

def init_demo_data():
    """Initialize demo data for testing"""
    app = create_app()
    with app.app_context():
        print("🏨 Adding demo hotels...")

        # Demo hotels
        hotels = [
            {
                'name': 'Atlantis The Palm',
                'location': 'Dubai',
                'description': 'Luxury beach resort with water park and aquarium',
                'stars': 5,
                'rate_single_aed': 1200,
                'rate_twin_aed': 1300,
            },
            {
                'name': 'Yas Plaza Hotel',
                'location': 'Abu Dhabi',
                'description': 'Modern hotel near Yas Island with Formula 1 track',
                'stars': 4,
                'rate_single_aed': 800,
                'rate_twin_aed': 900,
            },
            {
                'name': 'Conrad Etihad Towers',
                'location': 'Abu Dhabi',
                'description': 'Iconic twin towers with stunning views',
                'stars': 5,
                'rate_single_aed': 1500,
                'rate_twin_aed': 1600,
            },
        ]

        for hotel_data in hotels:
            existing = Hotel.query.filter_by(name=hotel_data['name']).first()
            if not existing:
                hotel = Hotel(**hotel_data)
                db.session.add(hotel)

        print("🎯 Adding demo services...")

        # Get categories
        accommodation = ServiceCategory.query.filter_by(name='Accommodation').first()
        transfers = ServiceCategory.query.filter_by(name='Transfers & Transport').first()
        activities = ServiceCategory.query.filter_by(name='Activities & Excursions').first()
        dining = ServiceCategory.query.filter_by(name='Dining & Catering').first()

        # Demo services
        services = [
            {
                'name': 'Airport Transfer (45 pax)',
                'description': 'VIP airport transfer from/to airport',
                'category_id': transfers.id if transfers else 1,
                'price_aed': 295,
                'unit': 'per transfer',
            },
            {
                'name': 'Desert Safari',
                'description': 'Full day desert safari with BBQ dinner',
                'category_id': activities.id if activities else 1,
                'price_aed': 185,
                'unit': 'per person',
            },
            {
                'name': 'Dubai City Tour',
                'description': 'Guided city tour with Burj Khalifa visit',
                'category_id': activities.id if activities else 1,
                'price_aed': 95,
                'unit': 'per person',
            },
            {
                'name': 'Buffet Dinner',
                'description': 'International buffet dinner at hotel',
                'category_id': dining.id if dining else 1,
                'price_aed': 57,
                'unit': 'per person',
            },
            {
                'name': 'Russian Speaking Guide',
                'description': 'Professional guide for the entire day',
                'category_id': transfers.id if transfers else 1,
                'price_aed': 130,
                'unit': 'per day',
            },
        ]

        for service_data in services:
            existing = Service.query.filter_by(name=service_data['name']).first()
            if not existing:
                service = Service(**service_data)
                db.session.add(service)

        db.session.commit()
        print("✅ Demo data added successfully!")
        print(f"🏨 Hotels: {Hotel.query.count()}")
        print(f"🎯 Services: {Service.query.count()}")


if __name__ == '__main__':
    init_demo_data()
