# Process Watchdog

**Your PC, less random junk in the background.** Process Watchdog sits in the Windows tray and quietly closes leftover helper/update processes when you are not actually using the main app. Pick what to watch on first run — then mostly forget it exists.

Made by **[somaqzz12](https://github.com/somaqzz12)**.

---

## Get the app (no coding)

You only need one file: **`ProcessWatchdog.exe`**.

### Option A — Releases (easiest when it is there)

Open **[Releases](https://github.com/somaqzz12/killswitch-for-all-apps-on-windows-/releases)** → latest → download **`ProcessWatchdog.exe`**.

### Option B — GitHub Actions (good when Releases is empty)

1. Open **[Build Windows EXE](https://github.com/somaqzz12/killswitch-for-all-apps-on-windows-/actions/workflows/build-exe.yml)**.
2. Click **Run workflow** → branch **main** → **Run workflow**.
3. When it finishes, open the run → **Artifacts** → **`ProcessWatchdog-windows`** (ZIP) → inside is **`ProcessWatchdog.exe`**.

### Option C — Build on your PC

Install Python, open this folder, run **`BUILD.bat`**, then grab **`dist\ProcessWatchdog.exe`**.

---

## First run

1. Double-click **`ProcessWatchdog.exe`**.
2. Choose apps on the welcome screen.
3. Look for the **tray icon** by the clock — that means it is running.
4. **Really quit:** tray menu → **Exit**. (Closing the window only closes the dashboard.)

---

## App icon (EXE / shortcut)

**`ProcessWatchdog.exe`** uses **`icon.ico`**, built from **`assets/app_icon.png`**. To swap art: replace the PNG, run **`python scripts/make_icon.py`**, then **`BUILD.bat`**.

## Optional: your own tray picture

Put **`tray_icon.png`** next to the EXE (or next to `watchdog.py` if you run from source). Use a **transparent PNG**, about **64×64**. It replaces the default lightning icon in the **tray** (separate from the EXE file icon above).

---

## Safety note

This is **Windows-only** and it **ends processes**. Start with fewer profiles, use **Pause** if something feels wrong, and read the **About** section in **Settings** anytime.

Logs: **`watchdog.log`** next to the app.

---

## Nerds

- From source: `SETUP.bat` then `python watchdog.py`
- Startup: `python watchdog.py --register-startup` / `--unregister-startup`
