# VoltWatch

**Cyberpunk-flavored bloat hunter for Windows.** It chills in your tray and clears junk processes when you are not actually using the “main” app. Flip a few switches on first run, then forget it exists — until your RAM breathes again.

Built by **[somaqzz12](https://github.com/somaqzz12)**.

---

## Grab the app

You want **`VoltWatch.exe`**. Three ways:

### 1) Releases (easiest, when it is there)

[Releases](https://github.com/somaqzz12/killswitch-for-all-apps-on-windows-/releases) → latest → download **`VoltWatch.exe`**.

### 2) GitHub Actions (no Python on your machine)

[Build Windows EXE](https://github.com/somaqzz12/killswitch-for-all-apps-on-windows-/actions/workflows/build-exe.yml) → **Run workflow** → wait for green → **Artifacts** → **`VoltWatch-windows`** (ZIP) → inside is **`VoltWatch.exe`**.

### 3) Build it yourself

Install Python, open this folder, double-click **`BUILD.bat`**, grab **`dist\VoltWatch.exe`**.

---

## First run

1. Run **`VoltWatch.exe`**.
2. Pick your stacks on the handshake screen (you can change later).
3. Spot the **tray icon** by the clock — that means the grid is live.
4. **Really quit:** tray menu → **Kill VoltWatch**. Closing the window only closes the dashboard.

---

## Custom tray icon (optional)

Drop a **`tray_icon.png`** next to the EXE (or next to `watchdog.py` if you run from source). Transparent PNG, roughly **64×64** — VoltWatch will use it instead of the default lightning glyph.

---

## Heads-up

- **Windows only.** It **ends processes**. Start conservative, use **CHILL** (pause) if something acts weird.
- Logs live next to the app: **`voltwatch.log`**.

---

## Nerds corner

- From source: `SETUP.bat` then `python watchdog.py`
- Startup keys: `python watchdog.py --register-startup` / `--unregister-startup`
