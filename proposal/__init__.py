"""
Proposal blueprint - for generating commercial proposals
"""
from flask import Blueprint, render_template, request, jsonify
from models import db, Hotel, Service, ServiceCategory, Currency
from utils.brief_extractor import extract_text_from_brief
from utils.ai_extractor import extract_from_brief_text

proposal_bp = Blueprint('proposal', __name__, template_folder='templates')


@proposal_bp.route('/brief', methods=['GET'])
def brief_form():
    hotels = Hotel.query.filter_by(active=True).order_by(Hotel.name).all()
    services = Service.query.filter_by(active=True).order_by(Service.name).all()
    categories = ServiceCategory.query.all()
    currencies = Currency.query.filter_by(active=True).all()
    return render_template(
        'proposal/brief.html',
        hotels=hotels,
        services=services,
        categories=categories,
        currencies=currencies,
    )


@proposal_bp.route('/brief/parse', methods=['POST'])
def parse_brief():
    text = None

    if 'file' in request.files and request.files['file'].filename:
        f = request.files['file']
        text = extract_text_from_brief(f.read(), f.filename)
    elif request.form.get('text'):
        text = request.form.get('text')

    if not text or not text.strip():
        return jsonify({'error': 'No content provided'}), 400

    result = extract_from_brief_text(text)
    if 'error' in result:
        return jsonify({'error': result['error']}), 500

    return jsonify(result)
