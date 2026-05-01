"""
INSIDERS Dubai - Commercial Proposal Generator
Main application file
"""
import os
from pathlib import Path
from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import configuration
from config import config
from models import db

# Create Flask app
def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Create instance and upload directories if not exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['INSTANCE_PATH'], exist_ok=True)
    
    # Initialize database
    db.init_app(app)
    
    # Create tables + lightweight column migrations
    with app.app_context():
        db.create_all()
        with db.engine.connect() as conn:
            for sql in [
                'ALTER TABLE hotels ADD COLUMN website_url VARCHAR(500)',
                'ALTER TABLE proposals ADD COLUMN itinerary_json TEXT',
            ]:
                try:
                    conn.execute(db.text(sql))
                    conn.commit()
                except Exception:
                    pass
    
    import json as _json
    app.jinja_env.filters['fromjson'] = lambda s: _json.loads(s) if s else []

    # Register blueprints
    from admin import admin_bp
    from proposal import proposal_bp
    
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(proposal_bp, url_prefix='/')
    
    # Main route
    @app.route('/')
    def index():
        return redirect(url_for('proposal.brief_form'))
    
    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200
    
    return app


application = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    application.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')
