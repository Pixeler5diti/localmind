"""
System Monitor mode (read-only).
Performs non-destructive checks on the local system and reports findings.
Designed for Fedora 42 / GNOME but uses generic checks where possible.
This mode NEVER performs destructive actions and will only read files and run
safe, read-only commands. It will never modify the system without explicit
user approval.
"""
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from model import query

def human_size(n):
    """Return human readable size."""
    for unit in ['B','KB','MB','GB','TB']:
        if n < 1024.0:
            return f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}PB"

def disk_report(paths=None):
    """Report disk usage for provided paths (defaults to / and home)."""
    if paths is None:
        paths = ['/', str(Path.home())]
    report = []
    for p in paths:
        try:
            usage = shutil.disk_usage(p)
            report.append({
                'path': p,
                'total': human_size(usage.total),
                'used': human_size(usage.used),
                'free': human_size(usage.free),
                'percent_used': round(usage.used/usage.total*100,1)
            })
        except Exception as e:
            report.append({'path': p, 'error': str(e)})
    return report

def find_large_cache_dirs(base_dirs=None, top_n=10):
    """Scan common cache directories and report largest entries (read-only)."""
    if base_dirs is None:
        base_dirs = [str(Path.home() / '.cache'), '/var/cache']
    entries = []
    for base in base_dirs:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            try:
                size = 0
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        size += os.path.getsize(fp)
                    except Exception:
                        pass
                entries.append((root, size))
            except Exception:
                pass
    entries.sort(key=lambda x: x[1], reverse=True)
    return [{'path': p, 'size_bytes': s, 'size_human': human_size(s)} for p, s in entries[:top_n]]

def journal_errors(max_lines=200):
    """Return recent journal errors (read-only)."""
    try:
        # Limit output to recent boot and errors only
        proc = subprocess.run([
            'journalctl', '-p', 'err', '-b', '--no-pager', '-n', str(max_lines)
        ], capture_output=True, text=True, timeout=8)
        if proc.returncode == 0:
            return proc.stdout.strip()
        else:
            return f"journalctl returned code {proc.returncode}: {proc.stderr.strip()}"
    except FileNotFoundError:
        return "journalctl not available on this system"
    except Exception as e:
        return f"Error running journalctl: {e}"

def dnf_cache_size():
    """Report size of dnf cache directories when available (Fedora-specific)."""
    paths = ['/var/cache/dnf']
    totals = []
    for p in paths:
        if os.path.exists(p):
            size = 0
            for root, dirs, files in os.walk(p):
                for f in files:
                    try:
                        size += os.path.getsize(os.path.join(root, f))
                    except Exception:
                        pass
            totals.append({'path': p, 'size_bytes': size, 'size_human': human_size(size)})
    return totals

def list_old_kernels(max_keep=3):
    """Attempt to list installed kernel versions (rpm-based). Read-only.
    Returns list of kernel versions sorted newest->oldest.
    """
    try:
        proc = subprocess.run(['rpm', '-q', 'kernel'], capture_output=True, text=True, timeout=5)
        if proc.returncode == 0:
            versions = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
            # rpm -q kernel returns names like 'kernel-6.8.5-200.fc38.x86_64'
            return versions
        else:
            return []
    except FileNotFoundError:
        return []
    except Exception:
        return []

def run_sysmon():
    """Run all checks and print a concise report. Read-only by design."""
    print("\n🔎 SYSTEM MONITOR REPORT (read-only)\n")
    print(f"Run at: {datetime.now().isoformat()}\n")

    # Disk usage
    print("== Disk Usage ==")
    for d in disk_report():
        if 'error' in d:
            print(f"- {d['path']}: Error: {d['error']}")
        else:
            print(f"- {d['path']}: {d['used']} used of {d['total']} ({d['percent_used']}%) - {d['free']} free")
    print("\n")

    # Large cache dirs
    print("== Largest cache directories (top entries) ==")
    caches = find_large_cache_dirs()
    if caches:
        for e in caches:
            print(f"- {e['path']}: {e['size_human']}")
    else:
        print("No cache directories found or accessible.")
    print("\n")

    # DNF/pacakge cache
    dnf = dnf_cache_size()
    if dnf:
        print("== DNF cache ==")
        for entry in dnf:
            print(f"- {entry['path']}: {entry['size_human']}")
        print("Hint: You can run 'sudo dnf clean all' if you want to free space (manual).")
    else:
        print("No DNF cache found or accessible.")
    print("\n")

    # Journal errors
    print("== Recent system errors (journalctl priority=err) ==")
    errors = journal_errors(200)
    if errors:
        print(errors[:4000])
        if len(errors) > 4000:
            print("\n...truncated (showing first 4000 chars). Use 'journalctl -p err -b' for full output.)")
    else:
        print("No recent errors found in journal or journalctl not available.")
    print("\n")

    # Old kernels
    kernels = list_old_kernels()
    if kernels:
        print("== Installed kernels ==")
        for k in kernels:
            print(f"- {k}")
        if len(kernels) > 3:
            print("Hint: You may consider keeping only the latest 2-3 kernels and removing older ones manually (requires sudo).")
    else:
        print("Could not determine installed kernel list (rpm not available or permission issue).")

    print("\n== Summary & LLM-Powered Recommendations ==")
    
    # Prepare health snapshot for LLM analysis
    root_usage = next((d for d in disk_report(['/'])), None)
    home_usage = next((d for d in disk_report([str(Path.home())])), None)
    
    health_data = {
        "root_percent": root_usage.get('percent_used', 'unknown') if root_usage else 'unknown',
        "home_percent": home_usage.get('percent_used', 'unknown') if home_usage else 'unknown',
        "largest_cache": f"{caches[0]['path']} ({caches[0]['size_human']})" if caches else "None found",
        "dnf_cache_size": dnf[0]['size_human'] if dnf else "None",
        "kernel_count": len(kernels),
        "error_count": len(errors.splitlines()) if errors else 0
    }
    
    # LLM-powered system health recommendation
    llm_prompt = (
        "Analyze this system health snapshot and provide specific, actionable recommendations "
        "(not generic) for optimization. Focus on the most impactful action first.\\n\\n"
        f"Disk: Root {health_data['root_percent']}% used, Home {health_data['home_percent']}% used\\n"
        f"Largest cache: {health_data['largest_cache']}\\n"
        f"DNF cache: {health_data['dnf_cache_size']}\\n"
        f"Kernels installed: {health_data['kernel_count']}\\n"
        f"Recent errors: {health_data['error_count']} entries\\n\\n"
        "Provide 2-3 concrete, specific recommendations. Avoid generic statements. "
        "Include bash commands if applicable."
    )
    
    try:
        llm_recommendation = query(llm_prompt).strip()
        print(llm_recommendation)
    except:
        # Fallback hopefully na use krna pade
        if root_usage and 'percent_used' in root_usage and root_usage['percent_used'] > 90:
            print(" Root partition >90% used — investigate large files and caches.")
        elif root_usage and root_usage['percent_used'] > 80:
            print(" Root partition >80% used — consider cleaning caches or logs.")
        else:
            print(" Disk usage looks healthy.")
        
        if caches and any(e['size_bytes'] > 500*1024*1024 for e in caches):
            print(" Large cache directories found (over 500MB). Consider cleanup.")
        else:
            print("Cache sizes are modest.")

    print("\nNote: This tool only inspects and reports. It will not modify anything without your explicit permission.")
