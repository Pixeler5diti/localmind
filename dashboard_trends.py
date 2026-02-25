from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from model import query

def get_sparkline(values, width=30):
    """Generate a simple ASCII sparkline from a list of values."""
    if not values:
        return "No data"
    
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val if max_val != min_val else 1
    
    # Sparkline characters: ▁ ▂ ▃ ▄ ▅ ▆ ▇ █
    spark_chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    
    spark = ""
    for v in values[-width:]:  # Last 'width' values
        normalized = (v - min_val) / range_val if range_val > 0 else 0
        idx = min(int(normalized * 7), 7)
        spark += spark_chars[idx]
    
    return spark

def visual_trends(focus_vals, clarity_vals, stress_vals, disk_percentages):
    """Display visual trends with LLM-powered interpretation and anomaly detection."""
    console = Console()
    
    trends_table = Table(title="[bold]Weekly Trends & Insights[/bold]", show_header=False, box=None)
    
    # Prepare trend data for LLM analysis
    trend_data = {
        "focus": focus_vals[-7:] if focus_vals else [],
        "clarity": clarity_vals[-7:] if clarity_vals else [],
        "stress": stress_vals[-7:] if stress_vals else [],
        "disk": disk_percentages[-7:] if disk_percentages else []
    }
    
    # LLM-powered trend analysis
    if any(trend_data.values()):
        trend_prompt = (
            "Analyze these weekly metrics and provide insight on patterns and anomalies.\\n\\n"
            f"Focus scores: {trend_data['focus']}\\n"
            f"Clarity scores: {trend_data['clarity']}\\n"
            f"Stress levels: {trend_data['stress']}\\n"
            f"Disk usage %: {trend_data['disk']}\\n\\n"
            "Provide 3-4 concise observations about trends and any anomalies. Be specific, not generic."
        )
        llm_insights = query(trend_prompt).strip()
        trends_table.add_row("[bold]LLM Insights[/bold]", llm_insights)
    
    # Visual sparklines for quick reference
    if focus_vals:
        sparkline = get_sparkline(focus_vals, 30)
        trends_table.add_row("[cyan]Focus[/cyan]", sparkline)
    
    if clarity_vals:
        sparkline = get_sparkline(clarity_vals, 30)
        trends_table.add_row("[green]Clarity[/green]", sparkline)
    
    if stress_vals:
        sparkline = get_sparkline(stress_vals, 30)
        color = "red" if stress_vals[-1] > 70 else "yellow" if stress_vals[-1] > 50 else "green"
        trends_table.add_row(f"[{color}]Stress[/{color}]", sparkline)
    
    if disk_percentages:
        sparkline = get_sparkline(disk_percentages, 30)
        color = "red" if disk_percentages[-1] > 85 else "yellow" if disk_percentages[-1] > 70 else "green"
        trends_table.add_row(f"[bold {color}]Disk%[/bold {color}]", sparkline)
    
    console.print(Panel(trends_table, border_style="cyan", padding=(1, 2)))

# For integration: import and call visual_trends(focus_vals, clarity_vals, stress_vals, disk_percentages) in dashboard.py
