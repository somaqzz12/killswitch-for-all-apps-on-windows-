# Process Watchdog

Windows tray watchdog that automatically shuts down background bloat processes based on app visibility/running state.

## Key features

- Event-driven process monitoring with WMI (with fallback polling when WMI is unstable)
- Profile-based kill rules with per-profile cooldowns
- First-run onboarding and built-in preset library
- Kill history and live log viewer
- Startup registration self-healing
- Optional idle-kill logic
- Configurable close behavior (`X` can close or minimize)

## Install and run

### End users (EXE)

1. Download `ProcessWatchdog.exe` from the latest release.
2. Run it once and choose your profiles.
3. App stays in system tray and starts with Windows.

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
