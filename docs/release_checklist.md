# M-78 Pre-Release Verification Checklist (v1.0.0)

Before publishing the release to GitHub, ensure all boxes are checked:

## 📦 Installer & Files
- [x] `build_installer.bat` runs successfully.
- [x] `M-78-Setup.exe` is generated in `dist-installer/`.
- [ ] Installer icon is correctly displayed.
- [ ] Installer license/terms (optional) are included if needed.

## 🚀 Execution (Post-Install)
- [ ] App launches from Desktop shortcut.
- [ ] App launches from Start Menu.
- [ ] Waveform widget appears and correctly captures audio.
- [ ] Dashboard opens at the correct entry point (Home).
- [ ] Taskbar icon shows the M-78 logo (no Python logo).
- [ ] App is grouped as "M-78" in the taskbar.

## ⚙️ Settings & Persistence
- [ ] SQLite database is auto-created in the install folder.
- [ ] User display name persists after restart.
- [ ] "Start with Windows" toggle creates a working shortcut in Startup.
- [ ] "Clear History" wipes the session list.
- [ ] "Reset Analytics" zeroes out the dashboard stay.

## 🗑️ Uninstallation
- [ ] Uninstaller removes all files from Program Files.
- [ ] Shortcuts are removed from Desktop/Start Menu.
- [ ] Registry keys (if any) are cleaned up.

---
*Verified by:* _________________
*Date:* _________________
