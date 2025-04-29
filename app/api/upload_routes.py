import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@upload_bp.route('', methods=['POST'])
def upload_video():
    uid = current_app.config['SESSION_UID']

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        session_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], uid)
        os.makedirs(session_folder, exist_ok=True)

        filepath = os.path.join(session_folder, filename)
        file.save(filepath)

        return jsonify({
            'message': 'File uploaded successfully.',
            'uid': uid,
            'filename': filename,
            'filepath': filepath
        }), 200

    return jsonify({'error': 'Invalid file type'}), 400

