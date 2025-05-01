import os
import cv2
import json
import mediapipe as mp
import logging
import math
import numpy as np

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

def pose_similarity(user_pose, pro_pose):
    """
    Compare user and pro based on joint angles.
    """
    important_joints = {
        "left_elbow":  (11, 13, 15),
        "right_elbow": (12, 14, 16),
        "left_knee":   (23, 25, 27),
        "right_knee":  (24, 26, 28),
        "left_shoulder_rotation": (23, 11, 13),
        "right_shoulder_rotation": (24, 12, 14),
        "left_hip_rotation": (11, 23, 25),
        "right_hip_rotation": (12, 24, 26),
    }
    angle_differences = {}


    total_diff = 0
    valid_angles = 0

    for joint_name, (p1_idx, p2_idx, p3_idx) in important_joints.items():
        key_a, key_b, key_c = f"point_{p1_idx}", f"point_{p2_idx}", f"point_{p3_idx}"

        if key_a in user_pose and key_b in user_pose and key_c in user_pose and \
           key_a in pro_pose and key_b in pro_pose and key_c in pro_pose:

            user_angle = calculate_angle(user_pose[key_a], user_pose[key_b], user_pose[key_c])
            pro_angle = calculate_angle(pro_pose[key_a], pro_pose[key_b], pro_pose[key_c])

            if user_angle is not None and pro_angle is not None:
                diff = abs(user_angle - pro_angle)
                angle_differences[joint_name] = {
                "user_angle": user_angle,
                "pro_angle": pro_angle,
                "difference": diff
                }
                total_diff += diff
                valid_angles += 1

    avg_diff = total_diff / valid_angles if valid_angles else float('inf')
    return avg_diff,angle_differences

def detect_stance_from_landmarks_batch(landmarks_list):
    counts = {"regular": 0, "goofy": 0}
    for landmarks in landmarks_list:
        if "point_11" in landmarks and "point_12" in landmarks:
            if landmarks["point_11"][0] > landmarks["point_12"][0]:
                counts["regular"] += 1
            else:
                counts["goofy"] += 1
    if counts["regular"] > counts["goofy"]:
        return "regular"
    elif counts["goofy"] > counts["regular"]:
        return "goofy"
    return None

def mirror_pose(landmarks):
    return {key: [1 - x, y] for key, (x, y) in landmarks.items()}

def estimate_camera_to_board_angle(landmarks):
    """
    Estimate the angle (degrees) between camera direction and board direction.
    """
    if "point_0" not in landmarks or "point_32" not in landmarks:
        return None

    nose = np.array(landmarks["point_0"])
    tail = np.array(landmarks["point_32"])
    board_vector = nose - tail

    if np.linalg.norm(board_vector) == 0:
        return None

    camera_pos = np.array([0.5, 1.0])  # bottom center
    surfer_pos = (nose + tail) / 2
    camera_vector = surfer_pos - camera_pos

    if np.linalg.norm(camera_vector) == 0:
        return None

    board_unit = board_vector / np.linalg.norm(board_vector)
    camera_unit = camera_vector / np.linalg.norm(camera_vector)
    dot = np.clip(np.dot(board_unit, camera_unit), -1.0, 1.0)

    angle_rad = np.arccos(dot)
    angle_deg = np.degrees(angle_rad)

    return angle_deg

def rotate_pose_to_side_view(landmarks, angle_deg):
    """
    Rotates pose landmarks by -angle_deg around image center to simulate side view.
    Assumes normalized coordinates in range [0, 1].
    """
    if angle_deg is None:
        return landmarks

    angle_rad = -np.radians(angle_deg)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)

    center = np.array([0.5, 0.5])
    rotated = {}

    for key, (x, y) in landmarks.items():
        point = np.array([x, y]) - center
        rotated_point = np.array([
            point[0] * cos_a - point[1] * sin_a,
            point[0] * sin_a + point[1] * cos_a
        ]) + center

        rotated[key] = np.clip(rotated_point, 0, 1)

    return rotated

