def build_prompt(message):
    return f"""
You are in PLANNING MODE.
Break problems into clear, actionable steps.
Be structured, practical, and technical.

Provide:
1. High-level approach (1-2 sentences)
2. Step-by-step plan (numbered, 5-7 steps)
3. Potential blockers or risks (2-3 bullet points)
4. Success criteria (what "done" looks like)

Task:
{message}
"""
