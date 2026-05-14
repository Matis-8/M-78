# M-78 Setup & Development Notes

## Environment Setup
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Dependencies
- **FastAPI/Uvicorn**: Backend API and Dashboard server.
- **PyWebView**: Native Windows window wrapper.
- **Tkinter**: Lightweight floating widget UI.
- **SoundDevice/Scipy**: Audio capture.
- **Pynput**: Global hotkey management.

## Building the App
Run the provided `build_m78.bat` to generate a standalone `.exe` using PyInstaller.

## Troubleshooting
- **Icon missing**: Ensure `assets/icons/m78_icon.ico` exists.
- **Permission error**: Run as Administrator if global injection fails in certain apps.
