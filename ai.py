import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

client = Groq(api_key=GROQ_API_KEY)

def generate_question(topic="Game Theory", difficulty="Medium", past_scenarios=None):
    if past_scenarios is None:
        past_scenarios = []
        
    history_str = "\n".join([f"- {s}" for s in past_scenarios])
    
    prompt = f"""
    You are an expert game theorist designing a strategic multiplayer quiz.
    Create a highly engaging scenario based on the topic: '{topic}' with difficulty '{difficulty}'.
    
    If the topic is generic, aggressively vary the models. Base the situation on advanced concepts such as Stag Hunt, Hawk-Dove, Centipede Game, Volunteer's Dilemma, Matching Pennies, or Battle of the Sexes.
    
    PREVIOUS ROUNDS PLAYED (YOU ABSOLUTELY MUST NOT REPEAT THESE CONCEPTS):
    {history_str if history_str else "None yet. Create a fresh strategic scenario!"}
    
    READABILITY RULES: 
    Write the scenario description concisely using 2-3 short, extremely readable paragraphs. Avoid massive dense blocks of text. The player only has 60 seconds to read and decide!
    
    Provide 4 multiple-choice options (A, B, C, D) for the player.
    Identify the BEST strategic choice (e.g. Nash equilibrium, dominant strategy, or optimal cooperative play).
    Allocate points: The best strategy gets 10 points, a reasonable but suboptimal strategy gets 5 points, and bad strategies get 0.
    
    You MUST return ONLY valid JSON format. DO NOT use markdown code blocks like ```json . Just raw JSON.
    Format exactly like this:
    {{
        "scenario": "Short description of the strategic situation...",
        "options": {{
            "A": "Strategy 1...",
            "B": "Strategy 2...",
            "C": "Strategy 3...",
            "D": "Strategy 4..."
        }},
        "best_option": "B",
        "points": {{
            "A": 0,
            "B": 10,
            "C": 5,
            "D": 0
        }},
        "explanation": "Strategic explanation of why this is the highest payoff choice based on Game Theory..."
    }}
    """
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a highly creative JSON-only response bot. Never return markdown formatting outside the raw JSON object."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.85, # Increased for higher randomness and creativity
            max_tokens=900,
        )
        
        response_text = completion.choices[0].message.content.strip()
        
        # Cleanup markdown wrapping if the AI hallucinates it
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        data = json.loads(response_text)
        return data
        
    except Exception as e:
        print(f"Error generating from Groq: {e}")
        return {
            "scenario": "Emergency fallback scenario: You and a partner are arrested. If you both stay silent, you get 1 year. Ratting implies varying consequences.",
            "options": {
                "A": "Stay silent (Cooperate)",
                "B": "Rat him out (Defect)",
                "C": "Confess to a completely unrelated crime",
                "D": "Demand your lawyer and say nothing"
            },
            "best_option": "B",
            "points": {"A": 5, "B": 10, "C": 0, "D": 5},
            "explanation": "Defecting is the dominant strategy to minimize maximum loss (Nash Equilibrium)."
        }
