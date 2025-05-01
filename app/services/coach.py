import openai
import os

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_surf_coach(maneuver_info, feedback_summary):
    """
    Uses OpenAI GPT to generate personalized surf coaching advice.
    """
    system_prompt = (
        "You are a professional surf coach. Provide personalized, constructive advice "
        "to help surfers improve their maneuvers. Use the maneuver details and feedback summary to "
        "give targeted suggestions for improvement."
    )

    user_prompt = f"""
Here is information about the maneuver the user is working on:
{maneuver_info}

Here is a summary of the pose analysis results:
{feedback_summary}

Please provide:
1. Constructive feedback on what the surfer did well and what they can improve.
2. Suggested drills or practice routines specific to this maneuver (e.g., skate training, balance board, water practice).
3. YouTube tutorial keywords or video types the surfer could search for (instead of recommending local files).
4. Mental training tips to build confidence, focus, or decision-making in waves.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"❌ Error generating coaching feedback: {str(e)}"

