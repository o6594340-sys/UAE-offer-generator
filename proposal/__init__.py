"""
Proposal blueprint - for generating commercial proposals
"""
from flask import Blueprint

proposal_bp = Blueprint('proposal', __name__, template_folder='templates')


@proposal_bp.route('/brief', methods=['GET', 'POST'])
def brief_form():
    """Proposal brief form"""
    # TODO: Implement brief form
    return '<h1>Brief Form - Coming Soon</h1>'
