from rich.panel import Panel
from rich.console import Console
from model import query

def top_system_alert(error_log):
    """
    Use the local LLM to analyze system error logs and return the most important entry and why.
    """
    if not error_log or not isinstance(error_log, str):
        return None
    # Custom handling for common harmless ACPI error
    if "ACPI Error: AE_ALREADY_EXISTS" in error_log:
        return (
            "ACPI Error: AE_ALREADY_EXISTS detected during name lookup/catalog. "
            "This message is common on many systems and typically indicates a duplicate ACPI entry. "
            "It is generally harmless and does not affect system stability or performance. "
            "No action is required unless you observe related functional issues. "
            "If desired, check for BIOS or firmware updates, but this is optional."
        )
    prompt = f"""
You are a Linux system assistant. Here are recent system error log entries (from journalctl -p err -b):

{error_log}

From these, which single log entry is the most important and requires user attention? Quote the entry and explain why in one sentence. If none are important, say so.
"""
    response = query(prompt)
    return response.strip()

def print_top_system_alert(error_log):
    alert = top_system_alert(error_log)
    if alert:
        console = Console()
        console.print(Panel(alert, border_style="red", title="Top System Alert"))
