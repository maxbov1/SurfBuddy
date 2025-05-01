import logging
from flask import Blueprint, request, jsonify
from app.services.coach import ask_surf_coach
from app.references.reference_data import SURF_MANEUVERS

def get_maneuver_context(maneuver_name):
    for maneuver in SURF_MANEUVERS:
        if maneuver['name'].lower() == maneuver_name.lower():
            return maneuver
        return None
coach_bp = Blueprint("coach", __name__)
@coach_bp.route("/", methods=["POST"])
def surf_coach():
    data = request.get_json()
    maneuver_name = data.get("maneuver_name")
    feedback_summary = data.get("feedback_summary")
    user_message = data.get("user_message")
    maneuver_context = data.get("maneuver_context")  # ✅ typo fix: 'manever' → 'maneuver'

    # ✅ Format a clean context prompt
    full_prompt = {
        "maneuver_info": maneuver_context,
        "feedback_summary": feedback_summary
    }

    # 🔁 Ask LLM for feedback
    try:
        feedback = ask_surf_coach(full_prompt, user_message)
    except Exception as e:
        return jsonify({"error": f"LLM call failed: {str(e)}"}), 500

    return jsonify({
        "llm_feedback": feedback,
        "context_for_llm": full_prompt
    }), 200
