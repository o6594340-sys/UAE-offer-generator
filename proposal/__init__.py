"""
Proposal blueprint - brief form, budget view, Excel export
"""
import uuid
import math
from datetime import datetime
from io import BytesIO

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file
from models import db, Hotel, Service, ServiceCategory, Currency, Proposal
from utils.brief_extractor import extract_text_from_brief
from utils.ai_extractor import extract_from_brief_text

proposal_bp = Blueprint('proposal', __name__, template_folder='templates')


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_rate(currency_code):
    """Return (aed_rate, target_rate). Prices stored in AED."""
    aed = Currency.query.filter_by(code='AED').first()
    target = Currency.query.filter_by(code=currency_code).first()
    aed_rate = aed.custom_rate if aed else 3.67
    target_rate = target.custom_rate if target else 1.0
    return aed_rate, target_rate


def _aed_to(price_aed, aed_rate, target_rate):
    if aed_rate == 0:
        return 0
    return price_aed / aed_rate * target_rate


def _nights(arrival, departure):
    if arrival and departure and departure > arrival:
        return (departure - arrival).days
    return 1


def _build_budget(proposal):
    """Return structured budget dict for template and Excel."""
    aed_rate, target_rate = _get_rate(proposal.currency_code)
    nights = _nights(proposal.arrival_date, proposal.departure_date)
    pax = proposal.pax

    hotel_ids = [int(x) for x in (proposal.hotels_selected or '').split(',') if x.strip()]
    service_ids = [int(x) for x in (proposal.services_selected or '').split(',') if x.strip()]

    hotels = Hotel.query.filter(Hotel.id.in_(hotel_ids)).all() if hotel_ids else []
    services = Service.query.filter(Service.id.in_(service_ids)).all() if service_ids else []

    hotel_rows = []
    for h in hotels:
        single_aed = h.rate_single_aed * nights
        twin_aed = h.rate_twin_aed * nights
        hotel_rows.append({
            'name': h.name,
            'location': h.location,
            'stars': h.stars,
            'nights': nights,
            'rate_single_aed': h.rate_single_aed,
            'rate_twin_aed': h.rate_twin_aed,
            'total_single_aed': single_aed,
            'total_twin_aed': twin_aed,
            'total_single': _aed_to(single_aed, aed_rate, target_rate),
            'total_twin': _aed_to(twin_aed, aed_rate, target_rate),
        })

    service_rows = []
    for s in services:
        unit = s.unit or 'per person'
        if unit == 'per person':
            qty = pax
        elif unit == 'per day':
            qty = nights
        elif unit == 'per room':
            qty = math.ceil(pax / 2)
        else:
            qty = 1
        total_aed = s.price_aed * qty
        service_rows.append({
            'name': s.name,
            'category': s.category.name if s.category else '',
            'price_aed': s.price_aed,
            'unit': unit,
            'qty': qty,
            'total_aed': total_aed,
            'total': _aed_to(total_aed, aed_rate, target_rate),
        })

    services_total = sum(r['total'] for r in service_rows)
    hotels_total_single = sum(r['total_single'] for r in hotel_rows)
    hotels_total_twin = sum(r['total_twin'] for r in hotel_rows)

    return {
        'currency': proposal.currency_code,
        'nights': nights,
        'pax': pax,
        'hotels': hotel_rows,
        'services': service_rows,
        'services_total': services_total,
        'hotels_total_single': hotels_total_single,
        'hotels_total_twin': hotels_total_twin,
        'grand_total_single': hotels_total_single + services_total,
        'grand_total_twin': hotels_total_twin + services_total,
    }


# ── routes ────────────────────────────────────────────────────────────────────

@proposal_bp.route('/brief', methods=['GET'])
def brief_form():
    hotels = Hotel.query.filter_by(active=True).order_by(Hotel.name).all()
    services = Service.query.filter_by(active=True).order_by(Service.name).all()
    currencies = Currency.query.filter_by(active=True).all()
    return render_template('proposal/brief.html',
                           hotels=hotels, services=services, currencies=currencies)


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


@proposal_bp.route('/brief/submit', methods=['POST'])
def brief_submit():
    def _parse_date(s):
        if not s:
            return None
        try:
            return datetime.strptime(s, '%Y-%m-%d')
        except ValueError:
            return None

    hotel_ids = ','.join(request.form.getlist('hotel_ids'))
    service_ids = ','.join(request.form.getlist('service_ids'))

    proposal = Proposal(
        id=str(uuid.uuid4()),
        company_name=request.form.get('company_name', 'Unknown'),
        group_type=request.form.get('group_type', ''),
        industry=request.form.get('industry', ''),
        pax=int(request.form.get('pax', 1)),
        arrival_date=_parse_date(request.form.get('arrival_date')),
        departure_date=_parse_date(request.form.get('departure_date')),
        currency_code=request.form.get('currency', 'USD'),
        hotels_selected=hotel_ids,
        services_selected=service_ids,
        special_requests=request.form.get('special_requests', ''),
        status='draft',
    )
    db.session.add(proposal)
    db.session.commit()
    return redirect(url_for('proposal.budget_view', proposal_id=proposal.id))


@proposal_bp.route('/proposal/<proposal_id>')
def budget_view(proposal_id):
    proposal = Proposal.query.get_or_404(proposal_id)
    budget = _build_budget(proposal)
    return render_template('proposal/budget.html', proposal=proposal, budget=budget)


@proposal_bp.route('/proposal/<proposal_id>/excel')
def export_excel(proposal_id):
    proposal = Proposal.query.get_or_404(proposal_id)
    budget = _build_budget(proposal)
    output = _generate_excel(proposal, budget)
    filename = f"Proposal_{proposal.company_name.replace(' ', '_')}.xlsx"
    return send_file(output, as_attachment=True,
                     download_name=filename,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# ── Excel generation ──────────────────────────────────────────────────────────

def _generate_excel(proposal, budget):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    cur = budget['currency']

    # ── Sheet 1: Summary ──
    ws = wb.active
    ws.title = 'Summary'

    BLUE = '1a73e8'
    LIGHT_BLUE = 'e8f0fe'
    GOLD = 'f9ab00'
    LIGHT_GOLD = 'fef9e7'
    GRAY = 'f5f5f5'

    def hdr_fill(color):
        return PatternFill('solid', fgColor=color)

    def bold(size=11):
        return Font(bold=True, size=size)

    def border():
        s = Side(style='thin', color='cccccc')
        return Border(left=s, right=s, top=s, bottom=s)

    def money(val):
        return round(val, 2)

    # Title
    ws.merge_cells('A1:G1')
    ws['A1'] = f'INSIDERS Dubai — Commercial Proposal'
    ws['A1'].font = Font(bold=True, size=16, color='FFFFFF')
    ws['A1'].fill = hdr_fill(BLUE)
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 36

    # Client info
    info = [
        ('Client', proposal.company_name),
        ('Group Type', proposal.group_type or '—'),
        ('Industry', proposal.industry or '—'),
        ('Pax', str(proposal.pax)),
        ('Arrival', proposal.arrival_date.strftime('%d %b %Y') if proposal.arrival_date else '—'),
        ('Departure', proposal.departure_date.strftime('%d %b %Y') if proposal.departure_date else '—'),
        ('Nights', str(budget['nights'])),
        ('Currency', cur),
    ]
    for i, (label, val) in enumerate(info, 3):
        ws.cell(i, 1, label).font = bold()
        ws.cell(i, 1).fill = hdr_fill(GRAY)
        ws.merge_cells(f'B{i}:G{i}')
        ws.cell(i, 2, val)

    row = 3 + len(info) + 1

    # Hotels section
    ws.cell(row, 1, 'HOTELS').font = Font(bold=True, size=13, color='FFFFFF')
    ws.cell(row, 1).fill = hdr_fill(BLUE)
    ws.merge_cells(f'A{row}:G{row}')
    row += 1

    heads = ['Hotel', 'Location', 'Stars', 'Nights', f'Single/night ({cur})', f'Twin/night ({cur})',
             f'Total Single ({cur})', f'Total Twin ({cur})']
    for col, h in enumerate(heads, 1):
        c = ws.cell(row, col, h)
        c.font = bold()
        c.fill = hdr_fill(LIGHT_BLUE)
        c.border = border()
    row += 1

    for h in budget['hotels']:
        vals = [h['name'], h['location'], f"{h['stars']}★", h['nights'],
                money(_aed_to(h['rate_single_aed'], *_get_aed_target(proposal.currency_code))),
                money(_aed_to(h['rate_twin_aed'], *_get_aed_target(proposal.currency_code))),
                money(h['total_single']), money(h['total_twin'])]
        for col, v in enumerate(vals, 1):
            c = ws.cell(row, col, v)
            c.border = border()
        row += 1

    if not budget['hotels']:
        ws.cell(row, 1, 'No hotels selected').font = Font(italic=True, color='999999')
        row += 1

    row += 1

    # Services section
    ws.cell(row, 1, 'SERVICES & ACTIVITIES').font = Font(bold=True, size=13, color='FFFFFF')
    ws.cell(row, 1).fill = hdr_fill(GOLD)
    ws.merge_cells(f'A{row}:G{row}')
    row += 1

    sheads = ['Service', 'Category', 'Unit', 'Qty', f'Price/unit ({cur})', f'Total ({cur})']
    for col, h in enumerate(sheads, 1):
        c = ws.cell(row, col, h)
        c.font = bold()
        c.fill = hdr_fill(LIGHT_GOLD)
        c.border = border()
    row += 1

    aed_r, tgt_r = _get_aed_target(proposal.currency_code)
    for s in budget['services']:
        vals = [s['name'], s['category'], s['unit'], s['qty'],
                money(_aed_to(s['price_aed'], aed_r, tgt_r)), money(s['total'])]
        for col, v in enumerate(vals, 1):
            c = ws.cell(row, col, v)
            c.border = border()
        row += 1

    if not budget['services']:
        ws.cell(row, 1, 'No services selected').font = Font(italic=True, color='999999')
        row += 1

    row += 1

    # Totals
    totals = [
        ('Services Total', budget['services_total']),
        ('Hotels Total (single rooms)', budget['hotels_total_single']),
        ('Hotels Total (twin rooms)', budget['hotels_total_twin']),
        ('GRAND TOTAL (single)', budget['grand_total_single']),
        ('GRAND TOTAL (twin)', budget['grand_total_twin']),
    ]
    for label, val in totals:
        is_grand = 'GRAND' in label
        ws.cell(row, 4, label).font = Font(bold=is_grand, size=12 if is_grand else 11)
        ws.merge_cells(f'D{row}:F{row}')
        c = ws.cell(row, 7, money(val))
        c.font = Font(bold=is_grand, size=12 if is_grand else 11,
                      color='FFFFFF' if is_grand else '000000')
        if is_grand:
            ws.cell(row, 4).fill = hdr_fill(BLUE)
            c.fill = hdr_fill(BLUE)
        c.border = border()
        row += 1

    # Special requests
    if proposal.special_requests:
        row += 1
        ws.cell(row, 1, 'Special Requests / Notes').font = bold()
        row += 1
        ws.merge_cells(f'A{row}:G{row}')
        ws.cell(row, 1, proposal.special_requests)
        ws.cell(row, 1).alignment = Alignment(wrap_text=True)
        ws.row_dimensions[row].height = 60

    # Column widths
    col_widths = [30, 18, 8, 8, 18, 18, 18, 18]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ── One sheet per hotel ──
    for h in budget['hotels']:
        ws2 = wb.create_sheet(title=h['name'][:30])
        ws2['A1'] = h['name']
        ws2['A1'].font = Font(bold=True, size=14)
        ws2.merge_cells('A1:F1')

        ws2['A2'] = f"{h['location']} · {h['stars']}★ · {h['nights']} nights"
        ws2['A2'].font = Font(italic=True, color='666666')
        ws2.merge_cells('A2:F2')

        r = 4
        for label, val in [
            (f'Single room/night ({cur})', money(_aed_to(h['rate_single_aed'], aed_r, tgt_r))),
            (f'Twin room/night ({cur})', money(_aed_to(h['rate_twin_aed'], aed_r, tgt_r))),
            (f'Total single × {h["nights"]} nights', money(h['total_single'])),
            (f'Total twin × {h["nights"]} nights', money(h['total_twin'])),
        ]:
            ws2.cell(r, 1, label).font = bold()
            ws2.cell(r, 1).fill = hdr_fill(LIGHT_BLUE)
            ws2.cell(r, 3, val).font = Font(bold='Total' in label)
            r += 1

        r += 1
        ws2.cell(r, 1, 'Services included in this proposal:').font = bold()
        r += 1
        for s in budget['services']:
            ws2.cell(r, 1, f'• {s["name"]}')
            ws2.cell(r, 3, money(s['total']))
            r += 1

        ws2.column_dimensions['A'].width = 35
        ws2.column_dimensions['C'].width = 18

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def _get_aed_target(currency_code):
    aed = Currency.query.filter_by(code='AED').first()
    target = Currency.query.filter_by(code=currency_code).first()
    return (aed.custom_rate if aed else 3.67), (target.custom_rate if target else 1.0)
