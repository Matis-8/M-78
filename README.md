# M-78: Premium Desktop Dictation Assistant

> [!IMPORTANT]
> ### DOWNLOAD M-78 SETUP HERE
> **For normal users:** Download and run the **`M-78-Setup.exe`** from the latest release. No Python or complex setup required.

---

## For Users
M-78 is a professional, system-wide dictation tool for Windows. It provides high-performance speech-to-text with a premium floating widget and an advanced insights dashboard.

### Getting Started
1. **Download**: Get the latest `M-78-Setup.exe` from the Releases page.
2. **Install**: Run the setup file and follow the wizard.
3. **Launch**: Open M-78 from your Desktop or Start Menu.
4. **Dictate**: Press `Ctrl + Alt + D` to start dictating into any app!

---

## For Developers
If you want to build M-78 from source or modify the code, follow these steps.

### Build the Installer (.exe)
We use a 3-step automated build process to generate the professional installer.
1. **Prerequisites**:
   - Install **Python 3.9+**.
   - Install **Inno Setup 6** (from jrsoftware.org).
2. **Setup Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Run Build Script**:
   Double-click `build_installer.bat`.
   - **Step 1**: Bundles code using PyInstaller.
   - **Step 2**: Compiles the installer using Inno Setup (`setup.iss`).
   - **Step 3**: Generates the final **`M-78 Setup.exe`**.

### Project Structure
- `app/`: Core logic (Backend, Database, Widgets).
- `assets/`: Branding and premium icons.
- `launcher.py`: Main entry point orchestrator.
- `setup.iss`: Inno Setup configuration script.
- `build_installer.bat`: Automated build pipeline.

---

## Professional Release Notes
See release_notes.md for a full list of features and fixes in v1.0.0.

*Built by the Matis-8 Team.*
