# Process Watchdog

**In plain English:** a small Windows app that sits in your **system tray** and can **close leftover background programs** when you are not actively using the “main” app (for example helpers/updaters). You choose which apps it manages on first run and in the dashboard.

**Important:** this tool **ends processes**. Use it only if you understand that, start with **defaults / fewer profiles**, and use **Pause** if something misbehaves. It is **Windows-only**.

---

## I just want the app (no coding)

You need a single file: **`ProcessWatchdog.exe`**. Pick **one** path below (they all produce the same app).

### A) Download from Releases (simplest, when it exists)

1. Open **[Releases](https://github.com/somaqzz12/killswitch-for-all-apps-on-windows-/releases)**.
2. Open the **latest** release and download **`ProcessWatchdog.exe`**.

If Releases is **empty** or has **no EXE attached yet**, use **B** or **C** — that is normal until the maintainer publishes a release.

### B) Download from GitHub Actions (no Python needed)

This uses the automated Windows build on GitHub.

1. Open **[Actions → Build Windows EXE](https://github.com/somaqzz12/killswitch-for-all-apps-on-windows-/actions/workflows/build-exe.yml)**.
2. Click **Run workflow** → branch **main** → **Run workflow** (you must be logged in and have permission on this repo).
3. Wait for the run to finish (green check).
4. Open that run → scroll to **Artifacts** → download **`ProcessWatchdog-windows`** (ZIP). Inside is **`ProcessWatchdog.exe`**.

### C) Build on your own PC (needs Python once)

1. Install **Python 3.10+** for Windows and clone or download this repo as a ZIP and extract it.
2. Double-click **`BUILD.bat`** in the project folder.
3. Take **`dist\ProcessWatchdog.exe`**.

### After you have the EXE

1. Double-click **`ProcessWatchdog.exe`**. Pick apps in the welcome screen. A **tray icon** appears near the clock.
2. **Fully quit:** right-click the tray icon → **Exit**. Closing the dashboard window does **not** stop the background watchdog until you **Exit** from the tray.

---

## Key features

- Event-driven process monitoring with WMI (with fallback polling when WMI is unstable)
- Profile-based kill rules with per-profile cooldowns
- First-run onboarding and built-in preset library
- Kill history and live log viewer
- Startup registration self-healing
- Optional idle-kill logic
- Configurable close behavior (`X` can close or minimize)

## Install and run (developers)

### End users (EXE)

Same as **“I just want the app”** above: Releases **or** Actions artifact **or** `BUILD.bat` → `ProcessWatchdog.exe`.

### Developers (source)

1. Install Python 3.10+ on Windows.
2. Run `SETUP.bat`.
3. Launch manually any time with `python watchdog.py`.

## Build EXE

- Local build: run `BUILD.bat`
- Output: `dist/ProcessWatchdog.exe`
- CI build: GitHub Action workflow at `.github/workflows/build-exe.yml`

## Recommended settings presets

- Balanced
  - `kill_cooldown_seconds`: `30`
  - `idle_kill_enabled`: `false`
  - `kill_on_startup`: `true`
- Aggressive
  - `kill_cooldown_seconds`: `15`
  - `idle_kill_enabled`: `true`
  - `idle_cpu_threshold_percent`: `0.5`
  - `idle_ram_mb_max`: `80`
  - `idle_duration_seconds`: `180`
- Gaming
  - `kill_cooldown_seconds`: `60`
  - `idle_kill_enabled`: `false`
  - Keep only gaming-related profiles enabled

## Dashboard overview

- `Profiles`: enable/disable rules and run per-profile nuke
- `App Browser`: add built-in presets
- `Kill History`: recent actions
- `Log`: runtime log stream
- `Settings`: cooldown, startup, idle kill, close behavior

## Close and exit behavior

- Clicking `X`: closes dashboard by default
- Optional: enable `Minimize to taskbar when clicking X` in Settings
- Full app exit: tray icon -> `Exit`

## Startup management

- Register: `python watchdog.py --register-startup`
- Unregister: `python watchdog.py --unregister-startup`

## Custom profile format

Add entries in `config.json` under `profiles`:

```json
{
  "name": "My App",
  "icon": "🔧",
  "description": "Kills helper processes when app is closed",
  "enabled": true,
  "mode": "kill_when_main_not_visible",
  "cooldown_seconds": 30,
  "main_apps": ["MyApp.exe"],
  "bloat_apps": ["MyAppHelper.exe", "MyAppUpdater.exe"],
  "allow_main_app_kill": false
}
```

## Release process

Follow `RELEASE_CHECKLIST.md` for professional GitHub releases with EXE artifacts.
