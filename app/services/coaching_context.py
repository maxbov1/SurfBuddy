# services/coaching_context.py

import logging

# Thresholds for angle difference feedback
ANGLE_THRESHOLDS = {
    "minor": 15,
    "moderate": 30,
    "major": 60
}

def interpret_angle_difference(diff):
    """Classify angle difference into a coaching category."""
    if diff < ANGLE_THRESHOLDS["minor"]:
        return "✅ Good alignment"
    elif diff < ANGLE_THRESHOLDS["moderate"]:
        return "⚠️ Slight deviation"
    elif diff < ANGLE_THRESHOLDS["major"]:
        return "❗ Moderate deviation"
    else:
        return "❌ Major issue"

def generate_coaching_context(pose_analysis):
    """
    Converts raw pose analysis into structured coaching feedback.
    Input:
        pose_analysis: dict containing per-stage user_pose, pro_pose, similarity_score, angle_differences, etc.
    Output:
        coaching_context: dict of text-based insights for each stage
    """
    context = {}

    for stage, data in pose_analysis.items():
        stage_feedback = {
            "summary": "",
            "joint_feedback": {}
        }

        # High-level summary based on similarity score
        score = data.get("similarity_score", float("inf"))
        if score < 20:
            stage_feedback["summary"] = "Excellent form 💯"
        elif score < 40:
            stage_feedback["summary"] = "Decent alignment – room to improve 👌"
        elif score < 60:
            stage_feedback["summary"] = "Notable form mismatches – check key joints 👀"
        else:
            stage_feedback["summary"] = "Major form differences – review this stage carefully 🚨"

        # Angle-level feedback
        angle_diff = data.get("angle_differences", {})
        for joint, angles in angle_diff.items():
            joint_msg = interpret_angle_difference(angles["difference"])
            stage_feedback["joint_feedback"][joint] = {
                "user_angle": round(angles["user_angle"], 1),
                "pro_angle": round(angles["pro_angle"], 1),
                "difference": round(angles["difference"], 1),
                "assessment": joint_msg
            }

        context[stage] = stage_feedback

    logging.info("✅ Coaching context generated.")
    return context

