import os
import datetime
import sys

LOG_DIR = os.path.join(os.path.expanduser("~"), ".m78")
LOG_FILE = os.path.join(LOG_DIR, "m78.log")

os.makedirs(LOG_DIR, exist_ok=True)

def log(message, role="App"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = f"[{timestamp}] [{role}]"
    line = f"{prefix} {message}\n"
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
        # Also print to stderr if not frozen (dev mode)
        if not getattr(sys, 'frozen', False):
            sys.stderr.write(line)
    except Exception:
        pass

def log_error(message, role="App"):
    log(f"ERROR: {message}", role)
