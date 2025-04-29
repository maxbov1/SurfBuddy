import base64
import numpy as np
import cv2
from flask import Blueprint, request, jsonify
import mediapipe as mp

joints_bp = Blueprint('joints', __name__)

@joints_bp.route('/joints_preview', methods=['POST'])
def joints_preview():
    data = request.get_json()
    image_b64 = data.get('image')

    if not image_b64:
        return jsonify({'error': 'No image data provided'}), 400

    try:
        image_data = base64.b64decode(image_b64.split(',')[1])
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose()
        results = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        if not results.pose_landmarks:
            print("⚠️ Mediapipe: No pose landmarks detected.")
            return jsonify({'pose_detected': False})

        landmarks = {}
        reliable_points = 0
        total_points = len(results.pose_landmarks.landmark)

        for idx, lm in enumerate(results.pose_landmarks.landmark):
            if lm.visibility > 0.5:
                landmarks[f"point_{idx}"] = [lm.x, lm.y]
                reliable_points += 1

        print(f"✅ Mediapipe: {reliable_points}/{total_points} joints reliably detected.")

        if reliable_points < 8:
            print("⚠️ Mediapipe: Pose detected but too few reliable joints.")

        return jsonify({
            'pose_detected': reliable_points >= 8,
            'landmarks': landmarks
        })

    except Exception as e:
        print(f"❌ Error during pose estimation: {str(e)}")
        return jsonify({'error': str(e)}), 500

