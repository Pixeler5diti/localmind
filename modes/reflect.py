def build_prompt(message):
    return f"""
You are in REFLECTION MODE.
Help analyze behavior patterns with technical depth. Identify actionable patterns and growth areas.
Be insightful, specific, and constructive. Avoid generic statements.

Provide:
1. Key pattern or insight (1-2 sentences)
2. Underlying cause or trend (1 sentence)
3. Specific, actionable next step (1 sentence)

Reflection:
{message}
"""
