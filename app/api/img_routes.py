# app/api/img_routes.py
# wants to reach into app/references/pro_references/maneuvers/"stage"

from flask import Blueprint, send_from_directory, abort,send_file
import os

reference_img_bp = Blueprint("reference_img", __name__)

# Get the absolute path to the root of /app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Go up to /app/, then into /references/pro_references/maneuvers
BASE_IMAGE_DIR = os.path.join(BASE_DIR, "..", "references", "pro_references", "maneuvers")
BASE_IMAGE_DIR = os.path.abspath(BASE_IMAGE_DIR)  # clean up ".."

@reference_img_bp.route("/pro_image/<maneuver>/<stage>")
def serve_pro_image(maneuver, stage):
    from PIL import Image, ImageDraw
    from io import BytesIO
    import json

    maneuver_dir = os.path.join(BASE_IMAGE_DIR, maneuver.capitalize())
    image_path = os.path.join(maneuver_dir, f"{stage}.png")
    json_path = os.path.join(maneuver_dir, f"{stage.lower()}_pose.json")

    if not os.path.exists(image_path):
        return abort(404, description=f"Image {image_path} not found.")

    image = Image.open(image_path).convert("RGBA")

    # Try drawing skeleton if JSON exists
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            raw_landmarks = json.load(f)

        # ✅ Strip [x, y] only
        landmarks = {
            k: [v[0], v[1]]
            for k, v in raw_landmarks.items()
            if isinstance(v, list) and len(v) >= 2
        }

        draw = ImageDraw.Draw(image)

        # Skeleton connections (same as JS)
        connections = [
            ("point_11", "point_13"), ("point_13", "point_15"),
            ("point_12", "point_14"), ("point_14", "point_16"),
            ("point_11", "point_12"), ("point_11", "point_23"),
            ("point_12", "point_24"), ("point_23", "point_24"),
            ("point_23", "point_25"), ("point_25", "point_27"),
            ("point_24", "point_26"), ("point_26", "point_28"),
        ]

        # ✅ Draw bones
        for start, end in connections:
            if start in landmarks and end in landmarks:
                x1, y1 = landmarks[start]
                x2, y2 = landmarks[end]
                draw.line([x1 * image.width, y1 * image.height, x2 * image.width, y2 * image.height], fill="red", width=3)

        # ✅ Draw joints
        for key, (x, y) in landmarks.items():
            draw.ellipse([
                x * image.width - 4, y * image.height - 4,
                x * image.width + 4, y * image.height + 4
            ], fill="lime")

    # ✅ Return image (modified or raw)
    img_io = BytesIO()
    image.save(img_io, "PNG")
    img_io.seek(0)
    return send_file(img_io, mimetype="image/png")

