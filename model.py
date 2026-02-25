import subprocess
import tempfile
import os

MODEL = "qwen-lite"

def query(prompt):
    """
    Query ollama with a prompt using file-based input to avoid subprocess issues.
    """
    # Write prompt to temp file to avoid stdin buffering issues
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(prompt)
        temp_path = f.name
    
    try:
        # Use shell with file redirection instead of stdin
        cmd = f"cat {temp_path} | ollama run {MODEL} 2>/dev/null"
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120
        )
        return result.stdout if result.stdout else ""
    except subprocess.TimeoutExpired:
        return "[Response timed out]"
    except Exception as e:
        return f"[Error: {str(e)[:100]}]"
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass
