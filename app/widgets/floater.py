"""
M-78 Floating Widget
---------------------
Pure waveform panel — no mic icon.
- Idle:       slow breathing wave (subtle, calm)
- Recording:  fast sine-wave bars growing from center + soft glow rings
- Processing: amber chase animation
- Right-click: context menu (Dashboard, Exit)
"""

import tkinter as tk
import threading
import time
import math
import os
import sys
import ctypes

if sys.platform == "win32":
    myappid = 'M78.Dictation.App' # Unified Professional ID
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
from app.dictation.engine import DictationBackend

# ── Widget geometry ───────────────────────────────────────────────────────────
W        = 130   # canvas width
H        = 90    # canvas height
CX       = W // 2
CY       = H // 2

# Waveform bars (grow symmetrically up AND down from CY)
NUM_BARS  = 9
BAR_W     = 5
BAR_GAP   = 4
BAR_MIN_H = 3
BAR_MAX_H = 38
TOTAL_W   = NUM_BARS * BAR_W + (NUM_BARS - 1) * BAR_GAP
BAR_X0    = CX - TOTAL_W // 2

# Colors
C_BG          = "#0b0e17"   # deep dark panel
C_BORDER_IDLE = "#16202e"   # border idle
C_BORDER_REC  = "#00d4aa"   # border recording
C_BORDER_PROC = "#f59e0b"   # border processing
C_WAVE_IDLE   = "#1b2d48"   # dim blue-teal bars when idle
C_WAVE_REC    = "#00d4aa"   # teal bars when recording
C_WAVE_PROC   = "#f59e0b"   # amber bars when processing
C_GLOW_1      = "#003d30"   # inner glow oval (subtle)
C_GLOW_2      = "#001f18"   # outer glow oval (barely visible)
C_STATUS_IDLE = "#3a4a62"
C_STATUS_REC  = "#00d4aa"
C_STATUS_PROC = "#f59e0b"

# Waveform vertical center (leave room for status label at bottom)
WAVE_CY = CY - 6


class FloatingWidget:
    def __init__(self):
        # ── Tk root ───────────────────────────────────────────────────────────
        self.root = tk.Tk()
        self.root.title("M78-Widget-Process")
        self.root.geometry(f"{W}x{H}+80+80")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)   # slight transparency for premium feel
        self.root.config(bg=C_BG)
        self.root.resizable(False, False)
        try:
            icon_path = os.path.abspath("assets/icons/m78_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

        # ── Prevent window from stealing focus on click ──────────────────────────
        def _apply_noactivate():
            try:
                import ctypes
                hwnd = ctypes.windll.user32.FindWindowW(None, "M78-Widget-Process")
                if hwnd:
                    GWL_EXSTYLE = -20
                    WS_EX_NOACTIVATE = 0x08000000
                    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE)
            except Exception as e:
                print(f"[M-78] WS_EX_NOACTIVATE failed: {e}")
        self.root.after(50, _apply_noactivate)

        # ── Canvas ────────────────────────────────────────────────────────────
        self.canvas = tk.Canvas(
            self.root,
            width=W, height=H,
            bg=C_BG,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # ── Glow ovals (behind bars, recording only) ──────────────────────────
        self._glow_outer = self.canvas.create_oval(
            CX-55, WAVE_CY-24, CX+55, WAVE_CY+24,
            fill="", outline="", width=0,
        )
        self._glow_inner = self.canvas.create_oval(
            CX-42, WAVE_CY-18, CX+42, WAVE_CY+18,
            fill="", outline="", width=0,
        )

        # ── Waveform bars ─────────────────────────────────────────────────────
        self._bars = []
        for i in range(NUM_BARS):
            x0 = BAR_X0 + i * (BAR_W + BAR_GAP)
            x1 = x0 + BAR_W
            bar = self.canvas.create_rectangle(
                x0, WAVE_CY - BAR_MIN_H,
                x1, WAVE_CY + BAR_MIN_H,
                fill=C_WAVE_IDLE, outline="", width=0,
            )
            self._bars.append((bar, x0, x1))

        # ── Widget border ─────────────────────────────────────────────────────
        self._border = self.canvas.create_rectangle(
            1, 1, W - 1, H - 1,
            fill="", outline=C_BORDER_IDLE, width=1,
        )

        # ── Status label ──────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Idle")
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Segoe UI", 7, "bold"),
            fg=C_STATUS_IDLE,
            bg=C_BG,
        )
        self.canvas.create_window(CX, H - 8, window=self.status_label)

        # ── State ─────────────────────────────────────────────────────────────
        self._state      = "idle"
        self._drag_x     = 0
        self._drag_y     = 0
        self._drag_moved = False

        # ── Backend ───────────────────────────────────────────────────────────
        self.backend = DictationBackend(on_status=self._on_backend_status)

        # ── Bindings ──────────────────────────────────────────────────────────
        self.canvas.bind("<ButtonPress-1>",   self._drag_start)
        self.canvas.bind("<B1-Motion>",       self._drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._drag_end)
        self.canvas.bind("<Button-3>",        self._show_context_menu)

        # Global hotkey — uses _hotkey_toggle (no focus manipulation needed)
        try:
            import keyboard
            keyboard.add_hotkey("ctrl+alt+d", self._hotkey_toggle, suppress=True)
        except Exception as e:
            print(f"[M-78] Hotkey registration failed: {e}")

        # Start animation
        self._animate()

    # ── Drag ──────────────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._drag_x     = e.x_root - self.root.winfo_x()
        self._drag_y     = e.y_root - self.root.winfo_y()
        self._drag_moved = False

    def _drag_motion(self, e):
        self.root.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")
        self._drag_moved = True

    def _drag_end(self, e):
        if not self._drag_moved:
            self._click_toggle()

    # ── Toggle from widget CLICK ───────────────────────────────────────────────
    def _click_toggle(self):
        """
        Since WS_EX_NOACTIVATE is set, clicking the widget NO LONGER steals focus
        from the underlying target app. The target app remains foreground!
        """
        if self._state == "idle":
            self._set_state("recording")
            self.backend.start_recording()
        elif self._state == "recording":
            self._stop_and_process()

    # ── Toggle from HOTKEY ─────────────────────────────────────────────────────
    def _hotkey_toggle(self):
        """
        Hotkey path: the user's app still has focus when hotkey fires,
        so we capture the HWND immediately with no delay.
        """
        if self._state == "idle":
            self.root.after(0, self._set_state, "recording")
            self.backend.start_recording()
        elif self._state == "recording":
            self.root.after(0, self._stop_and_process)

    # ── Stop & process ─────────────────────────────────────────────────────────
    def _stop_and_process(self):
        self._set_state("processing")
        result = self.backend.stop_recording()
        if result:
            wav, dur = result
            threading.Thread(
                target=self.backend.process_and_type,
                args=(wav, dur),
                daemon=True,
            ).start()
        else:
            self._set_state("idle")

    # ── Backend status callback ────────────────────────────────────────────────
    def _on_backend_status(self, status: str):
        target = "idle" if status in ("done", "error") else status
        self.root.after(0, self._set_state, target)

    # ── State transitions ──────────────────────────────────────────────────────
    def _set_state(self, state: str):
        self._state = state
        if state == "idle":
            self.status_var.set("Idle")
            self.status_label.config(fg=C_STATUS_IDLE)
            self.canvas.itemconfig(self._border, outline=C_BORDER_IDLE)
            self.canvas.itemconfig(self._glow_outer, outline="", width=0)
            self.canvas.itemconfig(self._glow_inner, outline="", width=0)
        elif state == "recording":
            self.status_var.set("● Recording")
            self.status_label.config(fg=C_STATUS_REC)
            self.canvas.itemconfig(self._border, outline=C_BORDER_REC)
        elif state == "processing":
            self.status_var.set("Processing…")
            self.status_label.config(fg=C_STATUS_PROC)
            self.canvas.itemconfig(self._border, outline=C_BORDER_PROC)
            self.canvas.itemconfig(self._glow_outer, outline="", width=0)
            self.canvas.itemconfig(self._glow_inner, outline="", width=0)

    # ── Animation ─────────────────────────────────────────────────────────────
    def _animate(self):
        t = time.time()
        if self._state == "recording":
            self._draw_bars(self._heights_active(t), C_WAVE_REC)
            self._draw_glow(t)
        elif self._state == "processing":
            self._draw_processing(t)
        else:
            self._draw_bars(self._heights_idle(t), C_WAVE_IDLE)
        self.root.after(35, self._animate)   # ~28 fps

    # ── Bar height generators ──────────────────────────────────────────────────
    def _heights_idle(self, t):
        """Slow breathing: low amplitude, tapered edges, feels calm."""
        heights = []
        for i in range(NUM_BARS):
            phase  = i * (math.pi / (NUM_BARS - 1))
            raw    = (math.sin(t * 0.55 * math.pi + phase) + 1) / 2  # 0..1
            # Edge taper — center bar is tallest
            center = (NUM_BARS - 1) / 2
            taper  = 1 - 0.60 * abs((i - center) / center) ** 1.4
            amp    = BAR_MAX_H * 0.18 * taper
            heights.append(max(BAR_MIN_H, int(BAR_MIN_H + raw * amp)))
        return heights

    def _heights_active(self, t):
        """Fast energetic wave: high amplitude, each bar has unique freq+phase."""
        heights = []
        for i in range(NUM_BARS):
            phase  = i * (math.pi * 2 / NUM_BARS) + 0.3
            freq   = 3.6 + i * 0.22
            raw    = (math.sin(t * freq + phase) + 1) / 2  # 0..1
            center = (NUM_BARS - 1) / 2
            taper  = 1 - 0.35 * abs((i - center) / center) ** 1.3
            amp    = BAR_MAX_H * taper
            heights.append(max(BAR_MIN_H, int(BAR_MIN_H + raw * (amp - BAR_MIN_H))))
        return heights

    # ── Draw helpers ───────────────────────────────────────────────────────────
    def _draw_bars(self, heights, color):
        """Bars grow symmetrically up and down from WAVE_CY."""
        for i, (bar, x0, x1) in enumerate(self._bars):
            h  = heights[i]
            y0 = WAVE_CY - h
            y1 = WAVE_CY + h
            self.canvas.coords(bar, x0, y0, x1, y1)
            self.canvas.itemconfig(bar, fill=color)

    def _draw_processing(self, t):
        """Amber chase — 1 bright bar travels left-to-right."""
        lit = int(t * 5) % NUM_BARS
        for i, (bar, x0, x1) in enumerate(self._bars):
            dist = min(abs(i - lit), NUM_BARS - abs(i - lit))
            if dist == 0:
                h, c = int(BAR_MAX_H * 0.60), C_WAVE_PROC
            elif dist == 1:
                h, c = int(BAR_MAX_H * 0.32), "#b45309"
            else:
                h, c = BAR_MIN_H, C_WAVE_IDLE
            self.canvas.coords(bar, x0, WAVE_CY - h, x1, WAVE_CY + h)
            self.canvas.itemconfig(bar, fill=c)

    def _draw_glow(self, t):
        """Two oval halos pulsing at offset phases — very soft, not flashy."""
        pulse1 = (math.sin(t * 3.2) + 1) / 2        # 0..1
        pulse2 = (math.sin(t * 3.2 + math.pi) + 1) / 2

        ri = int(40 + pulse1 * 7)
        ro = int(54 + pulse2 * 9)

        self.canvas.coords(
            self._glow_inner,
            CX - ri, WAVE_CY - ri // 2,
            CX + ri, WAVE_CY + ri // 2,
        )
        self.canvas.itemconfig(self._glow_inner, outline=C_GLOW_1, width=1)

        self.canvas.coords(
            self._glow_outer,
            CX - ro, WAVE_CY - ro // 2,
            CX + ro, WAVE_CY + ro // 2,
        )
        self.canvas.itemconfig(self._glow_outer, outline=C_GLOW_2, width=1)

    # ── Context menu ──────────────────────────────────────────────────────────
    def _show_context_menu(self, e):
        menu = tk.Menu(
            self.root, tearoff=0,
            bg="#141c2e", fg="#cbd5e1",
            activebackground="#00d4aa", activeforeground="#000",
            font=("Segoe UI", 9),
        )
        menu.add_command(label="  Open Dashboard", command=self._open_dashboard)
        menu.add_separator()
        menu.add_command(label="  Exit M-78", command=self._exit)
        try:
            menu.tk_popup(e.x_root, e.y_root)
        finally:
            menu.grab_release()

    def _open_dashboard(self):
        import subprocess
        try:
            subprocess.Popen(
                [sys.executable, "launcher.py", "--dashboard-only"],
                cwd=os.path.abspath("."),
            )
        except Exception as ex:
            print(f"[M-78] Dashboard open failed: {ex}")

    def _exit(self):
        try:
            import keyboard
            keyboard.unhook_all()
        except Exception:
            pass
        self.root.destroy()

    # ── Run ───────────────────────────────────────────────────────────────────
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath("."))
    FloatingWidget().run()
