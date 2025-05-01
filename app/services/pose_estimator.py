import os
import cv2
import json
import mediapipe as mp
import logging
import math
import numpy as np
from .pose_helper import calculate_angle,extract_pose_from_frame,detect_stance_from_landmarks_batch,mirror_pose,pose_similarity,rotate_pose_to_side_view,estimate_camera_to_board_angle
# Clean logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Correct base path for pro references
BASE_PRO_REFERENCE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "references", "pro_references", "maneuvers")
)
BASE_PRO_REFERENCE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "references", "pro_references", "maneuvers")
)

def load_pro_pose(maneuver_name, stage_name):
    """
    Loads a pro reference pose (JSON) for the given maneuver and stage.
    """
    maneuver_dir = maneuver_name.capitalize()
    stage_filename = stage_name.replace("-", "_").replace(" ", "_").lower() + "_pose.json"
    pose_path = os.path.join(BASE_PRO_REFERENCE_PATH, maneuver_dir, stage_filename)

    if not os.path.exists(pose_path):
        raise FileNotFoundError(f"Pro pose file not found for {maneuver_name} - {stage_name}")

    with open(pose_path, "r") as f:
        return json.load(f)
mp_pose = mp.solutions.pose
def analyze_selected_frames_with_pro_reference(video_path, maneuver_name, frame_selections):
    import logging
    analysis_results = {}
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Failed to open video file: {video_path}")

    # ====== 1. Detect stance from first 5 reliable frames ======
    landmark_batch = []
    frames_checked = 0
    frame_sample_times = [i * 0.1 for i in range(10)]  # First second, 10 frames

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()

    while frames_checked < 5 and frame_sample_times:
        t = frame_sample_times.pop(0)
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        success, frame = cap.read()
        if not success:
            continue

        results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if not results.pose_landmarks:
            continue

        landmarks = {}
        for idx, lm in enumerate(results.pose_landmarks.landmark):
            if lm.visibility > 0.5:
                landmarks[f"point_{idx}"] = [lm.x, lm.y]

        if len(landmarks) > 10:
            landmark_batch.append(landmarks)
            frames_checked += 1

    detected_stance = detect_stance_from_landmarks_batch(landmark_batch)
    logging.info(f"🧭 Detected user stance: {detected_stance}")

    # ====== 2. Analyze each selected stage frame ======
    for stage, frame_filename in frame_selections.items():
        try:
            frame_number = int(frame_filename.replace("frame_", "").replace(".jpg", ""))
            timestamp_sec = frame_number / 10.0
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
            success, frame = cap.read()

            if not success:
                logging.error(f"❌ Could not extract frame for {stage} at {timestamp_sec:.2f}s")
                analysis_results[stage] = {"error": "Frame not found in video"}
                continue

            user_pose = extract_pose_from_frame(frame)
            if not user_pose:
                logging.warning(f"⚠️ No user pose detected for {stage}")
                analysis_results[stage] = {"error": "Pose not detected in user frame"}
                continue

            logging.debug(f"🦴 Extracted user pose for {stage}: sample keys = {list(user_pose.keys())[:5]}")
            adjusted_user_pose = {k: [v[0], v[1]] for k, v in user_pose.items()}
            # 🔍 Estimate board angle and rotate pose to match side view
            cam_board_angle = estimate_camera_to_board_angle(adjusted_user_pose)
            logging.info(f"📷 Camera-to-board angle for {stage}: {cam_board_angle:.1f}°")


            # ✅ Load and mirror pro pose if needed
            try:
                pro_pose_raw = load_pro_pose(maneuver_name, stage)
                logging.debug(f"📦 Loaded pro pose for {stage}: sample keys = {list(pro_pose_raw.keys())[:5]}")
                if detected_stance == "goofy":
                    logging.info(f"🔁 Mirroring pro pose for stage {stage} to match goofy stance")
                    pro_pose_raw = mirror_pose(pro_pose_raw)


            except FileNotFoundError as e:
                logging.error(f"❌ {e}")
                analysis_results[stage] = {"error": str(e)}
                continue

            # 🛠 DEBUG: Validate input shapes for similarity
            for joint in adjusted_user_pose:
                if len(adjusted_user_pose[joint]) != 2:
                    logging.warning(f"⚠️ adjusted_user_pose[{joint}] = {adjusted_user_pose[joint]}")

            # 🔁 Compare angle-based similarity
            similarity_score, angles = pose_similarity(adjusted_user_pose, pro_pose_raw)

            trimmed_user_pose = {k: v[:2] for k, v in adjusted_user_pose.items()}
            trimmed_pro_pose  = {k: v[:2] for k, v in pro_pose_raw.items()}
            analysis_results[stage] = {
                "user_pose": user_pose,
                "adjusted_pose": trimmed_user_pose,
                "pro_pose": trimmed_pro_pose,
                "similarity_score": similarity_score,
                "camera_board_angle": cam_board_angle,
                "angles" : angles
            }

            logging.info(f"✅ Stage {stage}: Similarity Score = {similarity_score:.4f}")

        except Exception as e:
            logging.error(f"❌ Exception during pose analysis for {stage}: {str(e)}", exc_info=True)
            analysis_results[stage] = {"error": f"Exception: {str(e)}"}

    cap.release()
    return analysis_results

