import os
from flask import Blueprint, request, jsonify, current_app
from app.services.pose_estimator import analyze_selected_frames_with_pro_reference

pose_bp = Blueprint('pose', __name__)

@pose_bp.route('/', methods=['POST'])
def analyze_pose():
    data = request.get_json()

    uid = current_app.config['SESSION_UID']
    maneuver_name = data.get('maneuver_name')
    frame_selections = data.get('frame_selections')

    if not uid or not maneuver_name or not frame_selections:
        return jsonify({'error': 'Missing required fields.'}), 400

    # ✅ Find the uploaded video file
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], uid)
    video_files = [f for f in os.listdir(upload_folder) if f.endswith(('.mp4', '.mov'))]

    if not video_files:
        return jsonify({'error': 'No uploaded video found for UID.'}), 404

    video_path = os.path.join(upload_folder, video_files[0])

    try:
        # ✅ Instead of looking for pre-extracted frames,
        # dynamically extract the needed frames from video_path
        analysis_results = analyze_selected_frames_with_pro_reference(
            video_path=video_path,     # pass full video
            maneuver_name=maneuver_name,
            frame_selections=frame_selections
        )
    except Exception as e:
        current_app.logger.error(f"Pose analysis failed: {e}")
        return jsonify({'error': f'Pose analysis failed: {e}'}), 500

    return jsonify({'pose_analysis': analysis_results}), 200

