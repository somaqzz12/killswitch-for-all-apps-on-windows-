"""
VoltWatch — Windows bloat janitor (cyberpunk edition)
=====================================================
Tray app + dashboard: onboarding, presets, kill history, pause, WMI engine, optional idle kill.
Optional custom tray art: place tray_icon.png (64×64-ish, transparent PNG) next to the script/exe.
"""

import os
import sys
import json
import time
import logging
import threading
import ctypes
import psutil
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────

# When packaged as .exe, use the folder next to the exe for user data
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

CONFIG_FILE  = BASE_DIR / "config.json"
LOG_FILE     = BASE_DIR / "voltwatch.log"
HISTORY_FILE = BASE_DIR / "kill_history.json"

# ─── Branding (edit here) ─────────────────────────────────────────────────────
APP_NAME         = "VoltWatch"
APP_VERSION      = "3.0"
APP_CREATOR      = "somaqzz12"
APP_TAGLINE      = "NEURAL BLOAT // ZERO TOLERANCE"
APP_EXE_NAME     = "VoltWatch.exe"  # PyInstaller output / whitelist

STARTUP_REG_KEY        = "VoltWatch"
STARTUP_REG_KEY_LEGACY = "ProcessWatchdog"  # migrated on first launch after rebrand

# ─── Logging ──────────────────────────────────────────────────────────────────

_logger = logging.getLogger()
_logger.setLevel(logging.INFO)
if not _logger.handlers:
    _handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8"
    )
    _handler.setFormatter(
        logging.Formatter(
            "%(asctime)s  %(levelname)-8s  %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    _logger.addHandler(_handler)

_log_callbacks     = []
_history_callbacks = []

def log(msg, level="INFO"):
    ts   = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    getattr(logging, level.lower(), logging.info)(msg)
    for cb in _log_callbacks:
        try: cb(line)
        except Exception: pass

# ─── Kill History ─────────────────────────────────────────────────────────────

_history = []   # list of dicts: {time, profile, processes}

def record_kill(profile_name, killed):
    entry = {
        "time":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profile":   profile_name,
        "processes": killed,
    }
    _history.insert(0, entry)
    if len(_history) > 500:
        _history.pop()
    # persist
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(_history[:200], f, indent=2)
    except Exception:
        pass
    for cb in _history_callbacks:
        try: cb(entry)
        except Exception: pass

def load_history():
    global _history
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE) as f:
                _history = json.load(f)
    except Exception:
        _history = []

# ─── Built-in Preset Library ──────────────────────────────────────────────────

PRESETS = [
    {
        "name":        "Adobe Creative Cloud",
        "icon":        "🎨",
        "description": "Kills CC background services when no Adobe app is open",
        "enabled":     True,
        "mode":        "kill_when_main_not_visible",
        "cooldown_seconds": 25,
        "main_apps":   ["Photoshop.exe","Premiere.exe","AfterFX.exe",
                        "Illustrator.exe","InDesign.exe","Lightroom.exe","Acrobat.exe"],
        "bloat_apps":  ["Creative Cloud.exe","Adobe Desktop Service.exe",
                        "CCXProcess.exe","CoreSync.exe","AdobeIPCBroker.exe",
                        "Creative Cloud Helper.exe","Creative Cloud UI Helper.exe",
                        "AdobeUpdateService.exe","AdobeNotificationClient.exe"],
    },
    {
        "name":        "Microsoft Edge",
        "icon":        "🌐",
        "description": "Kills Edge background processes when no Edge window is open",
        "enabled":     True,
        "mode":        "kill_when_main_not_visible",
        "cooldown_seconds": 30,
        "main_apps":   ["msedge.exe"],
        "bloat_apps":  ["msedge_proxy.exe", "MicrosoftEdgeUpdate.exe"],
        "allow_main_app_kill": False,
        "respect_protect_webview2": True,
    },
    {
        "name":        "Steam / Gaming",
        "icon":        "🎮",
        "description": "Kills Steam overlay & helpers while a game is running",
        "enabled":     False,
        "mode":        "kill_when_main_running",
        "cooldown_seconds": 60,
        "main_apps":   ["Cyberpunk2077.exe","EldenRing.exe","witcher3.exe",
                        "GTA5.exe","RDR2.exe","Minecraft.exe","valheim.exe"],
        "bloat_apps":  ["Steam.exe","steamwebhelper.exe","GameOverlayUI.exe"],
    },
    {
        "name":        "Discord",
        "icon":        "💬",
        "description": "Kills Discord crash service when Discord is closed",
        "enabled":     False,
        "mode":        "kill_when_main_not_visible",
        "cooldown_seconds": 30,
        "main_apps":   ["Discord.exe"],
        "bloat_apps":  ["DiscordCrashService.exe","DiscordPTB.exe"],
    },
    {
        "name":        "Spotify",
        "icon":        "🎵",
        "description": "Kills Spotify web helper when Spotify is closed",
        "enabled":     False,
        "mode":        "kill_when_main_not_visible",
        "cooldown_seconds": 30,
        "main_apps":   ["Spotify.exe"],
        "bloat_apps":  ["SpotifyCrashService.exe","SpotifyWebHelper.exe"],
    },
    {
        "name":        "Epic Games",
        "icon":        "🕹️",
        "description": "Kills Epic launcher background services when not in use",
        "enabled":     False,
        "mode":        "kill_when_main_not_visible",
        "cooldown_seconds": 30,
        "main_apps":   ["EpicGamesLauncher.exe"],
        "bloat_apps":  ["EpicWebHelper.exe","EpicOnlineServices.exe",
                        "EpicGamesLauncher.exe"],
    },
    {
        "name":        "NVIDIA GeForce Experience",
        "icon":        "🖥️",
        "description": "Kills GeForce background telemetry & overlay when not gaming",
        "enabled":     False,
        "mode":        "kill_when_main_not_visible",
        "cooldown_seconds": 60,
        "main_apps":   ["NVIDIA Share.exe","nvcontainer.exe"],
        "bloat_apps":  ["NvTelemetryContainer.exe","NvNodeLauncher.exe",
                        "NvOAWrapperCache.exe"],
    },
    {
        "name":        "Microsoft Teams",
        "icon":        "📋",
        "description": "Kills Teams background agent when Teams is closed",
        "enabled":     False,
        "mode":        "kill_when_main_not_visible",
        "cooldown_seconds": 30,
        "main_apps":   ["ms-teams.exe","Teams.exe"],
        "bloat_apps":  ["TeamsUpdateDaemon.exe","ms-teamsupdate.exe"],
    },
    {
        "name":        "Zoom",
        "icon":        "📹",
        "description": "Kills Zoom background helper when Zoom is closed",
        "enabled":     False,
        "mode":        "kill_when_main_not_visible",
        "cooldown_seconds": 30,
        "main_apps":   ["Zoom.exe"],
        "bloat_apps":  ["ZoomHelper.exe","CptHost.exe"],
    },
]

# ─── Default Config ───────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "first_run":                   True,
    "kill_cooldown_seconds":       25,
    "protect_webview2":            True,
    "kill_on_startup":             True,
    "minimize_to_taskbar_on_close": False,
    "idle_kill_enabled":           False,
    "idle_cpu_threshold_percent":  0.5,
    "idle_ram_mb_max":             50,
    "idle_duration_seconds":       120,
    "paused_until":                0,
    "whitelist": [
        "explorer.exe","svchost.exe","System","Registry",
        "lsass.exe","csrss.exe","winlogon.exe","dwm.exe",
        "taskmgr.exe","watchdog.exe","pythonw.exe","python.exe",
        "ProcessWatchdog.exe",
        APP_EXE_NAME,
    ],
    "profiles": PRESETS[:2],  # Adobe + Edge on by default
}

def load_config():
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        log(f"Created default config at {CONFIG_FILE}")
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    # back-fill any missing top-level keys from defaults
    for k, v in DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)
    return cfg

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

# ─── Pause Logic ──────────────────────────────────────────────────────────────

def is_paused(cfg):
    return time.time() < cfg.get("paused_until", 0)

def pause_for(cfg, minutes):
    cfg["paused_until"] = time.time() + minutes * 60
    save_config(cfg)
    log(f"{APP_NAME} paused for {minutes} minutes.")
    show_notification(APP_NAME, f"Grid chilled — {minutes} min silence.")

def unpause(cfg):
    cfg["paused_until"] = 0
    save_config(cfg)
    log(f"{APP_NAME} unpaused.")
    show_notification(APP_NAME, "Signal hot. VoltWatch is live again.")

# ─── Process Helpers ──────────────────────────────────────────────────────────

user32 = ctypes.windll.user32

def get_visible_process_names():
    visible = set()
    EnumWindowsProc = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
    )
    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                visible.add(psutil.Process(pid.value).name())
            except Exception:
                pass
        return True
    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return visible

def get_running_process_names():
    return {p.info["name"] for p in psutil.process_iter(attrs=["name"]) if p.info["name"]}


def build_tray_icon_pack():
    """(green, orange, grey) 64×64 RGBA icons. Put tray_icon.png next to the exe/script to override art."""
    from PIL import Image, ImageDraw

    custom = BASE_DIR / "tray_icon.png"
    if custom.exists():
        try:
            base = Image.open(custom).convert("RGBA").resize(
                (64, 64), Image.Resampling.LANCZOS
            )

            def overlay_tint(rgb, alpha):
                return Image.alpha_composite(
                    base, Image.new("RGBA", (64, 64), (*rgb, alpha))
                )

            return (
                base,
                overlay_tint((251, 146, 60), 100),
                overlay_tint((30, 41, 59), 140),
            )
        except Exception:
            pass

    def draw_one(ring):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((2, 2, 62, 62), fill=(8, 12, 22))
        d.ellipse((5, 5, 59, 59), outline=ring, width=3)
        bolt = (
            (32, 8),
            (40, 26),
            (32, 26),
            (45, 36),
            (36, 36),
            (24, 56),
            (28, 36),
            (22, 36),
            (30, 24),
            (24, 24),
        )
        d.polygon(bolt, fill=ring)
        return img

    return (
        draw_one((34, 211, 238)),
        draw_one((251, 146, 60)),
        draw_one((88, 100, 120)),
    )


_tray_ref = None

def _tray_flash():
    if _tray_ref and hasattr(_tray_ref, "_flash"):
        _tray_ref._flash()

def kill_processes(names, label="", whitelist=None):
    whitelist = whitelist or set()
    killed = []
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            pname = proc.info["name"]
            if pname in names and pname not in whitelist:
                proc.kill()
                killed.append(pname)
        except Exception:
            pass
    if killed:
        log(f"[{label}] Killed: {', '.join(killed)}")
        _tray_flash()
    return killed

# ─── Notifications ────────────────────────────────────────────────────────────

def show_notification(title, message):
    def _send():
        try:
            from windows_toasts import Toast, WindowsToaster
            toaster = WindowsToaster(APP_NAME)
            t = Toast()
            t.text_fields = [title, message]
            toaster.show_toast(t)
            return
        except Exception:
            pass
        try:
            from win10toast import ToastNotifier
            ToastNotifier().show_toast(title, message, duration=5, threaded=True)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()

def notify_kill(profile_name, killed):
    if not killed:
        return
    names = ", ".join(killed[:3])
    if len(killed) > 3:
        names += f" +{len(killed)-3} more"
    show_notification(f"{APP_NAME} // {profile_name}",
                      f"Killed {len(killed)}: {names}")

# ─── Idle Kill ────────────────────────────────────────────────────────────────

_idle_tracking = {}

def check_idle_kills(cfg, whitelist):
    if not cfg.get("idle_kill_enabled", False):
        return
    cpu_thresh = cfg.get("idle_cpu_threshold_percent", 0.5)
    ram_max    = cfg.get("idle_ram_mb_max", 50) * 1024 * 1024
    duration   = cfg.get("idle_duration_seconds", 120)
    now = time.time()
    tracked_pids = set()
    for proc in psutil.process_iter(["name", "pid", "memory_info"]):
        try:
            pname = proc.info["name"]
            if pname in whitelist:
                continue
            pid = proc.info["pid"]
            tracked_pids.add(pid)
            ram = (proc.info["memory_info"].rss if proc.info["memory_info"] else 0)
            state = _idle_tracking.get(pid)
            if state is None:
                # Prime psutil CPU meter for this PID on first encounter.
                proc.cpu_percent(interval=None)
                _idle_tracking[pid] = {"since": now, "primed": True}
                continue

            cpu = proc.cpu_percent(interval=None) or 0
            if cpu <= cpu_thresh and ram <= ram_max:
                if now - state["since"] >= duration:
                    proc.kill()
                    log(f"[IdleKill] {pname} (PID {pid})")
                    _idle_tracking.pop(pid, None)
            else:
                _idle_tracking.pop(pid, None)
        except Exception:
            pass
    # Cleanup stale PIDs that no longer exist.
    for pid in list(_idle_tracking.keys()):
        if pid not in tracked_pids:
            _idle_tracking.pop(pid, None)

# ─── Profile Watchdog ─────────────────────────────────────────────────────────

class ProfileWatchdog:
    def __init__(self, profile, global_cfg):
        self.profile     = profile
        self.global_cfg  = global_cfg
        self.name        = profile["name"]
        self.icon        = profile.get("icon", "⬡")
        self.enabled     = profile.get("enabled", True)
        self.mode        = profile.get("mode", "kill_when_main_not_visible")
        self.main_apps   = set(profile.get("main_apps", []))
        self.bloat_apps  = set(profile.get("bloat_apps", []))
        self.cooldown    = profile.get("cooldown_seconds",
                           global_cfg.get("kill_cooldown_seconds", 25))
        self.last_kill   = 0
        self.kills_total = 0

    def cooldown_ok(self):
        return time.time() - self.last_kill > self.cooldown

    def get_targets(self):
        t = self.bloat_apps.copy()
        if not self.profile.get("allow_main_app_kill", False):
            t -= self.main_apps
        if self.profile.get("respect_protect_webview2") and \
           self.global_cfg.get("protect_webview2", True):
            t.discard("msedgewebview2.exe")
        return t

    def check(self, visible, running, whitelist):
        if not self.enabled or is_paused(self.global_cfg):
            return []
        targets = self.get_targets()
        wl      = set(whitelist)
        killed  = []

        if self.mode == "kill_when_main_not_visible":
            if not any(m in visible for m in self.main_apps):
                if self.cooldown_ok():
                    killed = kill_processes(targets, self.name, wl)
        elif self.mode == "kill_when_main_running":
            if any(m in running for m in self.main_apps):
                if self.cooldown_ok():
                    killed = kill_processes(targets, self.name, wl)

        if killed:
            self.last_kill   = time.time()
            self.kills_total += len(killed)
            notify_kill(self.name, killed)
            record_kill(self.name, killed)
        return killed

# ─── Startup Kill ─────────────────────────────────────────────────────────────

def startup_kill(watchdogs, whitelist):
    log("Running startup bloat purge...")
    time.sleep(4)
    per_profile = {}
    for wd in watchdogs:
        if wd.enabled:
            killed = kill_processes(wd.get_targets(), f"Startup/{wd.name}", set(whitelist))
            if killed:
                per_profile[wd.name] = killed
                record_kill(f"Startup / {wd.name}", killed)

    total = [p for kills in per_profile.values() for p in kills]
    if total:
        log(f"Startup purge: killed {len(total)} — {', '.join(total)}")
        lines = []
        for name, kills in per_profile.items():
            short = ", ".join(kills[:2])
            if len(kills) > 2: short += f" +{len(kills)-2} more"
            lines.append(f"{name}: {short}")
        show_notification(f"{APP_NAME} // cold boot purge ({len(total)})",
                          "\n".join(lines))
    else:
        log("Startup purge: nothing to kill.")
        show_notification(APP_NAME, "Boot sequence clean. No junk in the stack.")

# ─── WMI / Poll Engine ────────────────────────────────────────────────────────

def run_watchdog_engine(watchdogs, global_cfg):
    whitelist = set(global_cfg.get("whitelist", []))
    fallback_until = 0
    recent_wmi_errors = []

    def do_check():
        visible = get_visible_process_names()
        running = get_running_process_names()
        for wd in watchdogs:
            wd.check(visible, running, whitelist)
        check_idle_kills(global_cfg, whitelist)

    try:
        import wmi
        try:
            import pythoncom
        except ImportError:
            pythoncom = None

        log("WMI event-driven mode active (near 0% idle CPU).")

        def listen(event_type):
            nonlocal fallback_until
            if pythoncom:
                pythoncom.CoInitialize()

            last_error_log = 0
            watcher = None
            try:
                while True:
                    try:
                        if time.time() < fallback_until:
                            time.sleep(2)
                            continue
                        # Build watcher inside the same thread that consumes it
                        # to avoid cross-thread COM errors.
                        if watcher is None:
                            conn = wmi.WMI()
                            watcher = conn.watch_for(
                                notification_type=event_type,
                                wmi_class="Win32_Process",
                                delay_secs=1
                            )
                        watcher()
                        do_check()
                    except Exception as e:
                        watcher = None
                        now = time.time()
                        recent_wmi_errors.append(now)
                        # Keep only recent window.
                        while recent_wmi_errors and now - recent_wmi_errors[0] > 120:
                            recent_wmi_errors.pop(0)
                        # If WMI is repeatedly failing, temporarily rely on polling.
                        if len(recent_wmi_errors) >= 6 and fallback_until < now + 60:
                            fallback_until = now + 300
                            log("WMI unstable; switched to temporary polling mode (5 min).", "WARN")
                        if now - last_error_log > 30:
                            log(f"WMI {event_type.lower()} watcher reset after error: {e}", "WARN")
                            last_error_log = now
                        time.sleep(2)
            finally:
                if pythoncom:
                    pythoncom.CoUninitialize()

        def poll_fallback():
            while True:
                if time.time() < fallback_until:
                    do_check()
                    time.sleep(7)
                else:
                    time.sleep(2)

        threading.Thread(target=listen, args=("Creation",), daemon=True).start()
        threading.Thread(target=listen, args=("Deletion",), daemon=True).start()
        threading.Thread(target=poll_fallback, daemon=True).start()

    except ImportError:
        log("wmi not found — polling fallback (7s). pip install wmi pywin32")
        def poll():
            while True:
                do_check()
                time.sleep(7)
        threading.Thread(target=poll, daemon=True).start()

# ─── GUI ──────────────────────────────────────────────────────────────────────

_win_ref  = None   # the CTk window
_win_lock = threading.Lock()
_manually_opened = False   # True when user opened it; False when auto-opened

def build_gui(watchdogs, global_cfg, start_on_tab=None):
    """Build and run the dashboard window. Must be called from a thread (not main)."""
    global _win_ref, _manually_opened

    try:
        import customtkinter as ctk
    except ImportError:
        import tkinter.messagebox as mb
        mb.showinfo(f"{APP_NAME}", "Missing UI kit. Run: pip install customtkinter")
        return

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    win = ctk.CTk()
    win.title(APP_NAME)
    win.geometry("820x660")
    win.minsize(700, 500)
    _win_ref = win

    # Keep in taskbar always
    win.wm_attributes("-toolwindow", False)

    # ── Header ────────────────────────────────────────────────────
    hdr = ctk.CTkFrame(win, fg_color="#0d0d0d", corner_radius=0, height=50)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)

    brand = ctk.CTkFrame(hdr, fg_color="transparent")
    brand.pack(side="left", padx=16, pady=8)
    ctk.CTkLabel(brand, text=f"⚡  {APP_NAME.upper()}",
                 font=ctk.CTkFont(family="Consolas", size=16, weight="bold"),
                 text_color="#22d3ee", anchor="w").pack(anchor="w")
    ctk.CTkLabel(brand, text=APP_TAGLINE,
                 font=ctk.CTkFont(family="Consolas", size=9),
                 text_color="#64748b", anchor="w").pack(anchor="w")

    pause_btn_var = ctk.StringVar(value="⏸  CHILL 30m")
    def toggle_pause():
        if is_paused(global_cfg):
            unpause(global_cfg)
            pause_btn_var.set("⏸  CHILL 30m")
            status_var.set("● LIVE")
        else:
            pause_for(global_cfg, 30)
            pause_btn_var.set("▶  RESUME")
            status_var.set("⏸ GHOSTED")

    ctk.CTkButton(hdr, textvariable=pause_btn_var, width=110, height=30,
                  fg_color="#374151", hover_color="#4b5563",
                  font=ctk.CTkFont(size=11),
                  command=toggle_pause).pack(side="right", padx=(0, 12))

    status_var = ctk.StringVar(value="⏸ GHOSTED" if is_paused(global_cfg) else "● LIVE")
    ctk.CTkLabel(hdr, textvariable=status_var,
                 font=ctk.CTkFont(family="Consolas", size=11),
                 text_color="#22d3ee").pack(side="right", padx=(0, 8))

    # ── Tabs ──────────────────────────────────────────────────────
    tabs = ctk.CTkTabview(win,
        fg_color="#111111",
        segmented_button_fg_color="#1a1a1a",
        segmented_button_selected_color="#0891b2",
        segmented_button_selected_hover_color="#0e7490",
        segmented_button_unselected_color="#1a1a1a",
        segmented_button_unselected_hover_color="#222",
    )
    tabs.pack(fill="both", expand=True, padx=8, pady=(4, 0))

    t_profiles = tabs.add("  Targets  ")
    t_browser  = tabs.add("  Loadout  ")
    t_history  = tabs.add("  Blackbox  ")
    t_log      = tabs.add("  Raw feed  ")
    t_settings = tabs.add("  Config  ")

    if start_on_tab:
        tabs.set(start_on_tab)

    # ═══════════════════════════════════════════════════════════════
    # TAB: PROFILES
    # ═══════════════════════════════════════════════════════════════

    def render_profiles():
        for w in prof_scroll.winfo_children():
            w.destroy()

        if not watchdogs:
            ctk.CTkLabel(prof_scroll, text="No targets armed.\nOpen Loadout and bolt some presets on.",
                         text_color="#6b7280", font=ctk.CTkFont(size=13)).pack(pady=40)
            return

        for wd in watchdogs:
            card = ctk.CTkFrame(prof_scroll, fg_color="#1a1a1a", corner_radius=8)
            card.pack(fill="x", pady=3, padx=2)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(10, 2))

            color = "#22d3ee" if wd.enabled else "#4b5563"
            ctk.CTkLabel(top, text=f"{wd.icon}  {wd.name}",
                         font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                         text_color=color).pack(side="left")

            ctk.CTkLabel(top, text=f"{wd.kills_total} purges",
                         font=ctk.CTkFont(family="Consolas", size=11),
                         text_color="#6b7280").pack(side="right")

            mode_text = "kills when closed" if "not_visible" in wd.mode else "kills while running"
            ctk.CTkLabel(top, text=mode_text,
                         font=ctk.CTkFont(size=10), text_color="#4b5563").pack(side="right", padx=12)

            if wd.main_apps & wd.bloat_apps:
                ctk.CTkLabel(card,
                             text="⚠ Hot stack: can drop the main exe when no window is visible.",
                             font=ctk.CTkFont(size=10), text_color="#f59e0b", anchor="w"
                             ).pack(fill="x", padx=14, pady=(0, 4))

            bloat_preview = "  ·  ".join(list(wd.bloat_apps)[:4])
            if len(wd.bloat_apps) > 4: bloat_preview += f"  +{len(wd.bloat_apps)-4} more"
            ctk.CTkLabel(card, text=bloat_preview,
                         font=ctk.CTkFont(family="Consolas", size=10),
                         text_color="#374151", anchor="w").pack(fill="x", padx=14, pady=(0, 6))

            btns = ctk.CTkFrame(card, fg_color="transparent")
            btns.pack(fill="x", padx=12, pady=(0, 10))

            def make_toggle(w=wd):
                def t():
                    w.enabled = not w.enabled
                    for p in global_cfg.get("profiles", []):
                        if p["name"] == w.name: p["enabled"] = w.enabled
                    save_config(global_cfg)
                    render_profiles()
                return t

            def make_nuke(w=wd):
                def n():
                    killed = kill_processes(w.get_targets(), f"Manual/{w.name}",
                                            set(global_cfg.get("whitelist", [])))
                    if killed:
                        record_kill(f"Manual / {w.name}", killed)
                        render_history()
                    render_profiles()
                return n

            toggle_color = "#374151" if wd.enabled else "#155e75"
            toggle_text  = "DISARM" if wd.enabled else "ARM"
            ctk.CTkButton(btns, text=toggle_text, width=85, height=26,
                          fg_color=toggle_color, hover_color="#4b5563",
                          font=ctk.CTkFont(size=11), command=make_toggle()).pack(side="left", padx=(0,6))
            ctk.CTkButton(btns, text="PURGE", width=85, height=26,
                          fg_color="#7f1d1d", hover_color="#991b1b",
                          font=ctk.CTkFont(size=11), command=make_nuke()).pack(side="left")

    prof_scroll = ctk.CTkScrollableFrame(t_profiles, fg_color="transparent")
    prof_scroll.pack(fill="both", expand=True, padx=4, pady=4)
    render_profiles()

    # ═══════════════════════════════════════════════════════════════
    # TAB: APP BROWSER
    # ═══════════════════════════════════════════════════════════════

    browser_scroll = ctk.CTkScrollableFrame(t_browser, fg_color="transparent")
    browser_scroll.pack(fill="both", expand=True, padx=4, pady=4)

    def render_browser():
        for w in browser_scroll.winfo_children():
            w.destroy()

        active_names = {wd.name for wd in watchdogs}

        ctk.CTkLabel(browser_scroll,
                     text="Preset loadout — bolt a stack, flip the switch, done.",
                     font=ctk.CTkFont(size=11), text_color="#6b7280").pack(anchor="w", padx=4, pady=(4,8))

        for preset in PRESETS:
            already = preset["name"] in active_names
            card = ctk.CTkFrame(browser_scroll, fg_color="#1a1a1a", corner_radius=8)
            card.pack(fill="x", pady=3, padx=2)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=10)

            ctk.CTkLabel(row, text=f"{preset.get('icon','⬡')}  {preset['name']}",
                         font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                         text_color="#e5e7eb" if not already else "#22d3ee"
                         ).pack(side="left")

            if already:
                ctk.CTkLabel(row, text="✓ ARMED",
                             font=ctk.CTkFont(size=11), text_color="#22d3ee").pack(side="right")
            else:
                def make_add(p=preset):
                    def add():
                        p_copy = dict(p)
                        global_cfg.setdefault("profiles", []).append(p_copy)
                        save_config(global_cfg)
                        new_wd = ProfileWatchdog(p_copy, global_cfg)
                        watchdogs.append(new_wd)
                        render_browser()
                        render_profiles()
                        log(f"Added profile: {p['name']}")
                    return add

                ctk.CTkButton(row, text="+ BOLT ON", width=90, height=26,
                              fg_color="#155e75", hover_color="#0e7490",
                              font=ctk.CTkFont(size=11),
                              command=make_add()).pack(side="right")

            ctk.CTkLabel(card, text=preset.get("description",""),
                         font=ctk.CTkFont(size=11), text_color="#6b7280",
                         anchor="w").pack(fill="x", padx=14, pady=(0,8))

    render_browser()

    # ═══════════════════════════════════════════════════════════════
    # TAB: KILL HISTORY
    # ═══════════════════════════════════════════════════════════════

    hist_scroll = ctk.CTkScrollableFrame(t_history, fg_color="transparent")
    hist_scroll.pack(fill="both", expand=True, padx=4, pady=4)

    hist_btn_row = ctk.CTkFrame(t_history, fg_color="transparent")
    hist_btn_row.pack(fill="x", padx=8, pady=(0,4))

    def render_history():
        for w in hist_scroll.winfo_children():
            w.destroy()
        if not _history:
            ctk.CTkLabel(hist_scroll, text="Blackbox empty. No purges logged yet.",
                         text_color="#4b5563", font=ctk.CTkFont(size=13)).pack(pady=40)
            return
        for entry in _history[:100]:
            row_f = ctk.CTkFrame(hist_scroll, fg_color="#1a1a1a", corner_radius=6)
            row_f.pack(fill="x", pady=2, padx=2)
            inner = ctk.CTkFrame(row_f, fg_color="transparent")
            inner.pack(fill="x", padx=10, pady=6)
            ctk.CTkLabel(inner, text=entry["time"],
                         font=ctk.CTkFont(family="Consolas", size=10),
                         text_color="#4b5563", width=140, anchor="w").pack(side="left")
            ctk.CTkLabel(inner, text=entry["profile"],
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#5eead4", width=180, anchor="w").pack(side="left", padx=(4,0))
            procs = ", ".join(entry["processes"])
            ctk.CTkLabel(inner, text=procs,
                         font=ctk.CTkFont(family="Consolas", size=10),
                         text_color="#9ca3af", anchor="w").pack(side="left", padx=(8,0))

    render_history()

    def clear_history():
        global _history
        _history = []
        try: HISTORY_FILE.unlink(missing_ok=True)
        except Exception: pass
        render_history()

    ctk.CTkButton(hist_btn_row, text="Wipe blackbox", width=120, height=26,
                  fg_color="#374151", hover_color="#4b5563",
                  font=ctk.CTkFont(size=11), command=clear_history).pack(side="left")

    # Live update history tab when a kill happens
    def on_new_kill(entry):
        try: render_history()
        except Exception: pass
    _history_callbacks.append(on_new_kill)

    # ═══════════════════════════════════════════════════════════════
    # TAB: LOG
    # ═══════════════════════════════════════════════════════════════

    log_box = ctk.CTkTextbox(t_log,
        font=ctk.CTkFont(family="Consolas", size=11),
        fg_color="#0a0a0a", text_color="#5eead4",
        wrap="word", state="disabled")
    log_box.pack(fill="both", expand=True, padx=4, pady=4)

    try:
        with open(LOG_FILE) as f:
            existing = f.read()[-10000:]
        log_box.configure(state="normal")
        log_box.insert("end", existing)
        log_box.configure(state="disabled")
        log_box.see("end")
    except Exception:
        pass

    def on_new_log(line):
        try:
            log_box.configure(state="normal")
            log_box.insert("end", line + "\n")
            log_box.configure(state="disabled")
            log_box.see("end")
        except Exception:
            pass
    _log_callbacks.append(on_new_log)

    log_btns = ctk.CTkFrame(t_log, fg_color="transparent")
    log_btns.pack(fill="x", padx=4, pady=(0,4))
    ctk.CTkButton(log_btns, text="Clear pane", width=100, height=26,
                  fg_color="#1f2937", hover_color="#374151",
                  font=ctk.CTkFont(size=11),
                  command=lambda: [log_box.configure(state="normal"),
                                   log_box.delete("1.0","end"),
                                   log_box.configure(state="disabled")]
                  ).pack(side="left", padx=(0,6))
    ctk.CTkButton(log_btns, text="Open log file", width=110, height=26,
                  fg_color="#1f2937", hover_color="#374151",
                  font=ctk.CTkFont(size=11),
                  command=lambda: os.startfile(str(LOG_FILE))).pack(side="left")

    # ═══════════════════════════════════════════════════════════════
    # TAB: SETTINGS
    # ═══════════════════════════════════════════════════════════════

    sf = ctk.CTkScrollableFrame(t_settings, fg_color="transparent")
    sf.pack(fill="both", expand=True, padx=4, pady=4)

    import tkinter as tk

    def section_label(text):
        ctk.CTkLabel(sf, text=text,
                     font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                     text_color="#6b7280").pack(anchor="w", padx=4, pady=(14,4))

    def entry_row(label, key, cast=int):
        f = ctk.CTkFrame(sf, fg_color="#1a1a1a", corner_radius=6)
        f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=12),
                     text_color="#d1d5db").pack(side="left", padx=12, pady=8)
        var = tk.StringVar(value=str(global_cfg.get(key, "")))
        ctk.CTkEntry(f, textvariable=var, width=100,
                     fg_color="#111", border_color="#374151",
                     font=ctk.CTkFont(family="Consolas", size=12)
                     ).pack(side="right", padx=12)
        return var, cast

    def switch_row(label, key):
        f = ctk.CTkFrame(sf, fg_color="#1a1a1a", corner_radius=6)
        f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=12),
                     text_color="#d1d5db").pack(side="left", padx=12, pady=8)
        var = ctk.BooleanVar(value=global_cfg.get(key, False))
        ctk.CTkSwitch(f, text="", variable=var, progress_color="#06b6d4",
                      button_color="#22d3ee",
                      command=lambda k=key, v=var: global_cfg.update({k: v.get()})
                      ).pack(side="right", padx=12)
        return var

    section_label("// CORE")
    v_cooldown, _ = entry_row("Kill cooldown (seconds)", "kill_cooldown_seconds", int)
    switch_row("Protect WebView2", "protect_webview2")
    switch_row("Kill bloat on startup", "kill_on_startup")
    switch_row("Minimize to taskbar when clicking X", "minimize_to_taskbar_on_close")

    section_label("// IDLE STRIKE")
    switch_row("Enable idle kill", "idle_kill_enabled")
    v_cpu, _  = entry_row("CPU threshold (%)", "idle_cpu_threshold_percent", float)
    v_ram, _  = entry_row("RAM max (MB)", "idle_ram_mb_max", int)
    v_dur, _  = entry_row("Idle duration (seconds)", "idle_duration_seconds", int)

    def save_settings():
        try:
            global_cfg["kill_cooldown_seconds"]      = int(v_cooldown.get())
            global_cfg["idle_cpu_threshold_percent"] = float(v_cpu.get())
            global_cfg["idle_ram_mb_max"]            = int(v_ram.get())
            global_cfg["idle_duration_seconds"]      = int(v_dur.get())
            save_config(global_cfg)
            log("Config committed.")
        except ValueError as e:
            log(f"Settings error: {e}", "WARN")

    section_label("// AUTOBOOT")
    s_row = ctk.CTkFrame(sf, fg_color="transparent")
    s_row.pack(fill="x", pady=2)
    ctk.CTkButton(s_row, text="Wire into boot", width=155, height=30,
                  fg_color="#1d4ed8", hover_color="#1e40af",
                  font=ctk.CTkFont(size=11), command=register_startup).pack(side="left", padx=(0,8))
    ctk.CTkButton(s_row, text="Strip from boot", width=155, height=30,
                  fg_color="#374151", hover_color="#4b5563",
                  font=ctk.CTkFont(size=11), command=unregister_startup).pack(side="left")

    section_label("// CREATOR")
    about_txt = (
        f"{APP_NAME} {APP_VERSION}\n"
        f"Built by {APP_CREATOR}\n\n"
        "Windows-only. It ends processes — stay sharp, hit CHILL if a stack misbehaves."
    )
    ctk.CTkLabel(
        sf,
        text=about_txt,
        font=ctk.CTkFont(size=11),
        text_color="#94a3b8",
        justify="left",
        anchor="w",
    ).pack(anchor="w", padx=6, pady=(0, 12))

    ctk.CTkButton(sf, text="COMMIT CONFIG", height=32,
                  fg_color="#0891b2", hover_color="#0e7490",
                  font=ctk.CTkFont(size=12, weight="bold"),
                  command=save_settings).pack(fill="x", pady=(14, 4), padx=2)

    # ── Footer / Nuke All ─────────────────────────────────────────
    footer = ctk.CTkFrame(win, fg_color="#0d0d0d", corner_radius=0, height=52)
    footer.pack(fill="x", side="bottom")
    footer.pack_propagate(False)

    def nuke_all():
        all_bloat = set()
        for wd in watchdogs:
            all_bloat |= wd.get_targets()
        killed = kill_processes(all_bloat, "NukeAll",
                                set(global_cfg.get("whitelist", [])))
        if killed:
            record_kill("Manual Nuke All", killed)
            render_history()
        log(f"Manual nuke all: {len(killed)} killed")

    ctk.CTkButton(footer, text="⚡  FULL GRID PURGE", height=36,
                  fg_color="#7f1d1d", hover_color="#991b1b",
                  font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                  command=nuke_all).pack(fill="x", padx=10, pady=8)

    # ── Window close behavior ─────────────────────────────────────
    def on_close():
        global _win_ref, _manually_opened
        try: _log_callbacks.remove(on_new_log)
        except ValueError: pass
        try: _history_callbacks.remove(on_new_kill)
        except ValueError: pass
        _win_ref = None
        _manually_opened = False
        win.destroy()

    # X button behavior is user-configurable in settings.
    def on_x():
        if global_cfg.get("minimize_to_taskbar_on_close", False):
            win.iconify()   # minimize to taskbar, stay in taskbar
        else:
            on_close()

    win.protocol("WM_DELETE_WINDOW", on_x)
    win.mainloop()

    # cleanup after window closes
    try: _history_callbacks.remove(on_new_kill)
    except ValueError: pass


def open_dashboard(watchdogs, global_cfg, tab=None, manual=True):
    global _win_ref, _manually_opened
    with _win_lock:
        if _win_ref is not None:
            try:
                if _win_ref.state() == "iconic":
                    _win_ref.deiconify()
                _win_ref.lift()
                _win_ref.focus_force()
                _manually_opened = manual
                return
            except Exception:
                _win_ref = None
        _manually_opened = manual
    threading.Thread(target=build_gui, args=(watchdogs, global_cfg, tab), daemon=True).start()

# ─── Onboarding ───────────────────────────────────────────────────────────────

def show_onboarding(watchdogs, global_cfg):
    """First-run welcome screen. Blocks until dismissed."""
    try:
        import customtkinter as ctk
    except ImportError:
        return

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    ob = ctk.CTkToplevel()
    ob.title(f"{APP_NAME} // handshake")
    ob.geometry("600x520")
    ob.resizable(False, False)
    ob.grab_set()

    ctk.CTkLabel(ob, text="⚡", font=ctk.CTkFont(size=48), text_color="#22d3ee").pack(pady=(24,4))
    ctk.CTkLabel(ob, text=APP_NAME,
                 font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
                 text_color="#f9fafb").pack()
    ctk.CTkLabel(ob,
                 text="Welcome to the sprawl. Junk stacks love empty RAM.\n"
                      "Flip the switches for stacks you want VoltWatch to strip when you're dark.\n"
                      "(You can rewire this anytime in Loadout.)",
                 font=ctk.CTkFont(size=12), text_color="#9ca3af",
                 wraplength=520, justify="center").pack(pady=(8, 16))

    scroll = ctk.CTkScrollableFrame(ob, fg_color="#111111", height=240)
    scroll.pack(fill="x", padx=20)

    switches = {}
    for preset in PRESETS:
        f = ctk.CTkFrame(scroll, fg_color="#1a1a1a", corner_radius=6)
        f.pack(fill="x", pady=3)
        var = ctk.BooleanVar(value=preset.get("enabled", False))
        switches[preset["name"]] = var

        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=8)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkLabel(left, text=f"{preset.get('icon','⬡')}  {preset['name']}",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#e5e7eb", anchor="w").pack(fill="x")
        ctk.CTkLabel(left, text=preset.get("description", ""),
                     font=ctk.CTkFont(size=10), text_color="#6b7280",
                     justify="left", anchor="w", wraplength=430).pack(fill="x", pady=(2, 0))

        ctk.CTkSwitch(row, text="", variable=var, progress_color="#06b6d4",
                      button_color="#22d3ee").pack(side="right")

    def finish():
        # If user selects a preset during onboarding, it should be enabled
        # regardless of that preset's library default state.
        selected = []
        for preset in PRESETS:
            if switches[preset["name"]].get():
                p = dict(preset)
                p["enabled"] = True
                selected.append(p)
        global_cfg["profiles"] = selected
        global_cfg["first_run"] = False
        save_config(global_cfg)
        watchdogs.clear()
        for p in selected:
            watchdogs.append(ProfileWatchdog(p, global_cfg))
        log(f"Onboarding complete. {len(selected)} profiles selected.")
        ob.destroy()

    ctk.CTkButton(ob, text="ARM THE GRID  →", height=40,
                  fg_color="#0891b2", hover_color="#0e7490",
                  font=ctk.CTkFont(size=13, weight="bold"),
                  command=finish).pack(fill="x", padx=20, pady=(16, 8))

    ctk.CTkLabel(ob, text="More stacks? Crack open the Loadout tab after boot.",
                 font=ctk.CTkFont(size=10), text_color="#4b5563").pack()

    ob.wait_window()

# ─── Tray ─────────────────────────────────────────────────────────────────────

class TrayIcon:
    def __init__(self, watchdogs, global_cfg):
        self.watchdogs  = watchdogs
        self.global_cfg = global_cfg
        self._flashing  = False

    def _flash(self): pass

    def run(self):
        from pystray import Icon, Menu, MenuItem

        img_green, img_orange, img_grey = build_tray_icon_pack()

        def open_dash(icon, item):
            global _manually_opened
            _manually_opened = True
            open_dashboard(self.watchdogs, self.global_cfg, manual=True)

        def nuke_all(icon, item):
            all_bloat = set()
            for wd in self.watchdogs: all_bloat |= wd.get_targets()
            killed = kill_processes(all_bloat, "TrayNuke",
                                    set(self.global_cfg.get("whitelist",[])))
            if killed: record_kill("Tray Nuke All", killed)

        def toggle_pause(icon, item):
            if is_paused(self.global_cfg):
                unpause(self.global_cfg)
            else:
                pause_for(self.global_cfg, 30)

        def quit_app(icon, item):
            log(f"{APP_NAME} exiting.")
            icon.stop()
            os._exit(0)

        icon = Icon(APP_NAME, img_green, f"{APP_NAME} — {APP_TAGLINE}",
            menu=Menu(
                MenuItem("Open console", open_dash, default=True),
                MenuItem("⚡ Purge all stacks", nuke_all),
                MenuItem(
                    lambda i: "▶ Resume" if is_paused(self.global_cfg) else "⏸ Chill 30 min",
                    toggle_pause),
                MenuItem("Kill VoltWatch", quit_app),
            )
        )

        def flash_impl():
            if self._flashing: return
            self._flashing = True
            def do():
                for _ in range(4):
                    icon.icon = img_orange; time.sleep(0.4)
                    icon.icon = img_green;  time.sleep(0.4)
                icon.icon = img_grey if is_paused(self.global_cfg) else img_green
                self._flashing = False
            threading.Thread(target=do, daemon=True).start()

        global _tray_ref
        _tray_ref    = self
        self._flash  = flash_impl

        log("Tray link established.")
        icon.run()

# ─── Startup Registry ─────────────────────────────────────────────────────────

def _exe_path():
    if getattr(sys, "frozen", False):
        return f'"{Path(sys.executable)}"'
    pythonw = Path(sys.executable).parent / "pythonw.exe"
    return f'"{pythonw}" "{Path(__file__).resolve()}"'

def register_startup():
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, STARTUP_REG_KEY, 0, winreg.REG_SZ, _exe_path())
        try:
            winreg.DeleteValue(key, STARTUP_REG_KEY_LEGACY)
            log("Removed legacy startup entry.")
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        log(f"Registered for startup: {_exe_path()}")
    except Exception as e:
        log(f"Startup registration failed: {e}", "ERROR")

def ensure_startup_registration():
    import winreg
    expected = _exe_path()
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ | winreg.KEY_SET_VALUE
        )
    except Exception as e:
        log(f"Startup self-heal skipped: {e}", "WARN")
        return
    try:
        current, _ = winreg.QueryValueEx(key, STARTUP_REG_KEY)
        if current != expected:
            winreg.SetValueEx(key, STARTUP_REG_KEY, 0, winreg.REG_SZ, expected)
            log("Startup registration path updated.")
    except FileNotFoundError:
        try:
            winreg.QueryValueEx(key, STARTUP_REG_KEY_LEGACY)
            winreg.SetValueEx(key, STARTUP_REG_KEY, 0, winreg.REG_SZ, expected)
            try:
                winreg.DeleteValue(key, STARTUP_REG_KEY_LEGACY)
            except FileNotFoundError:
                pass
            log("Startup registry migrated to new app key.")
        except FileNotFoundError:
            register_startup()
    except Exception as e:
        log(f"Startup self-heal skipped: {e}", "WARN")
    finally:
        try:
            winreg.CloseKey(key)
        except Exception:
            pass

def unregister_startup():
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        removed = False
        try:
            winreg.DeleteValue(key, STARTUP_REG_KEY)
            removed = True
        except FileNotFoundError:
            pass
        try:
            winreg.DeleteValue(key, STARTUP_REG_KEY_LEGACY)
            removed = True
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        if removed:
            log("Removed from startup.")
        else:
            log("Was not in startup registry.")
    except Exception as e:
        log(f"Startup removal failed: {e}", "ERROR")

# ─── Entry ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--register-startup" in sys.argv:
        register_startup(); sys.exit(0)
    if "--unregister-startup" in sys.argv:
        unregister_startup(); sys.exit(0)

    log("=" * 55)
    log(f"{APP_NAME} {APP_VERSION} — grid online.")

    load_history()
    cfg       = load_config()
    watchdogs = [ProfileWatchdog(p, cfg) for p in cfg.get("profiles", [])]

    # First run — show onboarding before anything else
    if cfg.get("first_run", True):
        # Need a root window to host the onboarding toplevel
        try:
            import customtkinter as ctk
            ctk.set_appearance_mode("dark")
            root = ctk.CTk()
            root.withdraw()
            show_onboarding(watchdogs, cfg)
            root.destroy()
        except Exception as e:
            log(f"Onboarding error: {e}", "WARN")
            cfg["first_run"] = False
            save_config(cfg)

    enabled = [w.name for w in watchdogs if w.enabled]
    log(f"Active profiles: {', '.join(enabled) or 'none'}")

    # Startup kill
    if cfg.get("kill_on_startup", True):
        threading.Thread(
            target=startup_kill,
            args=(watchdogs, set(cfg.get("whitelist", []))),
            daemon=True
        ).start()

    # Auto-register and self-heal startup registration path.
    ensure_startup_registration()

    # Start engine
    run_watchdog_engine(watchdogs, cfg)

    # Run tray on main thread
    TrayIcon(watchdogs, cfg).run()
