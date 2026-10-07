"""
Async team/league logo cache.
Downloads happen on a small thread pool and are cached on disk; PhotoImages
are only created on the Tk main thread (Tk is not thread-safe).
"""

import hashlib
import io
import logging
import queue
import threading
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional, Tuple

from .. import config as C
from .. import net

log = logging.getLogger(__name__)

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
    HAVE_PIL = True
except Exception:  # pragma: no cover - Pillow is a declared dependency
    HAVE_PIL = False


class ImageCache:
    def __init__(self, root: tk.Misc, offline: bool = False):
        self.root = root
        self.offline = offline
        self._photos: Dict[Tuple[str, int], "ImageTk.PhotoImage"] = {}
        self._waiters: Dict[Tuple[str, int], List[Callable]] = {}
        self._failed: set = set()
        self._inflight: set = set()
        self._results: "queue.Queue[tuple]" = queue.Queue()
        self._pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="riftscout-img")
        self._lock = threading.Lock()

    # -------------------------------------------------------------- public
    def get(self, url: str, size: int, on_ready: Optional[Callable] = None, fallback_text: str = ""):
        """Return a PhotoImage now if cached; otherwise a placeholder, and call
        on_ready(photo) on the main thread once the real logo is loaded."""
        url = net.https(url or "")
        key = (url, size)
        if key in self._photos:
            return self._photos[key]
        placeholder = self.placeholder(fallback_text, size)
        if not url or not HAVE_PIL or url in self._failed or self.offline:
            return placeholder
        with self._lock:
            if on_ready:
                self._waiters.setdefault(key, []).append(on_ready)
            if key not in self._inflight:
                self._inflight.add(key)
                self._pool.submit(self._load, url, size)
        return placeholder

    def drain(self) -> None:
        """Called from the Tk loop: turn finished downloads into PhotoImages."""
        while True:
            try:
                url, size, pil_img = self._results.get_nowait()
            except queue.Empty:
                return
            key = (url, size)
            with self._lock:
                waiters = self._waiters.pop(key, [])
                self._inflight.discard(key)
            if pil_img is None:
                self._failed.add(url)
                continue
            try:
                photo = ImageTk.PhotoImage(pil_img, master=self.root)
            except Exception:
                continue
            self._photos[key] = photo
            for cb in waiters:
                try:
                    cb(photo)
                except tk.TclError:
                    pass  # widget was destroyed by a re-render

    def placeholder(self, text: str, size: int):
        key = ("__ph__" + (text or "?")[:4], size)
        if key in self._photos:
            return self._photos[key]
        if not HAVE_PIL:
            return None
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((1, 1, size - 2, size - 2), fill=(23, 38, 60, 255), outline=(200, 170, 110, 255))
        label = (text or "?")[:3].upper()
        try:
            f = ImageFont.truetype("segoeuib.ttf", max(8, int(size * (0.34 if len(label) > 2 else 0.42))))
        except Exception:
            f = ImageFont.load_default()
        bbox = d.textbbox((0, 0), label, font=f)
        d.text(((size - (bbox[2] - bbox[0])) / 2 - bbox[0], (size - (bbox[3] - bbox[1])) / 2 - bbox[1]),
               label, font=f, fill=(240, 230, 210, 255))
        photo = ImageTk.PhotoImage(img, master=self.root)
        self._photos[key] = photo
        return photo

    def clear_cache(self) -> int:
        count = 0
        try:
            for p in C.LOGO_CACHE_DIR.glob("*.png"):
                try:
                    p.unlink()
                    count += 1
                except OSError:
                    pass
            with self._lock:
                self._photos.clear()
                self._failed.clear()
        except Exception:
            pass
        return count

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)

    # -------------------------------------------------------------- worker side
    def _load(self, url: str, size: int) -> None:
        img = None
        try:
            path = C.LOGO_CACHE_DIR / (hashlib.sha1(url.encode()).hexdigest() + ".png")
            if path.exists() and path.stat().st_size > 0:
                raw = path.read_bytes()
            else:
                raw = net.fetch_bytes(url, timeout=10.0, max_retries=2, max_bytes=3 * 1024 * 1024)
                if raw:
                    path.write_bytes(raw)
            if raw:
                src = Image.open(io.BytesIO(raw))
                src.load()
                src = src.convert("RGBA")
                bbox = src.getbbox()  # trim transparent margins so logos fill the slot
                if bbox:
                    src = src.crop(bbox)
                src.thumbnail((size, size), Image.LANCZOS)
                img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                img.paste(src, ((size - src.width) // 2, (size - src.height) // 2), src)
        except Exception as exc:
            log.debug("Logo load failed for %s: %s", url, exc)
            img = None
        self._results.put((url, size, img))
