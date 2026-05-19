"""
M-78 Launcher
--------------
Starts FastAPI backend + floating widget + pywebview dashboard.
Usage:
  python launcher.py              → full app
  python launcher.py --widget-only → only the floating widget
  python launcher.py --dashboard-only → only the dashboard window
"""

import os
import sys
import time
import subprocess
import threading
import argparse
import requests
import ctypes
import multiprocessing
from app.utils.logger import log, log_error

if __name__ == "__main__":
    multiprocessing.freeze_support()

if sys.platform == "win32":
    myappid = 'M78.Dictation.App' # Professional ID
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

BACKEND_URL = "http://127.0.0.1:8000"


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resource_path(rel):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base = getattr(sys, "_MEIPASS", BASE_DIR)
    return os.path.join(base, rel)


# ── Backend process ───────────────────────────────────────────
def start_backend():
    log("Starting backend process...")
    python = sys.executable
    args = ["--backend"] if getattr(sys, 'frozen', False) else [resource_path("main.py")]
    proc = subprocess.Popen(
        [python] + args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=BASE_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    log("Backend process started.")
    return proc


def wait_for_backend(timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{BACKEND_URL}/stats", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.8)
    return False


# ── Floating widget ───────────────────────────────────────────
def run_widget():
    """Run the floating widget."""
    if getattr(sys, 'frozen', False):
        # In bundled mode, start a separate process so it's truly isolated
        subprocess.Popen(
            [sys.executable, "--widget"],
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    else:
        # In dev mode, we can just import and run (usually in a thread)
        if BASE_DIR not in sys.path:
            sys.path.insert(0, BASE_DIR)
        from app.widgets.floater import FloatingWidget
        FloatingWidget().run()


# ── Dashboard (pywebview) ─────────────────────────────────────
def set_window_icon():
    """Sets the window icon natively on Windows since pywebview doesn't expose it."""
    if sys.platform != "win32": return
    import time
    time.sleep(2) # Wait for window to exist
    try:
        import win32gui
        import win32con
        hwnd = win32gui.FindWindow(None, "M-78")
        if hwnd:
            icon_path = resource_path("assets/icons/m78_icon.ico")
            if os.path.exists(icon_path):
                # Load small and big icons
                hicon = win32gui.LoadImage(
                    0, icon_path, win32con.IMAGE_ICON, 
                    0, 0, win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                )
                win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
                win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)
    except Exception:
        pass

def run_dashboard():
    """Open the pywebview dashboard window (blocking)."""
    import webview
    
    # Start icon-setter thread
    threading.Thread(target=set_window_icon, daemon=True).start()
    
    window = webview.create_window(
        "M-78",
        f"{BACKEND_URL}/frontend/index.html",
        width=1160,
        height=780,
        min_size=(900, 600),
        background_color="#080c14",
    )
    webview.start()


def check_dependencies():
    """Quick check for critical dependencies to show friendly error message."""
    missing = []
    deps = ["fastapi", "webview", "requests", "keyboard", "psutil"]
    if sys.platform == "win32":
        deps.append("win32gui")
    
    for dep in deps:
        try:
            __import__(dep.split('.')[0])
        except ImportError:
            missing.append(dep)
    
    if missing:
        msg = f"Missing required dependencies: {', '.join(missing)}\n\nPlease reinstall M-78 or run: pip install -r requirements.txt"
        print(f"\n[M-78] ERROR: {msg}\n")
        
        # On Windows, try to show a GUI message box if we're in GUI mode
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, msg, "M-78 Launch Error", 0x10)
            except Exception:
                pass
        
        # Only try to wait for input if we have a valid stdin/stdout TTY
        if sys.platform == "win32" and sys.stdout and sys.stdout.isatty() and sys.stdin:
            try:
                input("Press Enter to exit...")
            except EOFError:
                pass
        sys.exit(1)

# ── Full app ──────────────────────────────────────────────────
def main():
    check_dependencies()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--widget-only",    action="store_true")
    parser.add_argument("--dashboard-only", action="store_true")
    parser.add_argument("--backend",        action="store_true")
    parser.add_argument("--widget",         action="store_true")
    args = parser.parse_args()

    if args.backend:
        import uvicorn
        # Import main at runtime to avoid circular/premature initialization
        from main import app
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
        return

    if args.widget or args.widget_only:
        # If we reached here with --widget or --widget-only, it's the role of THIS process
        if BASE_DIR not in sys.path:
            sys.path.insert(0, BASE_DIR)
        from app.widgets.floater import FloatingWidget
        FloatingWidget().run()
        return

    # Start backend
    backend_proc = start_backend()
    print("[M-78] Starting backend…")

    if not wait_for_backend():
        print("[M-78] ERROR: Backend did not start in time.")
        backend_proc.terminate()
        sys.exit(1)

    print("[M-78] Backend ready.")

    if args.dashboard_only:
        try:
            run_dashboard()
        finally:
            backend_proc.terminate()
        return

    # Read startup preferences from DB organically
    launch_widget_startup = True
    try:
        import sqlite3
        db_path = resource_path("m78_database.sqlite")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key='launch_widget_startup'")
            row = c.fetchone()
            conn.close()
            if row and row[0] == 'false':
                launch_widget_startup = False
    except Exception:
        pass

    if launch_widget_startup:
        widget_thread = threading.Thread(target=run_widget, daemon=True)
        widget_thread.start()

    try:
        run_dashboard()     # blocks until window is closed
    finally:
        print("[M-78] Shutting down…")
        backend_proc.terminate()
        try:
            backend_proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            backend_proc.kill()


if __name__ == "__main__":
    main()
