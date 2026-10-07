"""
RiftWatch System Tray Manager.
Runs a background tray icon via pystray with quick status, spoiler mode toggle,
refresh trigger, Ko-fi support, and window restore.
"""

import logging
import threading
from typing import Optional

try:
    from PIL import Image, ImageDraw
    import pystray
    HAVE_PYSTRAY = True
except ImportError:
    HAVE_PYSTRAY = False

from .. import config as C

log = logging.getLogger(__name__)


def create_tray_image():
    """Generate a crisp 64x64 Hextech emblem icon for the system tray."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Hextech gold circle
    d.ellipse((4, 4, 60, 60), fill=(9, 20, 40, 255), outline=(200, 170, 110, 255), width=4)
    # Magic teal diamond
    d.polygon([(32, 14), (50, 32), (32, 50), (14, 32)], outline=(10, 200, 185, 255), width=4)
    # Core gold jewel
    d.ellipse((26, 26, 38, 38), fill=(200, 170, 110, 255))
    return img


class TrayManager:
    def __init__(self, app):
        self.app = app
        self.icon: Optional[Any] = None
        self._thread: Optional[threading.Thread] = None
        self._notified_hide = False
        self.is_available = HAVE_PYSTRAY

    def start(self) -> None:
        if not self.is_available:
            log.info("pystray not available; running without system tray.")
            return

        def _open_app(icon=None, item=None):
            self.app.root.after(0, self.app.show_from_tray)

        def _toggle_spoiler(icon=None, item=None):
            self.app.root.after(0, self.app.toggle_spoiler)

        def _is_spoiler(item):
            return self.app.spoiler_on()

        def _refresh(icon=None, item=None):
            self.app.root.after(0, self.app.refresh)

        def _support(icon=None, item=None):
            self.app.root.after(0, lambda: self.app.open_url(C.KOFI_URL))

        def _exit(icon=None, item=None):
            self.app.root.after(0, self.app.close)

        def _watch_twitch(icon=None, item=None):
            self.app.root.after(0, lambda: self.app.open_url(C.TWITCH_CHANNEL_URL))

        def _watch_youtube(icon=None, item=None):
            self.app.root.after(0, lambda: self.app.open_url(C.YOUTUBE_LIVE_URL))

        menu = pystray.Menu(
            pystray.MenuItem("Open RiftWatch", _open_app, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Watch 24/7 Stream (YouTube)", _watch_youtube),
            pystray.MenuItem("Watch 24/7 Stream (Twitch)", _watch_twitch),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Spoiler Mode", _toggle_spoiler, checked=_is_spoiler),
            pystray.MenuItem("Refresh Schedule", _refresh),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("♥ Support on Ko-fi", _support),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit RiftWatch", _exit),
        )

        try:
            img = create_tray_image()
            self.icon = pystray.Icon("RiftWatch", img, "RiftWatch - LoL Esports Sentinel", menu)
            self._thread = threading.Thread(target=self._run, name="riftwatch-tray", daemon=True)
            self._thread.start()
        except Exception:
            log.exception("Failed to initialize system tray icon")
            self.is_available = False

    def _run(self) -> None:
        try:
            if self.icon:
                self.icon.run()
        except Exception:
            log.exception("Tray icon loop encountered an error")

    def notify_hidden(self) -> None:
        if not self.icon or self._notified_hide:
            return
        self._notified_hide = True
        try:
            if hasattr(self.icon, "notify"):
                self.icon.notify("RiftWatch is minimized to the system tray.", "RiftWatch")
        except Exception:
            pass

    def stop(self) -> None:
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
