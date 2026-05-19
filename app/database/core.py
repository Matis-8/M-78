import sqlite3
import datetime
import os

DB_DIR = os.path.join(os.path.expanduser("~"), ".m78")
DB_PATH = os.path.join(DB_DIR, "m78_database.sqlite")
os.makedirs(DB_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Sessions
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            text TEXT,
            word_count INTEGER,
            duration REAL DEFAULT 0,
            app_name TEXT
        )
    """)
    try:
        c.execute("ALTER TABLE sessions ADD COLUMN duration REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Settings
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    # Snippets
    c.execute("""
        CREATE TABLE IF NOT EXISTS snippets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT
        )
    """)
    # Dictionary
    c.execute("""
        CREATE TABLE IF NOT EXISTS dictionary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT,
            replacement TEXT
        )
    """)
    # Scratchpad
    c.execute("""
        CREATE TABLE IF NOT EXISTS scratchpad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT
        )
    """)
    
    # Insert initial scratchpad row if empty
    c.execute("SELECT COUNT(*) FROM scratchpad")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO scratchpad (content) VALUES ('')")

    conn.commit()
    conn.close()

# ── SESSIONS ──────────────────────────────────────────────────────────

def add_session(text, word_count, duration, app_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO sessions (timestamp, text, word_count, duration, app_name) VALUES (?, ?, ?, ?, ?)",
              (timestamp, text, word_count, duration, app_name))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # words and duration
    c.execute("SELECT SUM(word_count), SUM(duration) FROM sessions")
    row = c.fetchone()
    total_words = row[0] or 0
    total_duration = row[1] or 0
    avg_wpm = int((total_words / (total_duration / 60))) if total_duration > 0 else 0
    
    # today words
    today = datetime.date.today().isoformat()
    c.execute("SELECT SUM(word_count) FROM sessions WHERE timestamp LIKE ?", (f"{today}%",))
    today_words = c.fetchone()[0] or 0

    # total sessions
    c.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = c.fetchone()[0] or 0

    # streak & heatmap (last ~250 days)
    c.execute("SELECT substr(timestamp, 1, 10) as date, SUM(word_count) FROM sessions GROUP BY date ORDER BY date DESC")
    rows = c.fetchall()
    
    session_dates = [r[0] for r in rows]
    streak = 0
    longest_streak = 0
    current_temp = 0
    
    check = datetime.date.today()
    # current streak
    for d in session_dates:
        if d == str(check):
            streak += 1
            check -= datetime.timedelta(days=1)
        else:
            break
            
    # simplistic longest streak logic mapping
    # Just iterate through all unique sorted dates and group consecutive
    if session_dates:
        sorted_dates = sorted([datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in session_dates])
        longest_streak = 1
        cur_s = 1
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                cur_s += 1
            else:
                if cur_s > longest_streak:
                    longest_streak = cur_s
                cur_s = 1
        if cur_s > longest_streak:
            longest_streak = cur_s

    words_per_session = [{"date": r[0], "words": r[1]} for r in rows]

    conn.close()
    return {
        "total_words": total_words,
        "today_words": today_words,
        "total_sessions": total_sessions,
        "avg_wpm": avg_wpm,
        "streak_days": streak,
        "longest_streak": longest_streak,
        "words_per_session": words_per_session
    }

def get_desktop_usage():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT app_name, COUNT(*) as cnt, SUM(word_count) as words FROM sessions GROUP BY app_name ORDER BY cnt DESC")
    rows = c.fetchall()
    conn.close()
    
    # Map raw exe to nice labels
    mapping = {
        "chrome.exe": "Browser",
        "msedge.exe": "Browser",
        "firefox.exe": "Browser",
        "Code.exe": "VS Code / Dev",
        "pycharm64.exe": "VS Code / Dev",
        "WINWORD.EXE": "Documents",
        "EXCEL.EXE": "Documents",
        "Notion.exe": "Notes",
        "Obsidian.exe": "Notes",
        "WhatsApp.exe": "Messages",
        "Discord.exe": "Messages",
        "Slack.exe": "Work Messages"
    }

    # Aggregate
    agg = {}
    total_sessions = 0
    for r in rows:
        exe = r[0] if r[0] else "Other Tasks"
        nice_name = mapping.get(exe, exe) if exe != "Other Tasks" else "Other Tasks"
        # capitalize generic exes if unknown
        if exe.endswith(".exe") and nice_name == exe:
            nice_name = exe.replace(".exe", "").capitalize()
        
        agg[nice_name] = agg.get(nice_name, 0) + r[1]
        total_sessions += r[1]
        
    # Formatting
    result = []
    for k, v in agg.items():
        pct = int(round((v / total_sessions * 100))) if total_sessions > 0 else 0
        result.append({"name": k, "count": v, "percentage": pct})
        
    result.sort(key=lambda x: x["count"], reverse=True)
    return {"total_apps": len(agg), "usage": result}

def get_recent_sessions(limit=50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, timestamp, text, word_count, duration, app_name FROM sessions ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "timestamp": r[1], "text": r[2], "word_count": r[3], "duration": r[4], "app_name": r[5]} for r in rows]

# ── CRUD ──────────────────────────────────────────────────────────────

def get_all(table):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if table == 'snippets':
        c.execute("SELECT id, title, content FROM snippets ORDER BY id DESC")
        data = [{"id": r[0], "title": r[1], "content": r[2]} for r in c.fetchall()]
    elif table == 'dictionary':
        c.execute("SELECT id, word, replacement FROM dictionary ORDER BY id DESC")
        data = [{"id": r[0], "word": r[1], "replacement": r[2]} for r in c.fetchall()]
    else:
        data = []
    conn.close()
    return data

def add_snippet(title, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO snippets (title, content) VALUES (?, ?)", (title, content))
    conn.commit()
    conn.close()

def add_dict_word(word, replacement):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO dictionary (word, replacement) VALUES (?, ?)", (word, replacement))
    conn.commit()
    conn.close()

def delete_item(table, item_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"DELETE FROM {table} WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

def delete_all_sessions():
    """Clear History - Removes all session records."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM sessions")
    conn.commit()
    conn.close()

def reset_analytics_data():
    """Reset Analytics - Since analytics are derived from sessions, this also clears sessions."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM sessions")
    # Also reset any other future telemetry tables here
    conn.commit()
    conn.close()


def get_scratchpad():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT content FROM scratchpad LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""

def save_scratchpad(content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE scratchpad SET content=?", (content,))
    conn.commit()
    conn.close()

# ── SETTINGS ──────────────────────────────────────────────────────────

def get_settings():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT key, value FROM settings")
    data = {r[0]: r[1] for r in c.fetchall()}
    conn.close()
    return data

def update_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

init_db()
