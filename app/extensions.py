from flask_cors import CORS

def configure_extensions(app):
    CORS(app)
