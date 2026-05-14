# M-78 | Premium Desktop Dictation Assistant

M-78 is a professional, system-wide dictation tool for Windows. It provides high-performance speech-to-text with a premium floating widget and an advanced insights dashboard.

## Features
- **Global Dictation**: Trigger dictation anywhere with `Ctrl + Alt + D`.
- **Premium Dashboard**: Track your productivity, word counts, and WPM.
- **Smart Dictionary**: Save technical terms and names for better recognition.
- **Snippets**: Quick-inject reusable text phrases.
- **Privacy First**: All data is stored locally in an encrypted-ready SQLite database.

## 🚀 Quick Start (Windows)

### 1. Clone & Setup
```bash
git clone https://github.com/Matis-8/M-78.git
cd M-78
```

### 2. Install Python
Ensure you have **Python 3.9+** installed.

### 3. Install Requirements
We recommend using a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run M-78
Simply double-click **`M-78.vbs`** for a silent background launch, or run:
```bash
python launcher.py
```

---

## 🛠️ Portability Note
M-78 is designed to be fully portable. All paths are relative to the script directory. If you move the folder, the application and its database will follow.

## Project Structure
- `app/`: Core application logic (Database, Dictation, Widgets, Dashboard).
- `assets/`: Icons and branded media.
- `docs/`: Technical documentation and setup guides.

## License
Copyright © 2026 M-78 Organization. All rights reserved.
