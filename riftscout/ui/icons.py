"""
RiftWatch Icon System.
Provides high-resolution Vector Rift Herald branding for the Windows Taskbar,
System Notification Tray, Alt-Tab switcher, and Window Titlebar.
"""

import base64
import io
import logging
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageTk
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

log = logging.getLogger(__name__)

# Fallback base64 representation of the 64x64 Vector Rift Herald icon
VECTOR_HERALD_B64_64 = (
    "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"
    "rkJggg=="
)


def get_app_icon_ico_path() -> Optional[str]:
    """Finds the native Windows multi-resolution app.ico file."""
    candidates = []
    # 1. PyInstaller frozen temporary dir
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "app.ico"))
        candidates.append(os.path.join(sys._MEIPASS, "riftscout", "assets", "app.ico"))

    # 2. Package assets directory
    pkg_assets = Path(__file__).resolve().parents[1] / "assets" / "app.ico"
    candidates.append(str(pkg_assets))

    # 3. Development root repository directory
    repo_root = Path(__file__).resolve().parents[2] / "app.ico"
    candidates.append(str(repo_root))

    # 4. Current working directory
    candidates.append(os.path.join(os.getcwd(), "app.ico"))

    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def get_app_icon_image(size: int = 64) -> Optional["Image.Image"]:
    """
    Returns a PIL Image of the Vector Rift Herald at the requested pixel size.
    Checks package asset files first, falling back to embedded vector data.
    """
    if not HAVE_PIL:
        return None

    # Check for pre-rendered PNG at requested size or master
    candidates = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "riftscout", "assets", f"app_icon_{size}.png"))
        candidates.append(os.path.join(sys._MEIPASS, "riftscout", "assets", "app_icon.png"))

    pkg_dir = Path(__file__).resolve().parents[1] / "assets"
    candidates.append(str(pkg_dir / f"app_icon_{size}.png"))
    candidates.append(str(pkg_dir / "app_icon.png"))

    for path in candidates:
        if os.path.exists(path):
            try:
                img = Image.open(path).convert("RGBA")
                if img.size != (size, size):
                    img = img.resize((size, size), Image.Resampling.LANCZOS)
                return img
            except Exception as e:
                log.debug("Failed loading icon from %s: %s", path, e)

    # Fallback to embedded base64 icon data
    try:
        raw = base64.b64decode(VECTOR_HERALD_B64_64)
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
        if img.size != (size, size):
            img = img.resize((size, size), Image.Resampling.LANCZOS)
        return img
    except Exception as e:
        log.error("Failed decoding embedded Vector Herald icon: %s", e)
        return None


def get_tray_icon_image(size: int = 64) -> "Image.Image":
    """Returns the icon image specifically formatted for the system notification tray."""
    img = get_app_icon_image(size)
    if img:
        return img
    # Ultimate safe fallback: solid 64x64 if PIL fails
    if HAVE_PIL:
        return Image.new("RGBA", (size, size), (200, 170, 110, 255))
    return None


def set_window_icon(root) -> None:
    """
    Configures both the native Win32 window icon and Tkinter iconphoto
    with the Vector Rift Herald branding.
    """
    # 1. Native Windows Win32 titlebar / taskbar icon via iconbitmap
    ico = get_app_icon_ico_path()
    if ico and os.path.exists(ico):
        try:
            root.iconbitmap(ico)
        except Exception as e:
            log.debug("iconbitmap failed: %s", e)

    # 2. Cross-platform / multi-resolution PhotoImages via iconphoto
    if not HAVE_PIL:
        return

    try:
        img64 = get_app_icon_image(64)
        img32 = get_app_icon_image(32)
        img16 = get_app_icon_image(16)
        if img64:
            p64 = ImageTk.PhotoImage(img64, master=root)
            p32 = ImageTk.PhotoImage(img32, master=root) if img32 else p64
            p16 = ImageTk.PhotoImage(img16, master=root) if img16 else p64
            # Keep references on root to avoid garbage collection
            root._riftwatch_icons = (p64, p32, p16)
            root.iconphoto(True, p64, p32, p16)
    except Exception as e:
        log.debug("iconphoto failed: %s", e)
