import os
import datetime
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import uuid

from app.backend.transcriber import transcribe
from app.database import core as database
import ctypes
import sys

if sys.platform == "win32":
    myappid = 'M78.Dictation.App'
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resource_path(rel):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    import sys
    base = getattr(sys, "_MEIPASS", BASE_DIR)
    return os.path.join(base, rel)

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="M-78 Premium API")

@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/frontend/index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Schemas ────────────────────────────────────────────────────────────────────
class SnippetInput(BaseModel):
    title: str
    content: str

class DictionaryInput(BaseModel):
    word: str
    replacement: str

class ScratchpadInput(BaseModel):
    content: str

class SettingsInput(BaseModel):
    key: str
    value: str

# ── /transcribe (raw only) ─────────────────────────────────────────────────────
@app.post("/transcribe")
async def handle_transcription(file: UploadFile = File(...)):
    try:
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename)[1] or ".webm"
        file_path = os.path.join(TEMP_DIR, f"{file_id}{ext}")

        with open(file_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        # In unified mode, the widget handles its own session recording to capture duration and app name accurately.
        # The backend just provides the raw transcription service.
        raw_text = transcribe(file_path)
        os.remove(file_path)

        word_count = len(raw_text.split()) if raw_text else 0
        return {"raw_text": raw_text, "word_count": word_count}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── /stats ─────────────────────────────────────────────────────────────────────
@app.get("/stats")
def get_stats():
    # Merge core stats and desktop usage for the dashboard overview
    stats = database.get_stats()
    usage = database.get_desktop_usage()
    stats["desktop_usage"] = usage
    return stats

@app.get("/sessions")
def get_sessions():
    return database.get_recent_sessions(50)

@app.delete("/sessions/{item_id}")
def delete_session(item_id: int):
    database.delete_item('sessions', item_id)
    return {"status": "success"}

@app.delete("/stats/reset")
def reset_sessions():
    database.delete_all_sessions()
    return {"status": "success"}



# ── Pages API ──────────────────────────────────────────────────────────────────
@app.get("/snippets")
def get_snippets():
    return database.get_all('snippets')

@app.post("/snippets")
def add_snippet(data: SnippetInput):
    database.add_snippet(data.title, data.content)
    return {"status": "success"}

@app.delete("/snippets/{item_id}")
def delete_snippet(item_id: int):
    database.delete_item('snippets', item_id)
    return {"status": "success"}


@app.get("/dictionary")
def get_dictionary():
    return database.get_all('dictionary')

@app.post("/dictionary")
def add_dictionary(data: DictionaryInput):
    database.add_dict_word(data.word, data.replacement)
    return {"status": "success"}

@app.delete("/dictionary/{item_id}")
def delete_dictionary(item_id: int):
    database.delete_item('dictionary', item_id)
    return {"status": "success"}


@app.get("/scratchpad")
def get_scratchpad():
    return {"content": database.get_scratchpad()}

@app.post("/scratchpad")
def save_scratchpad(data: ScratchpadInput):
    database.save_scratchpad(data.content)
    return {"status": "success"}

@app.get("/settings")
def get_settings():
    return database.get_settings()

@app.post("/settings")
def update_setting(data: SettingsInput):
    database.update_setting(data.key, data.value)
    
    # Handle Start with Windows native integration
    if data.key == "start_with_windows":
        try:
            import os, sys
            shell_startup = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
            shortcut_path = os.path.join(shell_startup, "M-78.lnk")
            
            if data.value == "true":
                # Create shortcut in startup folder
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(shortcut_path)
                current_dir = BASE_DIR
                shortcut.Targetpath = os.path.join(current_dir, "M-78.vbs")
                shortcut.WorkingDirectory = current_dir
                shortcut.IconLocation = os.path.join(current_dir, "assets", "icons", "m78_icon.ico")
                shortcut.save()
            else:
                # Remove shortcut
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
        except Exception as e:
            print(f"[M-78] Failed to update startup shortcut: {e}")

    return {"status": "success"}

@app.delete("/history")
def clear_history():
    database.delete_all_sessions()
    return {"status": "success"}

@app.delete("/analytics")
def reset_analytics():
    database.reset_analytics_data()
    return {"status": "success"}


# ── /launch-widget ─────────────────────────────────────────────────────────────
@app.post("/launch-widget")
def launch_widget():
    import subprocess, sys, os
    import psutil
    try:
        hwnd = 0
        if sys.platform == "win32":
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "M78-Widget-Process")
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                return {"status": "restored"}
                
        # Singleton protection / Zombie check
        for p in psutil.process_iter(['name', 'cmdline']):
            try:
                name = p.info['name']
                if name and 'python' in name.lower():
                    cmdline = p.info.get('cmdline', [])
                    if cmdline and any("floater.py" in arg for arg in cmdline):
                        if not hwnd:
                            # It is running but has no window. It is likely a ghost process. Terminate it.
                            p.terminate()
                            p.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                pass

        args = ["--widget"] if getattr(sys, 'frozen', False) else [os.path.join(BASE_DIR, "app", "widgets", "floater.py")]
        subprocess.Popen(
            [sys.executable] + args,
            cwd=BASE_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        return {"status": "launched"}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}


# ── Frontend ───────────────────────────────────────────────────────────────────
app.mount("/frontend", StaticFiles(directory="app/dashboard"), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
