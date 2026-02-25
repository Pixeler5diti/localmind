from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import json

from dashboard_insights import smart_insights
from dashboard_trends import visual_trends
from dashboard_analytics import llm_interaction_analytics
from dashboard_timeline import system_health_timeline
from dashboard_alert import print_top_system_alert


console = Console()

# --- SYSTEM STATUS (from sysmon) ---

# Import sysmon helpers using relative import
try:
    from modes import sysmon
except ImportError:
    sysmon = None

def get_system_status():
    """Get a summary of system health using sysmon helpers."""
    if sysmon is None:
        return {'error': 'sysmon module not found'}
    try:
        disk = sysmon.disk_report()
        caches = sysmon.find_large_cache_dirs()
        dnf = sysmon.dnf_cache_size()
        errors = sysmon.journal_errors(20)
        kernels = sysmon.list_old_kernels()
        status = {
            'disk': disk,
            'caches': caches,
            'dnf': dnf,
            'errors': errors,
            'kernels': kernels,
        }
        return status
    except Exception as e:
        return {'error': str(e)}

def print_system_status(status):
    """Print a concise system status panel."""
    sys_table = Table(title="[bold]System Health[/bold]", show_header=False, box=None)
    if 'error' in status:
        sys_table.add_row("[red]System check error[/red]", status['error'])
    else:
        # Disk
        for d in status['disk']:
            if 'error' in d:
                sys_table.add_row(f"Disk {d['path']}", f"[red]{d['error']}[/red]")
            else:
                sys_table.add_row(f"Disk {d['path']}", f"{d['used']} used / {d['total']} ({d['percent_used']}%)")
        # Cache
        if status['caches']:
            largest = status['caches'][0]
            sys_table.add_row("Largest Cache", f"{largest['path']} ({largest['size_human']})")
        # DNF
        if status['dnf']:
            sys_table.add_row("DNF Cache", f"{status['dnf'][0]['size_human']}")
        # Errors
        if status['errors'] and isinstance(status['errors'], str):
            err_lines = status['errors'].splitlines()
            if err_lines:
                sys_table.add_row("Recent Errors", err_lines[0][:60] + ("..." if len(err_lines[0]) > 60 else ""))
        # Kernels
        if status['kernels'] and len(status['kernels']) > 3:
            sys_table.add_row("Old Kernels", f"{len(status['kernels'])} installed")
    console.print(Panel(sys_table, border_style="red", padding=(1, 2)))


conn = sqlite3.connect("brain.db")
c = conn.cursor()

# gettin all logs from the past
last_week = (datetime.now() - timedelta(days=7)).isoformat()
c.execute("""
    SELECT timestamp, mode, prompt, response, focus, clarity, stress
    FROM logs
    WHERE timestamp > ?
    ORDER BY timestamp DESC
""", (last_week,))

rows = c.fetchall()
conn.close()

if not rows:
    console.print("[red]No logs from the past week.[/red]")
    exit()

# Extract metrics
focus_vals = [r[4] for r in rows if r[4] is not None]
clarity_vals = [r[5] for r in rows if r[5] is not None]
stress_vals = [r[6] for r in rows if r[6] is not None]

# Count by mode
mode_counts = defaultdict(int)
for _, mode, _, _, _, _, _ in rows:
    mode_counts[mode] += 1

# Calculate averages
avg_focus = round(sum(focus_vals)/len(focus_vals), 1) if focus_vals else 0
avg_clarity = round(sum(clarity_vals)/len(clarity_vals), 1) if clarity_vals else 0
avg_stress = round(sum(stress_vals)/len(stress_vals), 1) if stress_vals else 0

# Health indicators
def get_health_color(value, invert=False):
    if invert:  # For stress (lower is better)
        if value < 4:
            return "green"
        elif value < 6:
            return "yellow"
        else:
            return "red"
    else:  # For focus/clarity (higher is better)
        if value >= 7:
            return "green"
        elif value >= 5:
            return "yellow"
        else:
            return "red"

def get_bar(value, max_val=10):
    filled = int((value / max_val) * 20)
    return "█" * filled + "░" * (20 - filled)


# --- DASHBOARD TITLE ---
console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
console.print("[bold cyan]    PERSONAL AI DASHBOARD[/bold cyan]")
console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]\n")

# Time period
week_start = (datetime.now() - timedelta(days=7)).strftime("%B %d")
week_end = datetime.now().strftime("%B %d, %Y")
console.print(f"[dim]Report Period: {week_start} - {week_end} | Total Interactions: {len(rows)}[/dim]\n")

# --- WOW FACTOR FEATURES (Primary) ---


# 1. System Status
status = get_system_status()
print_system_status(status)

# 1a. Top System Alert (LLM-powered)
if status.get('errors'):
    print_top_system_alert(status['errors'])

# 2. Smart Insights & Recommendations
smart_insights(rows, status)

# 3. Visual Trends & Anomalies
disk_percentages = [d['percent_used'] for d in status.get('disk', []) if 'percent_used' in d]
visual_trends(focus_vals, clarity_vals, stress_vals, disk_percentages)

# 4. LLM Interaction Analytics
llm_interaction_analytics(rows)

# 5. System Health Timeline
system_health_timeline(rows, status)

# --- SECONDARY: Cognitive Health Assessment (optional) ---
console.print("\n[bold yellow]Secondary: Cognitive Health (Optional)[/bold yellow]")
metrics_table = Table(title="[bold]Core Metrics[/bold]", show_header=False, box=None)
metrics_table.add_row("[bold]Focus[/bold]", 
    f"[{get_health_color(avg_focus)}]{avg_focus}/10[/{get_health_color(avg_focus)}]",
    f"  {get_bar(avg_focus)}")
metrics_table.add_row("[bold]Clarity[/bold]",
    f"[{get_health_color(avg_clarity)}]{avg_clarity}/10[/{get_health_color(avg_clarity)}]",
    f"  {get_bar(avg_clarity)}")
metrics_table.add_row("[bold]Stress[/bold]",
    f"[{get_health_color(avg_stress, invert=True)}]{avg_stress}/10[/{get_health_color(avg_stress, invert=True)}]",
    f"  {get_bar(avg_stress)}")

console.print(Panel(metrics_table, border_style="cyan", padding=(1, 2)))

# Activity Breakdown (Secondary)
activity_table = Table(title="[bold]Activity Breakdown[/bold]", show_header=True)
activity_table.add_column("Mode", style="magenta")
activity_table.add_column("Count", style="cyan", justify="right")
activity_table.add_column("Percentage", style="green")

total_activities = sum(mode_counts.values())
for mode, count in sorted(mode_counts.items(), key=lambda x: x[1], reverse=True):
    percentage = round((count / total_activities) * 100, 1)
    activity_table.add_row(mode, str(count), f"{percentage}%")

console.print(Panel(activity_table, border_style="magenta", padding=(1, 2)))

# Recent entries preview (Secondary)
console.print("\n[bold]Recent Activity[/bold]")
recent_table = Table(show_header=True)
recent_table.add_column("Time", style="dim")
recent_table.add_column("Mode", style="magenta")
recent_table.add_column("Prompt", style="white")

for timestamp, mode, prompt, _, _, _, _ in rows[:5]:
    ts = datetime.fromisoformat(timestamp).strftime("%m/%d %H:%M")
    prompt_preview = (prompt[:40] + "...") if len(prompt) > 40 else prompt
    recent_table.add_row(ts, mode, prompt_preview)

console.print(Panel(recent_table, border_style="green", padding=(1, 2)))


# --- WEEKLY SUMMARY FUNCTION --- very important 
def weekly():
    """Show a comprehensive summary of system, LLM, and user activity for the week."""
    console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]    WEEKLY SUMMARY[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]\n")
    
    # All primary features
    status = get_system_status()
    print_system_status(status)
    smart_insights(rows, status)
    disk_percentages = [d['percent_used'] for d in status.get('disk', []) if 'percent_used' in d]
    visual_trends(focus_vals, clarity_vals, stress_vals, disk_percentages)
    llm_interaction_analytics(rows)
    system_health_timeline(rows, status)
    
    # Secondary: Cognitive health
    console.print("\n[bold yellow]Secondary: Cognitive Health (Optional)[/bold yellow]")
    metrics_table = Table(title="[bold]Core Metrics[/bold]", show_header=False, box=None)
    metrics_table.add_row("[bold]Focus[/bold]", 
        f"[{get_health_color(avg_focus)}]{avg_focus}/10[/{get_health_color(avg_focus)}]",
        f"  {get_bar(avg_focus)}")
    metrics_table.add_row("[bold]Clarity[/bold]",
        f"[{get_health_color(avg_clarity)}]{avg_clarity}/10[/{get_health_color(avg_clarity)}]",
        f"  {get_bar(avg_clarity)}")
    metrics_table.add_row("[bold]Stress[/bold]",
        f"[{get_health_color(avg_stress, invert=True)}]{avg_stress}/10[/{get_health_color(avg_stress, invert=True)}]",
        f"  {get_bar(avg_stress)}")
    console.print(Panel(metrics_table, border_style="cyan", padding=(1, 2)))
    console.print("\n[dim]End of Weekly Summary.\n")