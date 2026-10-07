"""
Shared Tk widgets and helpers for the Hextech theme.
"""

import sys
import tkinter as tk
from typing import Callable, Optional

from .. import config as C

_SCALE = 1.0


def enable_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def apply_dark_titlebar(window: tk.Misc) -> None:
    """Enable Windows 10/11 Immersive Dark Mode for the native window frame."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetAncestor(window.winfo_id(), 2)
        if not hwnd:
            hwnd = window.winfo_id()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        value = ctypes.c_int(2)
        hr = set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
        if hr != 0:
            DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
            set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1, ctypes.byref(value), ctypes.sizeof(value))
    except Exception:
        pass


def init_scale(root: tk.Misc) -> None:
    global _SCALE
    try:
        _SCALE = max(1.0, root.winfo_fpixels("1i") / 96.0)
    except Exception:
        _SCALE = 1.0


def px(n: float) -> int:
    """Scale a 96-DPI pixel value for the current display."""
    return int(round(n * _SCALE))


def font(size: int = 10, bold: bool = False, family: str = C.FONT_FAMILY):
    return (family, size, "bold") if bold else (family, size)


def clear(frame: tk.Misc) -> None:
    for w in frame.winfo_children():
        w.destroy()


def label(parent, text="", size=10, bold=False, fg=C.COLOR_TEXT_PRIMARY, bg=None, **kw) -> tk.Label:
    return tk.Label(parent, text=text, font=font(size, bold), fg=fg,
                    bg=bg if bg is not None else parent.cget("bg"), **kw)


def button(parent, text: str, command: Callable, *, bg=C.COLOR_SURFACE_HOVER, fg=C.COLOR_TEXT_PRIMARY,
           hover_bg=None, size=9, bold=True, padx=10, pady=4, tooltip: Optional[str] = None) -> tk.Label:
    """Flat label-based button (tk.Button ignores colors on some Windows themes)."""
    hover_bg = hover_bg or C.COLOR_BORDER
    b = tk.Label(parent, text=text, font=font(size, bold), fg=fg, bg=bg, cursor="hand2",
                 padx=px(padx), pady=px(pady))
    b._base_bg = bg  # type: ignore[attr-defined]
    b._hover_bg = hover_bg  # type: ignore[attr-defined]
    b.bind("<Enter>", lambda e: b.configure(bg=getattr(b, "_hover_bg", hover_bg)))
    b.bind("<Leave>", lambda e: b.configure(bg=getattr(b, "_base_bg", bg)))  # type: ignore[attr-defined]
    b.bind("<Button-1>", lambda e: command())
    if tooltip:
        Tooltip(b, tooltip)
    return b


def set_button_colors(b: tk.Label, bg: str, fg: str, hover_bg: Optional[str] = None) -> None:
    b._base_bg = bg  # type: ignore[attr-defined]
    if hover_bg is not None:
        b._hover_bg = hover_bg  # type: ignore[attr-defined]
    b.configure(bg=bg, fg=fg)


def pill(parent, text: str, bg: str, fg: str = C.COLOR_BG, size: int = 8, bold: bool = True) -> tk.Label:
    return tk.Label(parent, text=text, font=font(size, bold), bg=bg, fg=fg, padx=px(6), pady=px(1))


def card(parent, border: str = C.COLOR_BORDER, bg: str = C.COLOR_SURFACE) -> tk.Frame:
    outer = tk.Frame(parent, bg=border)
    inner = tk.Frame(outer, bg=bg)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    outer.inner = inner  # type: ignore[attr-defined]
    return outer


class Tooltip:
    def __init__(self, widget: tk.Widget, text: str):
        self.widget, self.text, self.tip = widget, text, None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _show(self, _e=None):
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + px(8)
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + px(4)
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, font=font(9), bg=C.COLOR_BG_DARK, fg=C.COLOR_TEXT_PRIMARY,
                 padx=px(8), pady=px(4), relief="solid", bd=1).pack()

    def _hide(self, _e=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class ScrollFrame(tk.Frame):
    """Vertically scrolling container. `body` is where content goes.
    Mouse wheel works anywhere over the frame, including over child widgets."""

    _active: Optional["ScrollFrame"] = None
    _bound_root = None

    def __init__(self, parent, bg=C.COLOR_BG, **kw):
        super().__init__(parent, bg=bg, **kw)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.vbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview, width=px(10),
                                 bg=C.COLOR_SURFACE, activebackground=C.COLOR_GOLD, troughcolor=C.COLOR_BG_DARK,
                                 bd=0, highlightthickness=0, relief="flat")
        self.body = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.vbar.pack(side="right", fill="y")
        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        self.bind("<Enter>", lambda e: self._set_active(True))
        self.bind("<Leave>", lambda e: self._set_active(False))
        root = self.winfo_toplevel()
        if ScrollFrame._bound_root is not root:
            root.bind_all("<MouseWheel>", ScrollFrame._on_wheel, add="+")
            ScrollFrame._bound_root = root

    def _set_active(self, on: bool):
        if on:
            ScrollFrame._active = self
        elif ScrollFrame._active is self:
            ScrollFrame._active = None

    @staticmethod
    def _on_wheel(event):
        sf = ScrollFrame._active
        if sf is None or not sf.winfo_exists():
            return
        if sf.body.winfo_height() <= sf.canvas.winfo_height():
            return
        sf.canvas.yview_scroll(int(-event.delta / 120) * 3, "units")

    @staticmethod
    def _safe_destroy(widget: tk.Widget) -> None:
        try:
            if widget.winfo_exists():
                widget.destroy()
        except Exception:
            pass

    def keep_scroll(self, rebuild: Callable[[], None]) -> None:
        """Rebuild contents smoothly using double-buffered frame swapping to prevent white flashes."""
        try:
            pos = self.canvas.yview()[0]
        except Exception:
            pos = 0.0
        bg = self.cget("bg") or C.COLOR_BG
        old_body = self.body
        new_body = tk.Frame(self.canvas, bg=bg)
        self.body = new_body
        try:
            rebuild()
        except Exception:
            self.body = old_body
            new_body.destroy()
            raise
        self.canvas.itemconfigure(self._win, window=new_body)
        new_body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        w = self.canvas.winfo_width()
        if w > 1:
            self.canvas.itemconfigure(self._win, width=w)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(pos)
        self.after_idle(self._safe_destroy, old_body)

    def to_top(self) -> None:
        self.canvas.yview_moveto(0)
