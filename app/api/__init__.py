from .upload_routes import upload_bp
from .pose_routes import pose_bp
from .frame_routes import frame_selection_bp
from .reference_routes import reference_bp
from .joints_routes import joints_bp
from .img_routes import reference_img_bp
from .coach_routes import coach_bp

def register_blueprints(app):
    app.register_blueprint(upload_bp, url_prefix='/upload')
    app.register_blueprint(frame_selection_bp, url_prefix='/frame_selection')
    app.register_blueprint(pose_bp, url_prefix='/pose')
    app.register_blueprint(reference_bp, url_prefix='/reference')
    app.register_blueprint(joints_bp)
    app.register_blueprint(reference_img_bp)
    app.register_blueprint(coach_bp, url_prefix='/coach')

