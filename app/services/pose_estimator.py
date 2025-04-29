import os
import cv2
import json
import mediapipe as mp
import logging
import math
# Clean logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Correct base path for pro references
BASE_PRO_REFERENCE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "references", "pro_references", "maneuvers")
)

mp_pose = mp.solutions.pose

# ========== Helper Functions ==========

def calculate_angle(a, b, c):
    """
    Calculates the angle between three points: a-b-c (in degrees).
    Each point must be (x, y, z, visibility).
    """
    try:
        a = np.array(a[:3])  # use x, y, z
        b = np.array(b[:3])
        c = np.array(c[:3])

        ba = a - b
        bc = c - b

        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        return math.degrees(angle)
    except:
        return None


def extract_pose_from_frame(frame):
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    with mp_pose.Pose(static_image_mode=True) as pose:
        results = pose.process(image_rgb)
        if not results.pose_landmarks:
            return None

        keypoints = {}
        for idx, lm in enumerate(results.pose_landmarks.landmark):
            keypoints[f"point_{idx}"] = [lm.x, lm.y, lm.z, lm.visibility]

        return keypoints

def load_pro_pose(maneuver_name, stage_name):
    maneuver_dir = maneuver_name.replace("-", "_").replace(" ", "_")
    stage_filename = stage_name.replace("-", "_").replace(" ", "_").lower() + "_pose.json"
    pose_path = os.path.join(BASE_PRO_REFERENCE_PATH, maneuver_dir, stage_filename)

    if not os.path.exists(pose_path):
        raise FileNotFoundError(f"Pro pose file not found for {maneuver_name} - {stage_name}")

    with open(pose_path, "r") as f:
        return json.load(f)

def pose_similarity(user_pose, pro_pose):
    """
    Compare user and pro based on joint angles.
    """
    important_joints = {
        "left_elbow":  (11, 13, 15),  # Shoulder, Elbow, Wrist
        "right_elbow": (12, 14, 16),
        "left_knee":   (23, 25, 27),  # Hip, Knee, Ankle
        "right_knee":  (24, 26, 28),
        "left_shoulder_rotation": (23, 11, 13), # Hip, Shoulder, Elbow
        "right_shoulder_rotation": (24, 12, 14),
        "left_hip_rotation": (11, 23, 25), # Shoulder, Hip, Knee
        "right_hip_rotation": (12, 24, 26),
    }

    total_diff = 0
    valid_angles = 0

    for joint_name, (p1_idx, p2_idx, p3_idx) in important_joints.items():
        user_angle = calculate_angle(user_pose[f"point_{p1_idx}"], user_pose[f"point_{p2_idx}"], user_pose[f"point_{p3_idx}"])
        pro_angle = calculate_angle(pro_pose[f"point_{p1_idx}"], pro_pose[f"point_{p2_idx}"], pro_pose[f"point_{p3_idx}"])

        if user_angle is not None and pro_angle is not None:
            diff = abs(user_angle - pro_angle)
            total_diff += diff
            valid_angles += 1

    return total_diff / valid_angles if valid_angles else float('inf')

# ========== New Core Function ==========
def analyze_selected_frames_with_pro_reference(video_path, maneuver_name, frame_selections):
    analysis_results = {}

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Failed to open video file: {video_path}")

    for stage, frame_filename in frame_selections.items():
        try:
            frame_number = int(frame_filename.replace("frame_", "").replace(".jpg", ""))
            timestamp_sec = frame_number / 10.0  # Assuming 10 fps slider scaling
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
            success, frame = cap.read()

            if not success:
                logging.error(f"❌ Could not extract frame for {stage} at {timestamp_sec:.2f}s")
                analysis_results[stage] = {"error": "Frame not found in video"}
                continue

            user_pose = extract_pose_from_frame(frame)

            if not user_pose:
                logging.warning(f"⚠️ No pose detected in frame at {timestamp_sec:.2f}s for stage {stage}")
                analysis_results[stage] = {"error": "Pose not detected in user frame"}
                continue

            try:
                pro_pose = load_pro_pose(maneuver_name, stage)
            except FileNotFoundError as e:
                logging.error(f"❌ {e}")
                analysis_results[stage] = {"error": str(e)}
                continue

            similarity_score = pose_similarity(user_pose, pro_pose)

            analysis_results[stage] = {
                "user_pose": user_pose,
                "pro_pose": pro_pose,
                "similarity_score": similarity_score
            }

            logging.info(f"✅ Stage {stage}: Similarity Score = {similarity_score:.4f}")

        except Exception as e:
            logging.error(f"❌ Exception during pose analysis for {stage}: {str(e)}")
            analysis_results[stage] = {"error": f"Exception: {str(e)}"}

    cap.release()
    return analysis_results

