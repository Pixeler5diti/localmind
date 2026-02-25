from rich.panel import Panel
from rich.console import Console
from collections import Counter
import re
from itertools import groupby
from model import query

def smart_insights(rows, system_status):
    console = Console()
    insights = []
    # Productivity suggestion
    times = [r[0] for r in rows]
    hours = [int(re.search(r'T (\d+):', t).group(1)) if re.search(r'T (\d+):', t) else 0 for t in times]
    if hours:
        peak_hour = max(set(hours), key=hours.count)
        insights.append(f"You are most active around {peak_hour}:00.")
    # Disk usage
    if 'disk' in system_status:
        for d in system_status['disk']:
            if d.get('percent_used', 0) > 90:
                insights.append("Disk usage is high (>90%). Consider cleaning up.")
    # Cache (removed to avoid duplication with system health section)
    # Error summary using LLM for intelligent analysisor intelligent analysis
    if 'errors' in system_status and isinstance(system_status['errors'], str):
        err_lines = system_status['errors'].splitlines()
        if len(err_lines) > 0:
            # Limit to first 30 lines for brevity
            err_context = "\n".join(err_lines[:30])
            prompt = (
                "You are a Linux system assistant analyzing recent system error logs (from journalctl -p err -b).\n\n"
                "Here are the recent error entries:\n\n"
                f"{err_context}\n\n"
                "Write a concise, technical summary of the main issues or patterns. "
                "Distinguish between common harmless errors and real problems. "
                "Keep it to 2-3 sentences. Avoid generic statements."
            )
            summary = query(prompt).strip()
            if summary:
                insights.append(summary)
    # LLM streak
    modes = [r[1] for r in rows]
    streak = max([len(list(g)) for k, g in groupby(modes)]) if modes else 0
    if streak > 3:
        insights.append(f"Longest mode streak: {streak} sessions.")
    # Motivational nudge
    if not insights:
        insights.append("Keep up the good work! No major issues detected.")
    console.print(Panel("\n".join(insights), border_style="blue", title="Smart Insights & Recommendations"))
