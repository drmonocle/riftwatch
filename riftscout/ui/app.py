"""
RiftScout main window.
Owns app state, drains the worker queue on the Tk thread, and re-renders the
visible tab only when the data it depends on changes.
"""

import logging
import logging.handlers
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Any, Dict, Optional

from .. import __version__
from .. import config as C
from .. import net
from .. import updater
from ..catalog import Catalog
from ..data import format_relative_time
from ..settings import SettingsManager
from ..stream import event_title, now_airing
from ..watchlist import Watchlist
from ..worker import Worker
from . import widgets as W
from .images import ImageCache
from .tray import TrayManager
from .views import LiveView, ScheduleView, SettingsView, StreamView, WatchlistView
from .wizard import OnboardingWizard

log = logging.getLogger(__name__)

TABS = (
    ("live", "● Live", LiveView),
    ("schedule", "Schedule", ScheduleView),
    ("stream", "24/7 Stream", StreamView),
    ("watchlist", "★ Watchlist", WatchlistView),
    ("settings", "Settings", SettingsView),
)
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "RiftWatch"


class RiftScoutApp:
    def __init__(self, root: tk.Tk, settings: Optional[SettingsManager] = None, start_worker: bool = True,
                 offline_images: bool = False, db_path=None):
        self.root = root
        self.settings = settings or SettingsManager()
        self.q: "queue.Queue[tuple]" = queue.Queue()
        self.state: Dict[str, Any] = {
            "schedule": [], "live": [], "livestats": {}, "stream": [], "stream_online": True,
            "catalog": Catalog(), "update": None, "update_checked": False, "update_progress": "", "status": {},
        }
        self.versions: Dict[str, int] = {}
        self.revealed: set = set()
        self.rendered: Dict[str, tuple] = {}
        self.watchlist = Watchlist(self.settings, self.state["catalog"])
        self.images = ImageCache(root, offline=offline_images)
        self.worker = Worker(self.settings, self.q, db_path=db_path)

        W.init_scale(root)
        root.title(f"RiftWatch {__version__}")
        root.configure(bg=C.COLOR_BG)
        root.minsize(W.px(820), W.px(560))
        geo = self.settings.get("window_geometry", "")
        root.geometry(geo if geo else f"{W.px(1000)}x{W.px(720)}")
        self._set_icon()
        self._build_chrome()

        self.views: Dict[str, tk.Frame] = {}
        for key, _, cls in TABS:
            v = cls(self.container, self)
            v.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.views[key] = v
        last = self.settings.get("last_tab", "live")
        self.active = last if last in self.views else "live"
        self.show_tab(self.active)

        self.tray = TrayManager(self)
        self.tray.start()

        root.protocol("WM_DELETE_WINDOW", self.on_close_requested)
        if start_worker:
            self.worker.start()
        self._poll()

        if not self.settings.get("onboarding_completed", False):
            self.root.after(350, self.open_onboarding_wizard)

    # ================================================================ chrome
    def _set_icon(self) -> None:
        try:
            from PIL import Image, ImageDraw, ImageTk
            img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.ellipse((2, 2, 61, 61), fill=(9, 20, 40, 255), outline=(200, 170, 110, 255), width=4)
            d.polygon([(32, 12), (48, 32), (32, 52), (16, 32)], outline=(10, 200, 185, 255), width=4)
            d.ellipse((27, 27, 37, 37), fill=(200, 170, 110, 255))
            self._icon = ImageTk.PhotoImage(img, master=self.root)
            self.root.iconphoto(True, self._icon)
        except Exception:
            pass

    def _build_chrome(self) -> None:
        r = self.root
        header = tk.Frame(r, bg=C.COLOR_BG_DARK)
        header.pack(fill="x")
        tk.Frame(r, bg=C.COLOR_GOLD, height=1).pack(fill="x")
        left = tk.Frame(header, bg=C.COLOR_BG_DARK)
        left.pack(side="left", padx=W.px(16), pady=W.px(10))
        W.label(left, "RIFTWATCH", 15, True, fg=C.COLOR_GOLD).pack(side="left")
        W.label(left, f" v{__version__}", 8, fg=C.COLOR_TEXT_DIM).pack(side="left", anchor="s", pady=(0, W.px(3)))

        right = tk.Frame(header, bg=C.COLOR_BG_DARK)
        right.pack(side="right", padx=W.px(12))
        self.b_refresh = W.button(right, "⟳ Refresh", self.refresh, size=9, tooltip="Refresh everything now")
        self.b_refresh.pack(side="right", padx=W.px(4))
        self.b_spoiler = W.button(right, "", self.toggle_spoiler, size=9,
                                  tooltip="Spoiler mode hides scores and results")
        self.b_spoiler.pack(side="right", padx=W.px(4))
        self.b_support = W.button(right, "♥ Support", lambda: self.open_url(C.KOFI_URL), size=9,
                                  bg="#720e9e", fg="white", hover_bg="#8c19bd",
                                  tooltip="Support RiftWatch on Ko-fi")
        self.b_support.pack(side="right", padx=W.px(4))
        self.b_update = W.button(right, "", self.install_update, size=9, bg=C.COLOR_GOLD, fg=C.COLOR_BG,
                                 hover_bg=C.COLOR_GOLD_HOVER)

        mid = tk.Frame(header, bg=C.COLOR_BG_DARK)
        mid.pack(side="left", fill="x", expand=True, padx=W.px(10))

        self.pill_live = tk.Frame(mid, bg=C.COLOR_SURFACE, highlightbackground=C.COLOR_BORDER,
                                  highlightthickness=1, cursor="hand2")
        self.pill_live.pack(side="left", padx=(0, W.px(6)), pady=W.px(2))
        self.l_live = tk.Label(self.pill_live, text="Pro Matches: Idle", font=W.font(9, True),
                               fg=C.COLOR_TEXT_DIM, bg=C.COLOR_SURFACE, cursor="hand2",
                               padx=W.px(8), pady=W.px(2))
        self.l_live.pack()
        self.pill_live.bind("<Button-1>", lambda e: self.show_tab("live"))
        self.l_live.bind("<Button-1>", lambda e: self.show_tab("live"))
        W.Tooltip(self.pill_live, "Click to view Live Pro Match action")

        self.sep_header = tk.Frame(mid, bg=C.COLOR_BORDER, width=1, height=W.px(16))
        self.sep_header.pack(side="left", padx=W.px(6))

        self.pill_stream = tk.Frame(mid, bg=C.COLOR_SURFACE, highlightbackground=C.COLOR_BORDER,
                                    highlightthickness=1, cursor="hand2")
        self.pill_stream.pack(side="left", padx=(W.px(6), 0), pady=W.px(2))
        self.l_stream = tk.Label(self.pill_stream, text="Twitch 24/7: ○ OFF AIR", font=W.font(9, False),
                                 fg=C.COLOR_TEXT_DIM, bg=C.COLOR_SURFACE, cursor="hand2",
                                 padx=W.px(8), pady=W.px(2))
        self.l_stream.pack()
        self.pill_stream.bind("<Button-1>", lambda e: self.show_tab("stream"))
        self.l_stream.bind("<Button-1>", lambda e: self.show_tab("stream"))
        W.Tooltip(self.pill_stream, "Click to view 24/7 Twitch Rebroadcast Schedule")

        tabbar = tk.Frame(r, bg=C.COLOR_BG)
        tabbar.pack(fill="x", padx=W.px(12), pady=(W.px(6), 0))
        self.tab_buttons: Dict[str, tuple] = {}
        for key, text, _ in TABS:
            f = tk.Frame(tabbar, bg=C.COLOR_BG)
            f.pack(side="left", padx=W.px(2))
            b = tk.Label(f, text=text, font=W.font(10, True), bg=C.COLOR_BG, fg=C.COLOR_TEXT_MUTED,
                         padx=W.px(14), pady=W.px(6), cursor="hand2")
            b.pack()
            line = tk.Frame(f, bg=C.COLOR_BG, height=W.px(2))
            line.pack(fill="x")
            b.bind("<Button-1>", lambda e, k=key: self.show_tab(k))
            self.tab_buttons[key] = (b, line)
        tk.Frame(r, bg=C.COLOR_BORDER, height=1).pack(fill="x")

        footer = tk.Frame(r, bg=C.COLOR_BG_DARK)
        footer.pack(side="bottom", fill="x")
        self.l_status = W.label(footer, "Starting…", 8, fg=C.COLOR_TEXT_MUTED)
        self.l_status.pack(side="left", padx=W.px(12), pady=W.px(4))
        self.b_hide_tray = W.button(footer, "🗕 Hide to Tray", self.hide_to_tray, size=8, bold=False,
                                    bg=C.COLOR_SURFACE, fg=C.COLOR_TEXT_MUTED, hover_bg=C.COLOR_SURFACE_HOVER,
                                    tooltip="Minimize RiftWatch to system notification area")
        self.b_hide_tray.pack(side="right", padx=W.px(8), pady=W.px(2))
        self.l_tag = tk.Label(footer, text="Monocle Productions LLC", font=W.font(8, True),
                              fg=C.COLOR_TEXT_DIM, bg=C.COLOR_BG_DARK, cursor="hand2")
        self.l_tag.pack(side="right", padx=W.px(10), pady=W.px(4))
        self.l_tag.bind("<Enter>", lambda e: self.l_tag.configure(fg=C.COLOR_GOLD))
        self.l_tag.bind("<Leave>", lambda e: self.l_tag.configure(fg=C.COLOR_TEXT_DIM))
        self.l_tag.bind("<Button-1>", lambda e: self.open_url(C.PORTAL_URL))
        W.Tooltip(self.l_tag, "Monocle Productions LLC · drmonocle.com")
        self.l_spoiler_foot = W.label(footer, "", 8, True, fg=C.COLOR_GOLD)
        self.l_spoiler_foot.pack(side="right", padx=W.px(8))

        self.container = tk.Frame(r, bg=C.COLOR_BG)
        self.container.pack(fill="both", expand=True)
        self._refresh_header()

    def _refresh_header(self) -> None:
        live = self.state["live"]
        if live:
            first = live[0]
            more = f"  +{len(live) - 1} more" if len(live) > 1 else ""
            self.l_live.configure(text=f"● LIVE  {first['team1_code']} vs {first['team2_code']} "
                                       f"({first['league_name']}){more}", fg=C.COLOR_LIVE)
            self.pill_live.configure(highlightbackground=C.COLOR_LIVE)
        else:
            self.l_live.configure(text="Pro Matches: Idle", fg=C.COLOR_TEXT_DIM)
            self.pill_live.configure(highlightbackground=C.COLOR_BORDER)

        cur = now_airing(self.state["stream"]) if self.state["stream"] else None
        online = self.state.get("stream_online", True)
        if online is False or not cur:
            self.l_stream.configure(text="Twitch 24/7: Offline", fg=C.COLOR_TEXT_DIM, font=W.font(9, False))
            self.pill_stream.configure(highlightbackground=C.COLOR_BORDER)
        else:
            self.l_stream.configure(text=f"Twitch 24/7: {event_title(cur)}", fg=C.COLOR_CYAN, font=W.font(9, True))
            self.pill_stream.configure(highlightbackground=C.COLOR_CYAN_DIM)
        on = self.spoiler_on()
        W.set_button_colors(self.b_spoiler, C.COLOR_GOLD if on else C.COLOR_SURFACE_HOVER,
                            C.COLOR_BG if on else C.COLOR_TEXT_PRIMARY)
        self.b_spoiler.configure(text="Spoilers hidden" if on else "Spoilers shown")
        self.l_spoiler_foot.configure(text="SPOILER MODE ON: scores hidden" if on else "")
        info = self.state["update"]
        if info and not self.b_update.winfo_ismapped():
            self.b_update.configure(text=f"⬆ Update to {info['tag']}")
            self.b_update.pack(side="right", padx=W.px(4))
        elif not info and self.b_update.winfo_ismapped():
            self.b_update.pack_forget()

    def _refresh_status(self) -> None:
        st = self.state["status"]
        bad = [k for k, v in st.items() if not v.get("ok")]
        if not st:
            text = "Connecting to data sources…"
        elif bad:
            text = "⚠ " + "; ".join(st[k].get("detail", k) for k in bad)
        else:
            text = "All data sources up to date"
        self.l_status.configure(text=text, fg=C.COLOR_LIVE if bad else C.COLOR_TEXT_MUTED)

    # ================================================================ state
    def bump(self, key: str) -> None:
        self.versions[key] = self.versions.get(key, 0) + 1

    def _poll(self) -> None:
        changed = False
        try:
            while True:
                kind, payload = self.q.get_nowait()
                changed = True
                self._apply(kind, payload)
        except queue.Empty:
            pass
        self.images.drain()
        if changed:
            self._refresh_header()
            self._refresh_status()
        self._render_active()
        self._poll_id = self.root.after(150, self._poll)

    def _apply(self, kind: str, payload: Any) -> None:
        if kind == "status":
            self.state["status"][payload["source"]] = payload
            self.bump("status")
        elif kind == "catalog":
            if self.state.get("catalog") != payload:
                self.state["catalog"] = payload
                self.watchlist.set_catalog(payload)
                if self.settings.attach_team_names(lambda code: (payload.find_team(code) or {}).get("name")):
                    self.bump("prefs")
                self.bump("catalog")
        elif kind == "update":
            self.state["update"] = payload
            self.state["update_checked"] = True
            self.bump("update")
        elif kind == "update_progress":
            self.state["update_progress"] = payload
            self.bump("update_progress")
        elif kind == "update_ready":
            self._finish_update(payload)
        elif kind == "update_error":
            self.state["update_progress"] = ""
            self.bump("update_progress")
            messagebox.showerror("RiftWatch update", payload, parent=self.root)
        elif kind == "refresh_done":
            self.b_refresh.configure(text="⟳ Refresh")
        elif kind == "stream_online":
            if self.state.get("stream_online") != payload:
                self.state["stream_online"] = payload
                self.bump("stream")
        elif kind in ("schedule", "live", "livestats", "stream"):
            new_val = payload or ([] if kind != "livestats" else {})
            if self.state.get(kind) != new_val:
                self.state[kind] = new_val
                self.bump(kind)

    def _render_active(self) -> None:
        v = self.views[self.active]
        sig = v.signature()
        if self.rendered.get(self.active) != sig:
            self.rendered[self.active] = sig
            try:
                v.render()
            except Exception:
                log.exception("Render failed for %s", self.active)

    def request_render(self, view) -> None:
        for k, v in self.views.items():
            if v is view:
                self.rendered.pop(k, None)

    # ================================================================ actions
    def show_tab(self, key: str) -> None:
        self.active = key
        for k, (b, line) in self.tab_buttons.items():
            on = k == key
            b.configure(fg=C.COLOR_GOLD if on else C.COLOR_TEXT_MUTED)
            line.configure(bg=C.COLOR_GOLD if on else C.COLOR_BG)
        self.views[key].tkraise()
        self.settings.set("last_tab", key)
        self._render_active()

    def spoiler_on(self) -> bool:
        return bool(self.settings.get("spoiler_mode", False))

    def is_revealed(self, match_id: str) -> bool:
        return match_id in self.revealed

    def reveal(self, match_id: str) -> None:
        self.revealed.add(match_id)
        self.bump("prefs")

    def toggle_spoiler(self) -> None:
        self.settings.set("spoiler_mode", not self.spoiler_on())
        self.revealed.clear()
        self.bump("prefs")
        self._refresh_header()

    def toggle_team(self, code: str, name: str = "") -> None:
        self.settings.toggle_team(code, name)
        self.bump("prefs")

    def toggle_player(self, name: str) -> None:
        self.settings.toggle_player(name)
        self.bump("prefs")

    def toggle_league(self, slug: str) -> None:
        self.settings.toggle_league(slug)
        self.bump("prefs")

    def follow_leagues(self, slugs) -> None:
        for s in slugs:
            if not self.settings.is_league_followed(s):
                self.settings.toggle_league(s)
        self.bump("prefs")

    def toggle_region(self, region_name: str) -> None:
        self.settings.toggle_region(region_name)
        self.bump("prefs")

    def follow_all_regions(self) -> None:
        for r in C.MAJOR_REGIONS:
            if not self.settings.is_region_followed(r["name"]):
                self.settings.toggle_region(r["name"])
        self.bump("prefs")

    def unfollow_all_regions(self) -> None:
        self.settings.set("followed_regions", [])
        self.bump("prefs")

    def open_onboarding_wizard(self) -> None:
        OnboardingWizard(self.root, self)

    def on_close_requested(self) -> None:
        if self.settings.get("minimize_to_tray_on_close", True) and getattr(self, "tray", None) and self.tray.is_available:
            self.hide_to_tray()
        else:
            self.close()

    def hide_to_tray(self) -> None:
        try:
            if self.root.state() == "normal":
                self.settings.set("window_geometry", self.root.geometry())
        except tk.TclError:
            pass
        self.root.withdraw()
        if getattr(self, "tray", None):
            self.tray.notify_hidden()

    def show_from_tray(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def open_url(self, url: str) -> None:
        if not net.open_in_browser(url):
            messagebox.showwarning("RiftWatch", "That link couldn't be opened.", parent=self.root)

    def watch(self, match: Dict[str, Any]) -> None:
        url = (match.get("stream_url") or "").strip()
        if not url:
            league = match.get("league_name") or match.get("league_slug") or "LoL Esports"
            t1 = match.get("team1_name") or match.get("team1_code") or ""
            t2 = match.get("team2_name") or match.get("team2_code") or ""
            query = f"LoL Esports {league} {t1} vs {t2}".strip()
            import urllib.parse
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
        self.open_url(url)

    def refresh(self) -> None:
        self.b_refresh.configure(text="⟳ Refreshing…")
        self.worker.request("schedule", "live", "stream")

    def worker_request(self, *jobs: str) -> None:
        self.worker.request(*jobs)

    def check_updates(self) -> None:
        self.worker.request("update")

    # ---- autostart
    def _autostart_command(self) -> str:
        if updater.is_frozen():
            return f'"{Path(sys.executable).resolve()}"'
        pyw = Path(sys.executable).with_name("pythonw.exe")
        launcher = Path(__file__).resolve().parents[2] / "run_riftscout.pyw"
        return f'"{pyw if pyw.exists() else sys.executable}" "{launcher}"'

    def toggle_autostart(self) -> None:
        want = not self.settings.get("start_with_windows", False)
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
                if want:
                    winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, self._autostart_command())
                else:
                    try:
                        winreg.DeleteValue(k, RUN_NAME)
                    except FileNotFoundError:
                        pass
            self.settings.set("start_with_windows", want)
        except Exception as exc:
            log.exception("Autostart change failed")
            messagebox.showerror("RiftScout", f"Couldn't change the startup setting:\n{exc}", parent=self.root)
        self.bump("prefs")

    # ---- updates
    def install_update(self) -> None:
        info = self.state["update"]
        if not info or self.state["update_progress"]:
            return
        if not updater.is_frozen():
            messagebox.showinfo(
                "RiftScout update",
                f"Version {info['tag']} is available.\n\nYou're running RiftScout from source, so update "
                "with `git pull` in the project folder.", parent=self.root)
            return
        if not messagebox.askyesno("RiftScout update",
                                   f"Download RiftScout {info['tag']}, verify it, and restart now?",
                                   parent=self.root):
            return

        def progress(done: int, total: int) -> None:
            pct = f"{done * 100 // total}%" if total else f"{done // 1024} KB"
            self.q.put(("update_progress", f"Downloading {info['tag']}… {pct}"))

        def run() -> None:
            try:
                self.q.put(("update_progress", "Checking release checksum…"))
                path = updater.download_update(info, progress)
                self.q.put(("update_progress", "Verified. Restarting…"))
                self.q.put(("update_ready", str(path)))
            except updater.UpdateError as exc:
                self.q.put(("update_error", str(exc)))
            except Exception as exc:
                log.exception("Update failed")
                self.q.put(("update_error", f"Update failed: {exc}"))

        threading.Thread(target=run, name="riftwatch-update", daemon=True).start()
        self.show_tab("settings")

    def clear_logo_cache(self) -> None:
        count = self.images.clear_cache()
        self.bump("prefs")
        messagebox.showinfo("Logo Cache", f"Cleared {count} cached team logo files.", parent=self.root)

    def reset_watchlist(self) -> None:
        if messagebox.askyesno("Reset Watchlist",
                               "Are you sure you want to unfollow all teams, players, leagues, and regions?",
                               parent=self.root):
            self.settings.reset_all_follows()
            self.bump("prefs")
            messagebox.showinfo("Reset Watchlist", "Watchlist has been cleared.", parent=self.root)

    def open_logs(self) -> None:
        if C.LOG_PATH.exists():
            os.startfile(str(C.LOG_PATH))
        else:
            os.startfile(str(C.APPDATA_DIR))

    def _finish_update(self, path: str) -> None:
        try:
            _release_single_instance()
            updater.launch_swap_and_restart(Path(path))
        except Exception as exc:
            self.state["update_progress"] = ""
            self.bump("update_progress")
            messagebox.showerror("RiftWatch update", str(exc), parent=self.root)
            return
        self.close()
        try:
            self.root.quit()
        except Exception:
            pass
        sys.exit(0)

    # ---- shutdown
    def close(self) -> None:
        try:
            if self.root.state() == "normal":
                self.settings.set("window_geometry", self.root.geometry())
        except tk.TclError:
            pass
        if getattr(self, "tray", None):
            self.tray.stop()
        self.worker.stop()
        self.images.shutdown()
        try:
            self.root.after_cancel(self._poll_id)
        except Exception:
            pass
        _release_single_instance()
        self.root.destroy()


# ==================================================================== entry
def _setup_logging() -> None:
    import logging.handlers
    handler = logging.handlers.RotatingFileHandler(C.LOG_PATH, maxBytes=1_000_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def _single_instance() -> bool:
    """Return False if another RiftWatch window is already running."""
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        _single_instance.handle = kernel32.CreateMutexW(None, False, "Local\\RiftWatchSingleInstance")
        return kernel32.GetLastError() != 183  # ERROR_ALREADY_EXISTS
    except Exception:
        return True


def _release_single_instance() -> None:
    handle = getattr(_single_instance, "handle", None)
    if handle:
        try:
            import ctypes
            ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            pass
        _single_instance.handle = None


def run() -> None:
    _setup_logging()
    if not _single_instance():
        log.info("Another instance is already running; exiting.")
        return
    W.enable_dpi_awareness()
    root = tk.Tk()
    root.option_add("*Background", C.COLOR_BG)
    root.option_add("*Foreground", C.COLOR_TEXT_PRIMARY)
    RiftScoutApp(root)
    try:
        root.mainloop()
    finally:
        _release_single_instance()
