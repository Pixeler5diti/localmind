from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from datetime import datetime
from model import query

def system_health_timeline(rows, system_status):
    """Correlate system events (errors, disk/cache spikes) with LLM usage patterns."""
    console = Console()
    
    timeline_table = Table(title="[bold]System Health & LLM Correlation[/bold]", show_header=True)
    timeline_table.add_column("Metric", style="cyan")
    timeline_table.add_column("Status", style="green")
    timeline_table.add_column("Impact", style="yellow")
    
    # Check disk health
    if 'disk' in system_status:
        for disk in system_status['disk']:
            if 'percent_used' in disk:
                percent = disk['percent_used']
                if percent > 90:
                    impact = "Critical - may slow down LLM responses"
                    status_color = "red"
                elif percent > 75:
                    impact = "Warning - monitor closely"
                    status_color = "yellow"
                else:
                    impact = "Healthy"
                    status_color = "green"
                
                timeline_table.add_row(
                    f"Disk {disk['path']}",
                    f"[{status_color}]{percent}%[/{status_color}]",
                    impact
                )
    
    # Check cache size
    if 'caches' in system_status and system_status['caches']:
        largest = system_status['caches'][0]
        size_bytes = largest['size_bytes']
        if size_bytes > 1000*1024*1024:  # 1GB
            impact = "Large cache - may impact disk I/O"
            status_color = "red"
        elif size_bytes > 500*1024*1024:  # 500MB
            impact = "Moderate - consider cleanup"
            status_color = "yellow"
        else:
            impact = "Healthy"
            status_color = "green"
        
        timeline_table.add_row(
            "Largest Cache",
            f"[{status_color}]{largest['size_human']}[/{status_color}]",
            impact
        )
    
    # Check system errors
    error_count = 0
    if 'errors' in system_status and isinstance(system_status['errors'], str):
        error_count = len(system_status['errors'].splitlines())
        if error_count > 20:
            impact = "High error rate - check system logs"
            status_color = "red"
        elif error_count > 10:
            impact = "Moderate errors - monitor"
            status_color = "yellow"
        else:
            impact = "Healthy"
            status_color = "green"
        
        timeline_table.add_row(
            "Recent Errors",
            f"[{status_color}]{error_count}[/{status_color}]",
            impact
        )
    
    # Correlate with LLM usage
    if rows:
        # Count interactions by time of day
        hours = {}
        for timestamp, mode, _, _, _, _, _ in rows:
            try:
                hour = datetime.fromisoformat(timestamp).hour
                hours[hour] = hours.get(hour, 0) + 1
            except:
                pass
        
        if hours:
            peak_hour = max(hours, key=hours.get)
            peak_count = hours[peak_hour]
            timeline_table.add_row(
                "Peak Activity",
                f"[bold cyan]{peak_hour}:00 ({peak_count} sessions)[/bold cyan]",
                "Most productive time"
            )
    
    # LLM-powered system health correlation and recommendations
    health_data = {
        "disk_status": f"Disk: {[d.get('percent_used', 'N/A') for d in system_status.get('disk', [])]}",
        "error_count": len(system_status.get('errors', '').splitlines()) if system_status.get('errors') else 0,
        "cache_size": system_status.get('caches', [{}])[0].get('size_human', 'N/A') if system_status.get('caches') else 'N/A'
    }
    
    correlation_prompt = (
        "Analyze this system health snapshot and provide a brief, actionable recommendation "
        "for optimizing system performance given the current state.\\n\\n"
        f"Disk usage: {health_data['disk_status']}\\n"
        f"Recent errors: {health_data['error_count']}\\n"
        f"Largest cache: {health_data['cache_size']}\\n\\n"
        "Provide 1-2 sentences with specific, practical advice. Avoid generic statements."
    )
    recommendation = query(correlation_prompt).strip()
    timeline_table.add_row(
        "[bold]LLM Recommendation[/bold]",
        recommendation,
        "Action"
    )
    
    console.print(Panel(timeline_table, border_style="blue", padding=(1, 2)))

# For integration: import and call system_health_timeline(rows, system_status) in dashboard.py
