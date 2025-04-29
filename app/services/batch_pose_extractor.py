import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import mediapipe as mp
import cv2
from models.reference_models import SurfManeuver

# Setup
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "references", "pro_references", "maneuvers"))
mp_pose = mp.solutions.pose

def extract_pose_from_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Error loading {image_path}")
        return None

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    with mp_pose.Pose(static_image_mode=True) as pose:
        results = pose.process(image_rgb)

        if not results.pose_landmarks:
            print(f"⚠️ No pose detected in {image_path}")
            return None

        keypoints = {}
        for idx, lm in enumerate(results.pose_landmarks.landmark):
            keypoints[f"point_{idx}"] = [lm.x, lm.y, lm.z, lm.visibility]

        return keypoints

def save_pose_data(image_path, pose_data):
    if image_path.endswith(".jpg"):
        pose_json_path = image_path.replace(".jpg", "_pose.json")
    elif image_path.endswith(".png"):
        pose_json_path = image_path.replace(".png", "_pose.json")
    else:
        print(f"❌ Unsupported file format for {image_path}")
        return

    with open(pose_json_path, "w") as f:
        json.dump(pose_data, f)
    print(f"✅ Saved pose for {os.path.basename(image_path)}")

def batch_extract_poses():
    print(f"👀 BASE_PATH is: {os.path.abspath(BASE_PATH)}")

    if not os.path.exists(BASE_PATH):
        print(f"❌ BASE_PATH does not exist!")
        return

    print(f"📂 BASE_PATH exists! Contents:")
    print(os.listdir(BASE_PATH))
    for root, dirs, files in os.walk(BASE_PATH):
        for file in files:
            if file.endswith(".jpg") or file.endswith(".png"):
                print(f"file found : {file}")
                image_path = os.path.join(root, file)
                pose_data = extract_pose_from_image(image_path)
                if pose_data:
                    save_pose_data(image_path, pose_data)

if __name__ == "__main__":
    batch_extract_poses()

