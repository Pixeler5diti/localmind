from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from collections import Counter
import re
from model import query

def llm_interaction_analytics(rows):
    """Generate LLM interaction analytics: topics, streaks, response lengths, common questions."""
    console = Console()
    
    if not rows:
        console.print("[dim]No LLM interactions to analyze.[/dim]")
        return
    
    analytics_table = Table(title="[bold]LLM Interaction Analytics[/bold]", show_header=True)
    analytics_table.add_column("Metric", style="cyan")
    analytics_table.add_column("Value", style="green")
    
    # Extract data
    prompts = [r[2] for r in rows if r[2]]
    responses = [r[3] for r in rows if r[3]]
    modes = [r[1] for r in rows]
    
    # Most asked topics 
    if prompts:
        prompt_sample = "\n".join(prompts[:10])  # Sample of prompts
        topic_prompt = (
            "Analyze these recent LLM prompts and identify 3 main topics or themes the user is focused on. "
            "Be specific and concise. Return only the 3 topics as a comma-separated list.\n\n"
            f"{prompt_sample}"
        )
        topics_str = query(topic_prompt).strip()
    else:
        topics_str = "N/A"
    analytics_table.add_row("Top Topics", topics_str)
    
    # Longest conversation streak (consecutive same mode)
    if modes:
        max_streak = 1
        current_streak = 1
        for i in range(1, len(modes)):
            if modes[i] == modes[i-1]:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1
        analytics_table.add_row("Longest Streak", f"{max_streak} sessions")
    
    # Average response length
    avg_response_len = round(sum(len(r) for r in responses) / len(responses), 0) if responses else 0
    analytics_table.add_row("Avg Response Length", f"{int(avg_response_len)} chars")
    
    # Most common question type (by mode)
    mode_counts = Counter(modes)
    most_common_mode = mode_counts.most_common(1)[0][0] if mode_counts else "N/A"
    analytics_table.add_row("Primary Focus", f"{most_common_mode} ({mode_counts[most_common_mode]}x)")
    
    # Conversation pattern insights (LLM-powered)
    if len(prompts) > 0:
        pattern_prompt = (
            "Looking at this user's conversation history (prompts and responses), "
            "what is their typical conversation pattern or style? Be concise (1-2 sentences).\n\n"
            "Recent prompts:"
            + "\n".join([f"- {p[:80]}" for p in prompts[-5:]])
            + "\n\nRecent responses (lengths):" 
            + ", ".join([str(len(r)) for r in responses[-5:]])
        )
        pattern_str = query(pattern_prompt).strip()
        analytics_table.add_row("Conversation Pattern", pattern_str)
    
    # Shortest and longest prompts
    shortest_prompt = min(prompts, key=len) if prompts else "N/A"
    longest_prompt = max(prompts, key=len) if prompts else "N/A"
    analytics_table.add_row("Shortest Question", shortest_prompt[:50] + ("..." if len(shortest_prompt) > 50 else ""))
    analytics_table.add_row("Longest Question", longest_prompt[:50] + ("..." if len(longest_prompt) > 50 else ""))
    
    # Total interactions
    analytics_table.add_row("Total Interactions", str(len(rows)))
    
    console.print(Panel(analytics_table, border_style="magenta", padding=(1, 2)))

# For integration: import and call llm_interaction_analytics(rows) in dashboard.py
