import os
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st

def get_env(key):
    return st.secrets.get(key) or os.getenv(key)

load_dotenv()

client = OpenAI(
    client = OpenAI(
    api_key=get_env("API_KEY"),
    base_url="https://api.deepseek.com"
)


def generate_requirements(requirements_text):
    prompt = f"""
You are a senior requirements engineer.

Your task is to transform raw input into high-quality:
- Requirements
- User Stories
- Test Cases

----------------------------------------
STRICT RULES
----------------------------------------

GENERAL:
- Max 3 requirements
- Max 6 user stories
- Max 6 test cases
- Output MUST be valid JSON only (no explanations)

REQUIREMENTS:
- MUST use "SHALL"
- One requirement = one responsibility
- No "and", "or", "before", "after"
- No vague words (e.g. user-friendly, fast, simple)
- Must be testable
- No implementation details (no "how")

USER STORIES:
- Format: As a [user], I want [action], so that [benefit]

PRIORITY:
You MUST assign EXACTLY one of:
- High → security, authentication, blocking features
- Medium → important but not critical
- Low → optional / enhancement

TEST CASES:
- Must include:
  - precondition
  - steps (STRICT FORMAT)
  - expected

STEP FORMAT (MANDATORY):
- Alternate EXACTLY between Action and Expected

Example:
A1: Enter email
E1: Email field accepts input
A2: Enter password
E2: Password is masked
A3: Click login
E3: User is authenticated

RULES:
- NO "1. 2. 3."
- NO paragraphs
- MUST follow A/E pattern
- MUST be realistic and testable

----------------------------------------
INPUT:
{requirements_text}
----------------------------------------

OUTPUT FORMAT:
{{
  "requirements": [
    {{
      "title": "",
      "description": "",
      "priority": "High"
    }}
  ],
  "user_stories": [
    {{
      "title": "",
      "description": "",
      "priority": "Medium"
    }}
  ],
  "test_cases": [
    {{
      "title": "",
      "precondition": "",
      "steps": "",
      "expected": "",
      "priority": "Low"
    }}
  ]
}}
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content