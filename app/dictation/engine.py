"""
M-78 Dictation Engine
---------------------
Real-time speech-to-text with fast clipboard injection.
Tracks session stats and persists to sessions.json.
"""

import os
import sys
import time
import datetime
import json
import threading
from app.database import core as database
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as wav_write
import keyboard
import pyperclip
import pyautogui
import requests
from app.utils.logger import log, log_error

from app.backend.transcriber import transcribe

# ── Win32 focus helpers ───────────────────────────────────────────────────────
try:
    import ctypes
    import ctypes.wintypes
    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32

    def _get_foreground_hwnd():
        """Return the current foreground window handle (HWND)."""
        return _user32.GetForegroundWindow()

    def _restore_focus(hwnd):
        """
        Restore focus to a previously captured HWND.
        Uses SetForegroundWindow with the thread attach trick for reliability.
        """
        if not hwnd:
            return
        try:
            cur_tid  = _kernel32.GetCurrentThreadId()
            tgt_tid  = _user32.GetWindowThreadProcessId(hwnd, None)
            attached = False
            if cur_tid != tgt_tid:
                _user32.AttachThreadInput(cur_tid, tgt_tid, True)
                attached = True

            _user32.SetForegroundWindow(hwnd)
            _user32.BringWindowToTop(hwnd)

            if attached:
                _user32.AttachThreadInput(cur_tid, tgt_tid, False)
        except Exception as ex:
            print(f"[M-78] focus restore warning: {ex}")

    WIN32_AVAILABLE = True
except Exception:
    WIN32_AVAILABLE = False
    def _get_foreground_hwnd(): return None
    def _restore_focus(hwnd): pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_RATE    = 16000
TEMP_WAV       = os.path.join(BASE_DIR, "dictation_temp.wav")
HOTKEY         = "ctrl+alt+d"
from app.database.core import add_session

def get_process_name(hwnd):
    if not hwnd: return "Unknown"
    try:
        import psutil
        import ctypes.wintypes
        
        pid = ctypes.wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        name = psutil.Process(pid.value).name()
        if name and name != "Unknown":
            return name
        return "Unknown"
    except Exception:
        return "Unknown"


# ── Dictation Backend ─────────────────────────────────────────────────────────
class DictationBackend:
    def __init__(self, on_status=None):
        """
        on_status: optional callable(status: str) for widget updates.
        Status values: 'idle', 'recording', 'processing', 'done', 'error'
        """
        self.is_recording   = False
        self._chunks        = []
        self._stream        = None
        self._start_time    = 0.0
        self._on_status     = on_status or (lambda s: None)
        self._target_hwnd   = None   # window to inject text into
        
        # ── Global Focus Tracker ──
        self._last_external_hwnd = None
        if WIN32_AVAILABLE:
            threading.Thread(target=self._tracker_loop, daemon=True).start()

    def _tracker_loop(self):
        """
        Continuously polls the foreground window.
        Ignores any window owned by THIS process (widget, dashboard, etc).
        This perfectly preserves the last actual application the user was using.
        """
        cur_pid = os.getpid()
        while True:
            time.sleep(0.1)
            try:
                hwnd = _user32.GetForegroundWindow()
                if hwnd:
                    pid = ctypes.wintypes.DWORD()
                    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    if pid.value != cur_pid:
                        self._last_external_hwnd = hwnd
            except Exception:
                pass

    # ── Status ────────────────────────────────────────────────────────────────
    def _emit(self, status: str):
        try:
            self._on_status(status)
        except Exception:
            pass

    # ── Recording ─────────────────────────────────────────────────────────────
    def start_recording(self):
        if self.is_recording:
            return

        # Target the last external application we saw (Word, Chrome, etc)
        self._target_hwnd = self._last_external_hwnd
        print(f"[M-78] Target HWND: {self._target_hwnd}")

        self.is_recording = True
        self._chunks      = []
        self._start_time  = time.time()
        self._emit("recording")
        log("Recording started.", role="Widget")

        def _cb(indata, frames, t, status):
            if self.is_recording:
                self._chunks.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=4096,
            callback=_cb,
        )
        self._stream.start()

    def stop_recording(self):
        if not self.is_recording:
            return None
        self.is_recording = False
        duration = time.time() - self._start_time

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._chunks:
            self._emit("idle")
            return None

        audio = np.concatenate(self._chunks, axis=0)
        wav_write(TEMP_WAV, SAMPLE_RATE, audio)

        self._emit("processing")
        log(f"Recording stopped. Duration: {duration:.2f}s. Saved to {TEMP_WAV}", role="Widget")
        return TEMP_WAV, duration

    # ── Process & Inject ──────────────────────────────────────────────────────
    def process_and_type(self, wav_file: str, duration_s: float):
        try:
            # Try API first to save local resources and ensure only one model is loaded (in backend)
            raw = ""
            try:
                log("Attempting transcription via API...", role="Widget")
                with open(wav_file, "rb") as f:
                    # The backend expects 'file' parameter
                    files = {"file": ("audio.wav", f, "audio/wav")}
                    resp = requests.post("http://127.0.0.1:8000/transcribe", files=files, timeout=30)
                
                if resp.status_code == 200:
                    raw = resp.json().get("raw_text", "")
                    log("Transcription successful via API.", role="Widget")
                else:
                    log_error(f"API transcription failed (status {resp.status_code}). Falling back to local.", role="Widget")
                    raw = transcribe(wav_file)
            except Exception as api_ex:
                log_error(f"API transcription request failed: {api_ex}. Falling back to local.", role="Widget")
                raw = transcribe(wav_file)

            if not raw or not raw.strip():
                log("No speech detected.", role="Widget")
                self._emit("idle")
                return ""

            log(f"Transcription result: {raw[:50]}...", role="Widget")
            word_count = len(raw.split())

            self._inject_text(raw)

            # Save session to Database
            app_name = get_process_name(self._target_hwnd)
            add_session(raw, word_count, duration_s, app_name)

            self._emit("done")
            return raw

        except Exception as e:
            print(f"[M-78] Error: {e}")
            self._emit("error")
            return ""
        finally:
            try:
                if wav_file and os.path.exists(wav_file):
                    os.remove(wav_file)
            except Exception:
                pass

    def _inject_text(self, text: str):
        """
        Inject text at the cursor of the previously active window.
        Strategy:
          1. Restore focus to the captured HWND via win32
          2. Copy text to clipboard
          3. Paste with Ctrl+V
          4. Restore old clipboard content
          Fallback: pyautogui.write() if paste seems to fail
        """
        # ── Save old clipboard ────────────────────────────────────────────────
        prev_clip = ""
        try:
            prev_clip = pyperclip.paste()
        except Exception:
            pass

        # ── Stage text in clipboard ───────────────────────────────────────────
        paste_text = text.strip() + " "
        pyperclip.copy(paste_text)

        # ── Restore focus to target window ────────────────────────────────────
        if self._target_hwnd:
            _restore_focus(self._target_hwnd)
            time.sleep(0.15)   # let the OS process the focus switch
        else:
            # No HWND captured — just wait a moment and hope focus is right
            time.sleep(0.2)

        # ── Paste ─────────────────────────────────────────────────────────────
        try:
            pyautogui.hotkey("ctrl", "v")
            print("[M-78] Pasted via Ctrl+V")
        except Exception as e:
            print(f"[M-78] Ctrl+V failed ({e}), falling back to pyautogui.write")
            try:
                pyautogui.write(paste_text, interval=0.02)
            except Exception as e2:
                print(f"[M-78] write fallback also failed: {e2}")

        # ── Restore old clipboard ─────────────────────────────────────────────
        def _restore_clip():
            time.sleep(0.6)
            try:
                pyperclip.copy(prev_clip)
            except Exception:
                pass
        threading.Thread(target=_restore_clip, daemon=True).start()

    # ── Toggle (convenience) ──────────────────────────────────────────────────
    def toggle(self):
        if not self.is_recording:
            self.start_recording()
        else:
            result = self.stop_recording()
            if result:
                wav, dur = result
                threading.Thread(
                    target=self.process_and_type,
                    args=(wav, dur),
                    daemon=True,
                ).start()


# ── Standalone CLI mode ───────────────────────────────────────────────────────
def run_standalone():
    backend = DictationBackend()

    def on_hotkey():
        if not backend.is_recording:
            print(f"\n[●] Recording... (press {HOTKEY} to stop)")
            backend.start_recording()
        else:
            print("[■] Processing...")
            result = backend.stop_recording()
            if result:
                wav, dur = result
                threading.Thread(
                    target=backend.process_and_type,
                    args=(wav, dur),
                    daemon=True,
                ).start()

    # The hotkey string should ideally come from database, for now we hardcore the default correctly
    keyboard.add_hotkey("ctrl+alt+d", on_hotkey, suppress=True)
    print(f"[M-78] Raw Dictation Active — ctrl+alt+d to toggle | Esc+C to quit")
    keyboard.wait("esc+c")


if __name__ == "__main__":
    # Ensure project root is in sys.path
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    run_standalone()
