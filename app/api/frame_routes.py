# app/api/frame_routes.py

from flask import Blueprint, request, jsonify
import os
import json

frame_selection_bp = Blueprint('frame_selection', __name__)

FRAME_SELECTION_FOLDER = 'app/uploads/frame_selections'
os.makedirs(FRAME_SELECTION_FOLDER, exist_ok=True)

@frame_selection_bp.route('/', methods=['POST'])
def save_frame_selection():
    data = request.get_json()

    folder_name = data.get('folder_name')
    maneuver_name = data.get('maneuver_name')
    frame_selections = data.get('frame_selections')

    if not folder_name or not maneuver_name or not frame_selections:
        return jsonify({'error': 'Missing required fields.'}), 400

    save_path = os.path.join(FRAME_SELECTION_FOLDER, f"{folder_name}_{maneuver_name}.json")

    try:
        with open(save_path, 'w') as f:
            json.dump(frame_selections, f, indent=4)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Frame selections saved successfully.'}), 200

