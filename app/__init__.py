from flask import Flask, render_template  
from flask_cors import CORS
from .extensions import configure_extensions
from .api import register_blueprints
import uuid

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    configure_extensions(app)
    register_blueprints(app)
    app.config['SESSION_UID'] = str(uuid.uuid4())
    print(f"🆕 New SurfBuddy Session UID: {app.config['SESSION_UID']}")
    @app.route('/')
    def wizard():
        return render_template('wizard.html')

    print("🧪 MAX_CONTENT_LENGTH:", app.config.get("MAX_CONTENT_LENGTH"))

    return app
