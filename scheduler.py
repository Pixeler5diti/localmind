#!/usr/bin/env python3
"""
Scheduler for automatic cleanup of old brain logs.
This can be run as a cron job or background service.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

BRAIN_DIR = Path(__file__).parent
LOG_FILE = BRAIN_DIR / ".cleanup.log"
KEEP_DAYS = 7

def log_message(msg):
    """Log cleanup operations"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {msg}\n"
    print(log_entry.strip())
    
    # Append to log file
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def run_cleanup():
    """Execute the cleanup routine"""
    try:
        result = subprocess.run(
            ["python", str(BRAIN_DIR / "brain.py"), "cleanup", str(KEEP_DAYS)],
            cwd=str(BRAIN_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            log_message("✓ Weekly cleanup completed successfully")
            for line in result.stdout.split("\n"):
                if line.strip():
                    log_message(f"  {line}")
        else:
            log_message(f"✗ Cleanup failed: {result.stderr}")
            return False
        
        return True
    
    except subprocess.TimeoutExpired:
        log_message("✗ Cleanup timed out")
        return False
    except Exception as e:
        log_message(f"✗ Error during cleanup: {e}")
        return False

def setup_cron():
    """Print instructions for setting up cron job"""
    print("\n" + "="*60)
    print("AUTOMATIC CLEANUP SETUP")
    print("="*60)
    print("\nTo enable automatic weekly cleanup, add this to your crontab:")
    print("\n  crontab -e")
    print("\nThen add this line (runs every Sunday at 2 AM):")
    print(f"\n  0 2 * * 0 python {BRAIN_DIR}/scheduler.py")
    print("\nOr for other frequencies:")
    print(f"  # Daily at 3 AM:     0 3 * * * python {BRAIN_DIR}/scheduler.py")
    print(f"  # Every Monday 1 AM: 0 1 * * 1 python {BRAIN_DIR}/scheduler.py")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        setup_cron()
    else:
        run_cleanup()
#the most useless feature of this system till now.