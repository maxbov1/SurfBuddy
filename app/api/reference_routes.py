
from flask import Blueprint, jsonify
from app.references.reference_data import SURF_MANEUVERS, SURF_TECHNIQUES
from app.models.reference_models import SurfManeuver, SurfTechnique

reference_bp = Blueprint('reference', __name__)

@reference_bp.route('/', methods=['GET'])
def get_references():
    references = []

    # Validate maneuvers
    for maneuver in SURF_MANEUVERS:
        validated = SurfManeuver(**maneuver)
        references.append(validated.dict())

    # Validate techniques
    for technique in SURF_TECHNIQUES:
        # Techniques don't have frames yet! Let's patch dummy frames if missing
        if 'frames' not in technique:
            technique['frames'] = ["Start", "Middle", "End"]

        validated = SurfTechnique(**technique)
        references.append(validated.dict())

    return jsonify(references), 200

