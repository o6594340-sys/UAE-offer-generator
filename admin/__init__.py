"""
Admin blueprint for managing hotels, services, and currencies
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from pathlib import Path
import os
from models import db, Hotel, Service, ServiceCategory, Currency
from utils.pptx_extractor import extract_text_from_pptx
from utils.pdf_extractor import extract_text_from_pdf
from utils.ai_extractor import extract_from_pptx_text, extract_services_from_excel_text
from utils.excel_extractor import extract_text_from_excel

admin_bp = Blueprint('admin', __name__, template_folder='templates')


def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@admin_bp.route('/')
def dashboard():
    """Admin dashboard"""
    hotels_count = Hotel.query.filter_by(active=True).count()
    services_count = Service.query.filter_by(active=True).count()
    currencies_count = Currency.query.filter_by(active=True).count()
    
    stats = {
        'hotels': hotels_count,
        'services': services_count,
        'currencies': currencies_count,
    }
    
    return render_template('admin/dashboard.html', stats=stats)


# ===================== CURRENCIES =====================

@admin_bp.route('/currencies')
def currencies():
    """Manage currencies"""
    currencies = Currency.query.all()
    return render_template('admin/currencies.html', currencies=currencies)


@admin_bp.route('/currencies/update/<int:currency_id>', methods=['POST'])
def update_currency(currency_id):
    """Update currency rate"""
    currency = Currency.query.get_or_404(currency_id)
    data = request.get_json()
    
    if 'custom_rate' in data:
        currency.custom_rate = float(data['custom_rate'])
    if 'real_rate' in data:
        currency.real_rate = float(data['real_rate'])
    if 'active' in data:
        currency.active = bool(data['active'])
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Currency updated'})


@admin_bp.route('/currencies/refresh', methods=['POST'])
def refresh_rates():
    import requests as req
    try:
        resp = req.get('https://api.frankfurter.app/latest?from=USD', timeout=8)
        data = resp.json()
        rates = data.get('rates', {})
        rates['USD'] = 1.0
        updated = {}
        for currency in Currency.query.all():
            if currency.code in rates:
                currency.real_rate = round(float(rates[currency.code]), 4)
                updated[currency.code] = currency.real_rate
        db.session.commit()
        return jsonify({'success': True, 'rates': updated})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/currencies/init', methods=['POST'])
def init_currencies():
    """Initialize default currencies"""
    from config import Config
    
    for code, info in Config.CURRENCIES.items():
        existing = Currency.query.filter_by(code=code).first()
        if not existing:
            currency = Currency(
                code=code,
                name=info['name'],
                real_rate=info['rate'],
                custom_rate=info['rate'],
                active=info['active']
            )
            db.session.add(currency)
    
    db.session.commit()
    flash(f'Currencies initialized', 'success')
    return redirect(url_for('admin.currencies'))


# ===================== HOTELS =====================

@admin_bp.route('/hotels')
def hotels():
    """List all hotels"""
    hotels = Hotel.query.all()
    return render_template('admin/hotels.html', hotels=hotels)


@admin_bp.route('/hotels/add', methods=['GET', 'POST'])
def add_hotel():
    """Add new hotel"""
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        description = request.form.get('description')
        stars = request.form.get('stars', 5, type=int)
        rate_single = request.form.get('rate_single_aed', 0, type=float)
        rate_twin = request.form.get('rate_twin_aed', 0, type=float)
        
        # Handle photo upload
        photo_url = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"hotel_{name.replace(' ', '_')}_{filename}"
                os.makedirs(os.path.join('uploads', 'hotels'), exist_ok=True)
                filepath = os.path.join('uploads', 'hotels', filename)
                file.save(filepath)
                photo_url = filepath
        
        hotel = Hotel(
            name=name,
            location=location,
            description=description,
            stars=stars,
            rate_single_aed=rate_single,
            rate_twin_aed=rate_twin,
            photo_url=photo_url,
            website_url=request.form.get('website_url', ''),
        )
        
        db.session.add(hotel)
        db.session.commit()
        
        flash(f'Hotel "{name}" added successfully', 'success')
        return redirect(url_for('admin.hotels'))
    
    return render_template('admin/hotel_form.html')


@admin_bp.route('/hotels/edit/<int:hotel_id>', methods=['GET', 'POST'])
def edit_hotel(hotel_id):
    """Edit hotel"""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    if request.method == 'POST':
        hotel.name = request.form.get('name')
        hotel.location = request.form.get('location')
        hotel.description = request.form.get('description')
        hotel.stars = request.form.get('stars', type=int)
        hotel.rate_single_aed = request.form.get('rate_single_aed', type=float)
        hotel.rate_twin_aed = request.form.get('rate_twin_aed', type=float)
        hotel.website_url = request.form.get('website_url', '')
        
        # Handle photo upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"hotel_{hotel.name.replace(' ', '_')}_{filename}"
                os.makedirs(os.path.join('uploads', 'hotels'), exist_ok=True)
                filepath = os.path.join('uploads', 'hotels', filename)
                file.save(filepath)
                hotel.photo_url = filepath
        
        db.session.commit()
        flash(f'Hotel "{hotel.name}" updated successfully', 'success')
        return redirect(url_for('admin.hotels'))
    
    return render_template('admin/hotel_form.html', hotel=hotel)


@admin_bp.route('/hotels/delete/<int:hotel_id>', methods=['POST'])
def delete_hotel(hotel_id):
    """Delete hotel"""
    hotel = Hotel.query.get_or_404(hotel_id)
    name = hotel.name
    db.session.delete(hotel)
    db.session.commit()
    flash(f'Hotel "{name}" deleted', 'success')
    return redirect(url_for('admin.hotels'))


# ===================== SERVICE CATEGORIES =====================

@admin_bp.route('/categories')
def categories():
    """Manage service categories"""
    categories = ServiceCategory.query.all()
    return render_template('admin/categories.html', categories=categories)


DEFAULT_CATEGORIES = [
    'Accommodation',
    'Transfers & Transport',
    'Activities & Excursions',
    'Dining & Catering',
    'Events & Entertainment',
    'Additional Services',
]


@admin_bp.route('/categories/init', methods=['POST'])
def init_categories():
    created = 0
    for name in DEFAULT_CATEGORIES:
        if not ServiceCategory.query.filter_by(name=name).first():
            db.session.add(ServiceCategory(name=name, description=''))
            created += 1
    db.session.commit()
    flash(f'Done: {created} categories created', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/add', methods=['POST'])
def add_category():
    """Add service category"""
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    existing = ServiceCategory.query.filter_by(name=name).first()
    if existing:
        flash('Category already exists', 'warning')
    else:
        category = ServiceCategory(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        flash(f'Category "{name}" added', 'success')
    
    return redirect(url_for('admin.categories'))


# ===================== SERVICES =====================

@admin_bp.route('/services')
def services():
    """List all services"""
    category = request.args.get('category', '')
    
    query = Service.query
    if category:
        query = query.join(ServiceCategory).filter(ServiceCategory.name == category)
    
    services = query.all()
    categories = ServiceCategory.query.all()
    
    return render_template('admin/services.html', services=services, categories=categories, selected_category=category)


@admin_bp.route('/services/add', methods=['GET', 'POST'])
def add_service():
    """Add new service"""
    categories = ServiceCategory.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category_id = request.form.get('category_id', type=int)
        price_aed = request.form.get('price_aed', 0, type=float)
        unit = request.form.get('unit', 'per person')
        
        # Handle photo upload
        photo_url = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"service_{name.replace(' ', '_')}_{filename}"
                os.makedirs(os.path.join('uploads', 'services'), exist_ok=True)
                filepath = os.path.join('uploads', 'services', filename)
                file.save(filepath)
                photo_url = filepath
        
        service = Service(
            name=name,
            description=description,
            category_id=category_id,
            price_aed=price_aed,
            unit=unit,
            photo_url=photo_url
        )
        
        db.session.add(service)
        db.session.commit()
        
        flash(f'Service "{name}" added successfully', 'success')
        return redirect(url_for('admin.services'))
    
    return render_template('admin/service_form.html', categories=categories)


@admin_bp.route('/services/edit/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    """Edit service"""
    service = Service.query.get_or_404(service_id)
    categories = ServiceCategory.query.all()
    
    if request.method == 'POST':
        service.name = request.form.get('name')
        service.description = request.form.get('description')
        service.category_id = request.form.get('category_id', type=int)
        service.price_aed = request.form.get('price_aed', type=float)
        service.unit = request.form.get('unit')
        
        # Handle photo upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"service_{service.name.replace(' ', '_')}_{filename}"
                os.makedirs(os.path.join('uploads', 'services'), exist_ok=True)
                filepath = os.path.join('uploads', 'services', filename)
                file.save(filepath)
                service.photo_url = filepath
        
        db.session.commit()
        flash(f'Service "{service.name}" updated successfully', 'success')
        return redirect(url_for('admin.services'))
    
    return render_template('admin/service_form.html', service=service, categories=categories)


@admin_bp.route('/services/delete/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    """Delete service"""
    service = Service.query.get_or_404(service_id)
    name = service.name
    db.session.delete(service)
    db.session.commit()
    flash(f'Service "{name}" deleted', 'success')
    return redirect(url_for('admin.services'))


@admin_bp.route('/services/toggle/<int:service_id>', methods=['POST'])
def toggle_service(service_id):
    """Toggle service active status"""
    service = Service.query.get_or_404(service_id)
    service.active = not service.active
    db.session.commit()
    return jsonify({'success': True, 'active': service.active})


# ===================== PPT IMPORT =====================

ALLOWED_IMPORT_EXTENSIONS = {'pptx', 'ppt', 'xlsx', 'xls', 'pdf'}


def _allowed_import(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMPORT_EXTENSIONS


def _ext(filename):
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''


@admin_bp.route('/test-api')
def test_api():
    import os, anthropic
    api_key = os.getenv('ANTHROPIC_API_KEY', '')
    if not api_key or api_key == 'your-api-key-here':
        return jsonify({'ok': False, 'error': 'ANTHROPIC_API_KEY is not set in .env'}), 400
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=16,
            messages=[{'role': 'user', 'content': 'Reply with just: OK'}]
        )
        return jsonify({'ok': True, 'response': msg.content[0].text.strip()})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@admin_bp.route('/import')
def import_page():
    existing_hotel_names = [h.name.strip().lower() for h in Hotel.query.all()]
    existing_service_names = [s.name.strip().lower() for s in Service.query.all()]
    return render_template('admin/import.html',
                           existing_hotel_names=existing_hotel_names,
                           existing_service_names=existing_service_names)


@admin_bp.route('/import/upload', methods=['POST'])
def import_upload():
    try:
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files uploaded'}), 400

        pptx_parts = []
        excel_parts = []
        skipped = []

        for f in files:
            if not f or not _allowed_import(f.filename):
                skipped.append(f.filename)
                continue
            ext = _ext(f.filename)
            try:
                file_bytes = f.read()
                if ext in ('pptx', 'ppt'):
                    text = extract_text_from_pptx(file_bytes)
                    if text.strip():
                        pptx_parts.append(f"=== {f.filename} ===\n{text}")
                elif ext == 'pdf':
                    text = extract_text_from_pdf(file_bytes)
                    if text.strip():
                        pptx_parts.append(f"=== {f.filename} ===\n{text}")
                elif ext in ('xlsx', 'xls'):
                    text = extract_text_from_excel(file_bytes)
                    if text.strip():
                        excel_parts.append(f"=== {f.filename} ===\n{text}")
            except Exception as e:
                skipped.append(f"{f.filename} (error: {str(e)})")

        if not pptx_parts and not excel_parts:
            return jsonify({'error': 'Could not extract text from uploaded files'}), 400

        result = {'hotels': [], 'services': []}

        if pptx_parts:
            pptx_result = extract_from_pptx_text("\n\n".join(pptx_parts))
            if pptx_result.get('error') and not pptx_result.get('hotels') and not pptx_result.get('services'):
                return jsonify({'error': pptx_result['error']}), 500
            result['hotels'].extend(pptx_result.get('hotels', []))
            result['services'].extend(pptx_result.get('services', []))

        if excel_parts:
            excel_result = extract_services_from_excel_text("\n\n".join(excel_parts))
            if excel_result.get('error') and not excel_result.get('hotels') and not excel_result.get('services'):
                return jsonify({'error': excel_result['error']}), 500
            result['hotels'].extend(excel_result.get('hotels', []))
            result['services'].extend(excel_result.get('services', []))

        if not result['hotels'] and not result['services']:
            return jsonify({'error': 'No content could be extracted from the files'}), 500

        result['skipped'] = skipped
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@admin_bp.route('/import/save', methods=['POST'])
def import_save():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    saved = {'hotels': 0, 'services': 0}
    updated = {'hotels': 0, 'services': 0}

    existing_hotels = {h.name.strip().lower(): h for h in Hotel.query.all()}
    existing_services = {s.name.strip().lower(): s for s in Service.query.all()}

    for h in data.get('hotels', []):
        if not h.get('selected'):
            continue
        name = h.get('name', 'Unknown Hotel')
        existing = existing_hotels.get(name.strip().lower())
        if existing:
            existing.location = h.get('location', existing.location)
            existing.description = h.get('description', existing.description)
            existing.stars = int(h.get('stars', existing.stars))
            existing.rate_single_aed = float(h.get('rate_single_aed', existing.rate_single_aed))
            existing.rate_twin_aed = float(h.get('rate_twin_aed', existing.rate_twin_aed))
            existing.website_url = h.get('website_url', existing.website_url)
            updated['hotels'] += 1
        else:
            hotel = Hotel(
                name=name,
                location=h.get('location', 'Dubai'),
                description=h.get('description', ''),
                stars=int(h.get('stars', 5)),
                rate_single_aed=float(h.get('rate_single_aed', 0)),
                rate_twin_aed=float(h.get('rate_twin_aed', 0)),
                website_url=h.get('website_url', ''),
            )
            db.session.add(hotel)
            saved['hotels'] += 1

    for s in data.get('services', []):
        if not s.get('selected'):
            continue
        name = s.get('name', 'Unknown Service')
        existing = existing_services.get(name.strip().lower())

        category_name = s.get('category', 'Additional Services')
        category = ServiceCategory.query.filter_by(name=category_name).first()
        if not category:
            category = ServiceCategory(name=category_name, description='')
            db.session.add(category)
            db.session.flush()

        if existing:
            existing.description = s.get('description', existing.description)
            existing.price_aed = float(s.get('price_aed', existing.price_aed))
            existing.unit = s.get('unit', existing.unit)
            existing.category_id = category.id
            updated['services'] += 1
        else:
            service = Service(
                name=name,
                description=s.get('description', ''),
                category_id=category.id,
                price_aed=float(s.get('price_aed', 0)),
                unit=s.get('unit', 'per person'),
            )
            db.session.add(service)
            saved['services'] += 1
            existing_services[name.strip().lower()] = service

    db.session.commit()
    return jsonify({'success': True, 'saved': saved, 'updated': updated})
