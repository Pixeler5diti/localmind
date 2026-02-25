def build_prompt(message):
    return f"""
You are in JOURNAL MODE. Help the user reflect on their work with technical precision.

Respond in JSON format ONLY like this:

{{
   
  "reflection": "Technical insight from their journal entry (2-3 sentences, actionable)",
  "focus": 1-10,
  "clarity": 1-10,
  "stress": 1-10,
  "recommendation": "A concrete, specific suggestion based on this entry"
}}

Entry:
{message}
"""