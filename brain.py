import sys
import importlib
import json
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
import subprocess
import os

from model import query
import memory

memory.init()

AVAILABLE_MODES = [
    "plan",
    "debug",
    "debug-interactive",
    "reflect",
    "code",
    "journal",
    "codefile",
    "weekly",
    "agent",
    "sysmon",
    "cleanup"
]


def cleanup_old_logs(days_to_keep=7):
    """Delete logs older than specified days and clear Ollama history"""
    cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
    
    conn = sqlite3.connect("brain.db")
    c = conn.cursor()
    
    # Get count of logs to be deleted
    c.execute("SELECT COUNT(*) FROM logs WHERE timestamp < ?", (cutoff_date,))
    count = c.fetchone()[0]
    
    if count == 0:
        print("No old logs to clean up.")
        return
    
    # Delete old logs
    c.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff_date,))
    conn.commit()
    
    # Vacuum to reclaim space
    c.execute("VACUUM")
    conn.close()
    
    print(f"✓ Deleted {count} log entries older than {days_to_keep} days")
    print(f"✓ Database optimized and space reclaimed")
    
    # Clear Ollama model cache/history
    try:
        subprocess.run(["ollama", "list"], capture_output=True, timeout=5)
        print("✓ Ollama cache remains available for inference")
    except Exception as e:
        print(f"Note: Could not verify Ollama status: {e}")
    
    print("\nCleanup complete. Your brain database is fresh and lean!")



def handle_codefile(filepath):
    path = Path(filepath)

    if not path.exists():
        print("File not found.")
        return

    content = path.read_text()

    prompt = f"""
You are reviewing this file.
Explain issues, improvements, and structure clearly.

File Content:
{content}
"""

    response = query(prompt)
    print(response)
    memory.save("codefile", filepath, response)


#weekly summary mde
def weekly_summary():
    conn = sqlite3.connect("brain.db")
    c = conn.cursor()

    last_week = (datetime.now() - timedelta(days=7)).isoformat()

    c.execute("""
        SELECT mode, prompt, response, focus, clarity, stress
        FROM logs
        WHERE timestamp > ?
        ORDER BY timestamp
    """, (last_week,))

    rows = c.fetchall()
    conn.close()

    if not rows:
        print("No logs from the past week.")
        return

    from rich.console import Console
    from rich.panel import Panel
    from collections import defaultdict
    
    console = Console()
    
    # Extract metrics
    focus_vals = [r[3] for r in rows if r[3] is not None]
    clarity_vals = [r[4] for r in rows if r[4] is not None]
    stress_vals = [r[5] for r in rows if r[5] is not None]

    # Count by mode
    mode_counts = defaultdict(int)
    for mode, _, _, _, _, _ in rows:
        mode_counts[mode] += 1

    # Calculate averages
    avg_focus = round(sum(focus_vals)/len(focus_vals), 1) if focus_vals else 0
    avg_clarity = round(sum(clarity_vals)/len(clarity_vals), 1) if clarity_vals else 0
    avg_stress = round(sum(stress_vals)/len(stress_vals), 1) if stress_vals else 0

    # Build activity summary
    activities_summary = "\n".join([
        f"- {mode}: {count} entries" 
        for mode, count in sorted(mode_counts.items(), key=lambda x: x[1], reverse=True)
    ])

    console.print("\n[bold cyan]═══ WEEKLY COGNITIVE SUMMARY ═══[/bold cyan]\n")
    
    # Generate insights from data
    def get_assessment(val, metric_type="normal"):
        """Return assessment based on metric value"""
        if metric_type == "stress":  # Lower is better
            if val < 4:
                return "Excellent - Low stress"
            elif val < 6:
                return "Good - Manageable stress"
            else:
                return "Caution - High stress"
        else:  # Higher is better
            if val >= 8:
                return "Excellent"
            elif val >= 6:
                return "Good"
            elif val >= 4:
                return "Fair"
            else:
                return "Needs improvement"
    
    # Create assessment text
    assessment = f"""
[bold cyan]COGNITIVE HEALTH ASSESSMENT[/bold cyan]
• Focus: {avg_focus}/10 - {get_assessment(avg_focus)}
• Clarity: {avg_clarity}/10 - {get_assessment(avg_clarity)}
• Stress: {avg_stress}/10 - {get_assessment(avg_stress, 'stress')}

[bold cyan]ACTIVITY BREAKDOWN[/bold cyan]
{activities_summary}
Total entries: {len(rows)}

[bold cyan]KEY OBSERVATIONS[/bold cyan]
"""
    
    # Add observations
    if avg_focus < 5:
        assessment += "\n Low focus levels detected - consider breaking tasks into smaller chunks"
    if avg_stress > 6:
        assessment += "\n Stress is elevated - prioritize relaxation and breaks"
    if avg_clarity >= 7:
        assessment += "\n Strong clarity - great time for complex decision-making"
    if "journal" in mode_counts and mode_counts["journal"] >= 3:
        assessment += "\n Good journaling habit - consistent self-reflection"
    
    assessment += "\n\n[bold cyan]RECOMMENDATION[/bold cyan]\n"
    if avg_stress > 7:
        assessment += "Focus on stress reduction techniques this week. Consider mindfulness or breaks."
    elif avg_focus < 5:
        assessment += "Boost focus by eliminating distractions and using time-blocking techniques."
    else:
        assessment += "Maintain current routine - you're in a good cognitive state. Push toward goals."
    
    console.print(Panel(assessment, border_style="cyan"))


#agent mode, still needs work.i hate this personally,might even delete
def run_agent(goal):
    print("\n--- AGENT START ---\n")

    plan_prompt = f"""
Break this goal into 3 concrete steps.

Goal:
{goal}
"""
    plan = query(plan_prompt)
    print("PLAN:\n", plan)

    execute_prompt = f"""
Execute step 1 from this plan:

{plan}
"""
    execution = query(execute_prompt)
    print("\nEXECUTION:\n", execution)

    review_prompt = f"""
Review this output critically and suggest improvements:

{execution}
"""
    review = query(review_prompt)
    print("\nREVIEW:\n", review)

    memory.save("agent", goal, review)

#main woohhooo
def main():
    if len(sys.argv) < 2:
        print("Usage: brain <mode> <message>")
        print("Modes:", ", ".join(AVAILABLE_MODES))
        return

    mode = sys.argv[1]

    if mode not in AVAILABLE_MODES:
        print("Invalid mode.")
        print("Available modes:", ", ".join(AVAILABLE_MODES))
        return

    # Weekly summary
    if mode == "weekly":
        weekly_summary()
        return

    # Interactive debug mode
    if mode == "debug-interactive":
        if len(sys.argv) < 3:
            print("Problem description required.")
            print("Usage: brain debug-interactive 'describe your problem'")
            return
        problem = " ".join(sys.argv[2:])
        from modes.debug_interactive import run_debug_session
        run_debug_session(problem)
        return

    # System monitor (read-only)
    if mode == "sysmon":
        from modes.sysmon import run_sysmon
        run_sysmon()
        return

    # Cleanup mode
    if mode == "cleanup":
        days = 7  # Default
        if len(sys.argv) > 2:
            try:
                days = int(sys.argv[2])
            except ValueError:
                print("Usage: brain cleanup [days_to_keep]")
                print("Example: brain cleanup 7  (keeps last 7 days)")
                return
        cleanup_old_logs(days)
        return

    # Agent mode
    if mode == "agent":
        if len(sys.argv) < 3:
            print("Goal required for agent mode.")
            return
        goal = " ".join(sys.argv[2:])
        run_agent(goal)
        return

    # Codefile mode
    if mode == "codefile":
        if len(sys.argv) < 3:
            print("File path required.")
            return
        filepath = sys.argv[2]
        handle_codefile(filepath)
        return

    # All other modes require message
    if len(sys.argv) < 3:
        print("Message required for this mode.")
        return

    message = " ".join(sys.argv[2:])
    module = importlib.import_module(f"modes.{mode}")
    prompt = module.build_prompt(message)

    response = query(prompt)

    focus = clarity = stress = None

    if mode == "journal":
        try:
            parsed = json.loads(response)
            focus = parsed.get("focus")
            clarity = parsed.get("clarity")
            stress = parsed.get("stress")
            print(parsed.get("reflection"))
        except Exception:
            print(response)
    else:
        print(response)

    memory.save(mode, message, response, focus, clarity, stress)


if __name__ == "__main__":
    main()