from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def evaluate_interview(text):
    prompt = f"""
Evaluate this candidate interview:

{text}

Give:
- Accuracy (0-10)
- Relevance (0-10)
- Communication (0-10)
- Notes
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content


def generate_offer(name, role):
    prompt = f"""
Write offer email for {name} for role {role}.
Include strengths and improvements.
"""

    res = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content