"""
Match-card building blocks shared by the Live, Schedule and Stream views.
"""

import tkinter as tk
from typing import Any, Dict, List

from .. import config as C
from ..data import format_local_match_time, format_relative_time
from ..watchlist import FollowReason
from .widgets import button, font, label, pill, px, Tooltip

SPOILER_MASK = "–"


def logo(parent, app, url: str, size: int, text: str) -> tk.Label:
    def ready(photo):
        if lbl.winfo_exists():
            lbl.configure(image=photo)
            lbl.image = photo

    photo = app.images.get(url, px(size), on_ready=ready, fallback_text=text)
    lbl = tk.Label(parent, bg=parent.cget("bg"), bd=0, image=photo) if photo is not None else tk.Label(parent, bg=parent.cget("bg"), bd=0)
    if photo is not None:
        lbl.image = photo
    return lbl


def scores_hidden(app, match: Dict[str, Any]) -> bool:
    """Spoiler mode hides every score/result until the user reveals that match."""
    if match.get("state") == "unstarted":
        return False
    return app.spoiler_on() and not app.is_revealed(match.get("match_id", ""))


def score_text(app, match: Dict[str, Any]) -> tuple:
    if match.get("state") == "unstarted":
        return ("", "")
    if scores_hidden(app, match):
        return (SPOILER_MASK, SPOILER_MASK)
    return (str(match.get("team1_score", 0)), str(match.get("team2_score", 0)))


def team_star(parent, app, code: str, name: str) -> tk.Label:
    """Clickable ☆/★ that follows or unfollows a team."""
    on = app.settings.is_team_followed(code, name)
    star = tk.Label(parent, text="★" if on else "☆", font=font(11, True),
                    fg=C.COLOR_GOLD if on else C.COLOR_TEXT_DIM, bg=parent.cget("bg"), cursor="hand2")
    if code and code.upper() != "TBD":
        star.bind("<Button-1>", lambda e: app.toggle_team(code, name))
        Tooltip(star, f"{'Unfollow' if on else 'Follow'} {name or code}")
    return star


def reason_chips(parent, reasons: List[FollowReason]) -> tk.Frame:
    row = tk.Frame(parent, bg=parent.cget("bg"))
    for r in reasons:
        if r.kind == "team":
            p = pill(row, f"★ {r.label}", C.COLOR_GOLD)
        elif r.kind == "player":
            p = pill(row, f"★ {r.label}", C.COLOR_GOLD if r.confirmed else C.COLOR_CYAN_DIM,
                     fg=C.COLOR_BG if r.confirmed else C.COLOR_TEXT_PRIMARY)
            if not r.confirmed:
                Tooltip(p, "On the team's registered roster. Starters are confirmed once the game is live.")
        elif r.kind == "region":
            p = pill(row, f"🌐 {r.label}", C.COLOR_CYAN_DIM, fg=C.COLOR_TEXT_PRIMARY, bold=True)
            Tooltip(p, f"From your followed region: {r.label}")
        else:
            p = pill(row, r.label, C.COLOR_SURFACE_HOVER, fg=C.COLOR_TEXT_MUTED, bold=False)
        p.pack(side="left", padx=(0, px(4)))
    return row


def state_badge(parent, match: Dict[str, Any]) -> tk.Label:
    st = match.get("state")
    if st == "inProgress":
        return pill(parent, "● LIVE", C.COLOR_LIVE, fg="white")
    if st == "completed":
        return pill(parent, "FINAL", C.COLOR_BORDER, fg=C.COLOR_TEXT_MUTED)
    return pill(parent, format_relative_time(match.get("start_time_utc", "")).upper(),
                C.COLOR_SURFACE_HOVER, fg=C.COLOR_CYAN)


def match_row(parent, app, match: Dict[str, Any], livestats=None) -> tk.Frame:
    """Compact schedule card: header line, teams + score, follow reasons."""
    reasons = app.watchlist.reasons(match, livestats)
    strong = any(r.strong for r in reasons)
    border = C.COLOR_BORDER_FOCUS if strong else C.COLOR_BORDER
    c = tk.Frame(parent, bg=C.COLOR_SURFACE, highlightbackground=border, highlightthickness=1)

    top = tk.Frame(c, bg=C.COLOR_SURFACE)
    top.pack(fill="x", padx=px(12), pady=(px(8), 0))
    league = match.get("league_name", "")
    block = match.get("block_name", "")
    label(top, f"{league}" + (f"  ·  {block}" if block else ""), 8, True, fg=C.COLOR_TEXT_MUTED).pack(side="left")
    state_badge(top, match).pack(side="right")
    label(top, format_local_match_time(match.get("start_time_utc", "")), 8, fg=C.COLOR_TEXT_MUTED).pack(
        side="right", padx=px(8))

    mid = tk.Frame(c, bg=C.COLOR_SURFACE)
    mid.pack(fill="x", padx=px(12), pady=px(6))
    mid.grid_columnconfigure(0, weight=1, uniform="t")
    mid.grid_columnconfigure(2, weight=1, uniform="t")
    s1, s2 = score_text(app, match)
    hidden = scores_hidden(app, match)
    winner = "" if hidden else match.get("winner", "")

    for col, i, anchor in ((0, 1, "e"), (2, 2, "w")):
        side = tk.Frame(mid, bg=C.COLOR_SURFACE)
        side.grid(row=0, column=col, sticky=anchor)
        code, name = match.get(f"team{i}_code", "TBD"), match.get(f"team{i}_name", "TBD")
        lost = bool(winner) and winner != code
        name_fg = C.COLOR_TEXT_DIM if lost else (C.COLOR_GOLD if winner == code else C.COLOR_TEXT_PRIMARY)
        parts = [
            logo(side, app, match.get(f"team{i}_image", ""), 30, code),
            label(side, name, 11, True, fg=name_fg),
            team_star(side, app, code, name),
        ]
        if i == 1:
            parts.reverse()  # team 1 reads star, name, logo toward the centre
        for w in parts:
            w.pack(side="left", padx=px(3))

    center = tk.Frame(mid, bg=C.COLOR_SURFACE)
    center.grid(row=0, column=1, padx=px(14))
    if s1 or s2:
        label(center, f"{s1}  :  {s2}", 15, True,
              fg=C.COLOR_TEXT_DIM if hidden else C.COLOR_TEXT_PRIMARY).pack()
    else:
        label(center, "vs", 11, True, fg=C.COLOR_TEXT_DIM).pack()
    label(center, f"Bo{match.get('best_of', 1)}", 8, fg=C.COLOR_TEXT_DIM).pack()

    bottom = tk.Frame(c, bg=C.COLOR_SURFACE)
    bottom.pack(fill="x", padx=px(12), pady=(0, px(8)))
    reason_chips(bottom, reasons).pack(side="left")
    if hidden:
        button(bottom, "Reveal score", lambda m=match: app.reveal(m.get("match_id", "")), size=8,
               bg=C.COLOR_SURFACE_HOVER, fg=C.COLOR_TEXT_MUTED, bold=False, pady=1).pack(side="right")
    if match.get("state") == "inProgress":
        button(bottom, "▶ Watch", lambda m=match: app.watch(m), size=8, bg=C.COLOR_LIVE, fg="white",
               hover_bg="#ff5b70", pady=1).pack(side="right", padx=px(6))
    return c
