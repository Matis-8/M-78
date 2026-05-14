# M-78 Setup & Development Notes

## Prerequisites
- Windows 10/11
- Python 3.9 - 3.12 (Recommended)
- Internet connection (for transcription API)

## Installation Flow
1. **Clone the repo** to any local directory.
2. **Setup environment**:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
   - `pip install -r requirements.txt`
3. **Launch**:
   - Use `M-78.vbs` for a silent launch.
   - Use `launcher.py` for debugging/console output.

## Project Structure (Modular)
- `M-78.vbs`: Main silent entry point.
- `launcher.py`: Orchestrator (Backend + UI).
- `app/`: Core logic and modules.
- `assets/`: Branding and icons.
- `m78_database.sqlite`: Local storage (auto-created).

## Building the App
Run the provided `build_m78.bat` to generate a standalone `.exe` using PyInstaller.

## Troubleshooting
- **Icon missing**: Ensure `assets/icons/m78_icon.ico` exists.
- **Permission error**: Run as Administrator if global injection fails in certain apps.
