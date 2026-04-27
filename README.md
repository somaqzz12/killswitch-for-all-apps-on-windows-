# Process Watchdog

**Your PC, less random junk in the background.** Process Watchdog sits in the Windows tray and can close leftover helper/update processes when you are not really using the main app. You pick what to watch on first run — then mostly forget it exists.

Made by **[somaqzz12](https://github.com/somaqzz12)**.

---
Here is a straight list of everything Process Watchdog does in this codebase, in plain terms.

What it is for
Windows only. It runs in the system tray and can terminate (“kill”) processes you’ve marked as “bloat” for certain apps, based on rules you choose (profiles).
It is meant to reduce background junk (helpers, updaters, extra instances) when you’re not really using the main app, or under other rules per profile.
How it watches the PC
Primary: WMI event notifications when processes start/stop (low overhead when it’s healthy).
Fallback: If WMI keeps failing, it temporarily polls (checks on a timer) so behavior doesn’t die completely.
It also runs checks after those events (and during polling) using which processes exist and which have visible windows (to know if a “main” app looks “in use”).
Profiles (the rules)
Each profile is roughly:

Main app(s): executables that represent “I’m using this product” (often “has a visible window” for one mode).
Bloat app(s): executables it is allowed to kill when the rule says so.
Mode (simplified):
Kill when main not visible: if none of the main apps have a visible window, it may kill the bloat list (respects cooldown).
Kill when main running: if a main app is running, it may kill the bloat list (respects cooldown).
Cooldown: avoids kill-spamming the same profile too often.
Edge-style safety: profiles can avoid killing msedgewebview2.exe when “protect WebView2” is on, and there is logic so main executables aren’t killed by default unless a profile explicitly allows that kind of overlap.
Startup behavior
Optional “purge on boot”: shortly after launch, it can kill matching bloat once for enabled profiles (still respects whitelist).
It can register with Windows startup (Run key) and self-heal the path if your Python/EXE location changes.
If you once had the interim “VoltWatch” startup entry, it can migrate that to the normal ProcessWatchdog key so you don’t double-start.

## What it does (everything)

### Core idea

- **Windows only.** It runs from the **system tray** and **ends (“kills”) processes** that you have configured as targets, using **profiles** (rules per app or preset).
- Goal: **fewer background processes** eating RAM/CPU — not a full system cleaner and not antivirus.

### How it watches your PC

- **Main path:** **WMI** — listens for process **create/delete** events so it can react without constantly scanning the whole machine.
- **Backup path:** If WMI/COM is flaky, it **falls back to timed polling** for a while so the app does not go completely blind.
- Each check uses:
  - **What is running** (process names), and  
  - **Which processes have a visible window** (to infer “main app looks in use” for common modes).

### Profiles (rules)

Each profile has:

- **Main app(s)** — executables that mean “this product is in play” (often tied to **visible windows**).
- **Bloat app(s)** — executables it is allowed to kill when the rule fires.
- **Mode** (typical):
  - **Kill when main not visible** — if **none** of the main apps have a **visible window**, it may kill targets from the bloat list (with cooldown).
  - **Kill when main running** — if a main app **is running**, it may kill the bloat list (with cooldown).
- **Cooldown per profile** — avoids kill-spam on the same profile.
- **Edge / WebView2** — optional protection so **`msedgewebview2.exe`** is not killed when that setting is on.
- **Main vs bloat overlap** — by default a profile **does not** kill executables listed as **main** unless the profile explicitly allows that (safer for misconfigured lists).

### On startup

- Optional **boot purge** — shortly after launch, can **kill matching bloat once** for enabled profiles (still respects the whitelist).
- Can **register with Windows** so it starts at login; the app **checks and fixes** the startup command if the EXE/Python path moves.
- If an old **“VoltWatch”** startup entry exists from an earlier build, it **migrates** to the normal **ProcessWatchdog** key so Windows does not launch two copies.

### Tray

- **Tray icon** (small lightning by default; optional **`tray_icon.png`** next to the EXE or script overrides the tray image).
- **Flashes** when something was killed.
- **Menu:** open dashboard, nuke all (manual), pause/resume, **Exit** (only this fully stops the background app).

### Dashboard (window)

- **Profiles** — enable/disable, kill counts, **nuke one profile** now.
- **App browser** — add built-in presets to your config in one click.
- **Kill history** — timestamp, profile, process names; can clear.
- **Log** — live tail of **`watchdog.log`** (rotating log next to the app).
- **Settings** — cooldown, WebView2 protection, boot purge toggle, **idle kill** tuning, close-button behavior, Windows startup register/remove, **About** (creator).
- **Important:** closing the **dashboard** is **not** the same as quitting the **tray app**. Use tray → **Exit** to fully stop Process Watchdog.

### Notifications

- **Windows toasts** (with a fallback) for pause/resume, kills, boot purge summaries, etc.

### Idle kill (optional, usually off)

- If you turn it on: finds processes that stay **very low CPU + low RAM** for a set time, then can kill them (whitelist still applies).
- Uses a **proper CPU sampling** approach so “idle” is less random than a single instant reading.

### Safety rails

- **Whitelist** — never kills listed core/system processes, the watchdog **EXE** itself, and related interpreters.
- **Pause** — global “do not kill anything” for a timed window.

### Files next to the EXE (or next to `watchdog.py` if you run from source)

- **`config.json`** — profiles and settings.
- **`kill_history.json`** — saved history (trimmed).
- **`watchdog.log`** — rotating log.

### What it does **not** do

- **Not** antivirus or malware removal.
- **Not** a safe “delete Windows components” tool — bad profiles can still kill apps **you** listed as bloat.
- **Not** macOS/Linux — Windows + WMI/COM assumptions.

---

## Get the app (install)

You only need **`ProcessWatchdog.exe`** in a folder you control (e.g. `C:\Apps\ProcessWatchdog\`). First run creates **`config.json`** and logs **next to that EXE**.

### Path 1 — GitHub Releases (simplest when a release exists)

1. Open **[Releases](https://github.com/somaqzz12/killswitch-for-all-apps-on-windows-/releases)**.
2. Pick the **latest** release.
3. Download **`ProcessWatchdog.exe`** (under **Assets**).
4. If Windows **SmartScreen** warns: **More info** → **Run anyway** (normal for unsigned indie EXEs).

### Path 2 — No release yet? Use GitHub Actions (official build)

1. Open **[Build Windows EXE](https://github.com/somaqzz12/killswitch-for-all-apps-on-windows-/actions/workflows/build-exe.yml)** (you must be logged into GitHub).
2. **Run workflow** → branch **`main`** → **Run workflow**.
3. Wait until the run is **green**.
4. Open that run → scroll to **Artifacts** → download **`ProcessWatchdog-windows.zip`**.
5. **Extract the ZIP** → inside is **`ProcessWatchdog.exe`**. Move it wherever you want and run it.

### Path 3 — Build on your own PC

1. Install **Python 3.10+** and check **`python`** works in a terminal.
2. Open this repo folder.
3. Double-click **`BUILD.bat`** (installs build deps, runs PyInstaller).
4. Output: **`dist\ProcessWatchdog.exe`**.

**If `BUILD.bat` says access denied on `dist\…`:** exit Process Watchdog from the **tray** first, then build again.

---

## First run

1. Run **`ProcessWatchdog.exe`**.
2. On the welcome screen, **turn on only the apps you understand** — you can add more later in **App Browser**.
3. Confirm the **tray icon** appears by the clock.
4. To **fully quit:** tray → **Exit** (closing the dashboard window does **not** stop the tray service).

---

## App icon (EXE / shortcut)

**`ProcessWatchdog.exe`** is built with **`icon.ico`**, generated from **`assets/app_icon.png`**. To change it: replace the PNG, run **`python scripts/make_icon.py`**, then **`BUILD.bat`**.

## Optional: tray picture (not the EXE icon)

Put **`tray_icon.png`** next to the EXE (or next to `watchdog.py` from source): **transparent PNG**, about **64×64**. That only changes the **tray** image, not the Windows file icon.

---

## Safety note

**Windows only.** It **ends processes**. Start conservative, use **Pause** if something misbehaves, and read **Settings → About**.

---

## Nerds

- From source: **`SETUP.bat`**, then **`python watchdog.py`**
- Startup CLI: **`python watchdog.py --register-startup`** / **`--unregister-startup`**
