"""
The five main tabs. Each view declares which state keys it depends on; the app
only re-renders a view when one of those changes (or once a minute for views
that show relative times), and only while it is visible.
"""

import datetime
import os
import tkinter as tk
from typing import Any, Dict, List, Optional

from .. import __version__
from .. import config as C
from ..catalog import role_label
from ..data import (format_local_day, format_local_match_time, format_relative_time,
                    parse_iso_datetime, utcnow)
from ..stream import event_subtitle, event_title, next_banger, now_airing, upcoming
from . import cards
from .widgets import ScrollFrame, button, clear, font, label, pill, px, Tooltip


class View(tk.Frame):
    deps: tuple = ()
    minute_refresh = False

    def __init__(self, parent, app):
        super().__init__(parent, bg=C.COLOR_BG)
        self.app = app
        self.scroll = ScrollFrame(self)
        self.scroll.pack(fill="both", expand=True)
        self.body = self.scroll.body

    def signature(self) -> tuple:
        sig = tuple(self.app.versions.get(d, 0) for d in self.deps)
        sig += (self.app.versions.get("prefs", 0),)
        if self.minute_refresh:
            sig += (int(utcnow().timestamp() // 60),)
        return sig

    def render(self) -> None:
        self.scroll.keep_scroll(self._build)

    def _build(self) -> None:  # pragma: no cover - overridden
        raise NotImplementedError

    # helpers
    def section(self, text: str, sub: str = "") -> None:
        row = tk.Frame(self.body, bg=C.COLOR_BG)
        row.pack(fill="x", padx=px(18), pady=(px(16), px(6)))
        label(row, text.upper(), 10, True, fg=C.COLOR_GOLD).pack(side="left")
        if sub:
            label(row, sub, 9, fg=C.COLOR_TEXT_MUTED).pack(side="left", padx=px(10))

    def empty(self, title: str, detail: str = "") -> None:
        box = tk.Frame(self.body, bg=C.COLOR_BG)
        box.pack(fill="x", pady=px(40))
        label(box, title, 13, True, fg=C.COLOR_TEXT_MUTED).pack()
        if detail:
            label(box, detail, 9, fg=C.COLOR_TEXT_DIM, wraplength=px(560), justify="center").pack(pady=px(6))


# =============================================================================
# LIVE
# =============================================================================
class LiveView(View):
    deps = ("live", "livestats", "schedule", "catalog")
    minute_refresh = True

    def _build(self) -> None:
        clear(self.body)
        a = self.app
        live = list(a.state["live"])
        stats = a.state["livestats"]
        live.sort(key=lambda m: (not a.watchlist.is_strong(m, stats.get(m["match_id"])),
                                 not a.watchlist.is_followed(m, stats.get(m["match_id"])),
                                 m.get("start_time_utc", "")))
        if live:
            self.section("Live now", f"{len(live)} match{'es' if len(live) != 1 else ''} in progress")
            for m in live:
                self._live_card(m, stats.get(m["match_id"]))
        else:
            self._idle()

    # ---- idle state
    def _idle(self) -> None:
        a = self.app
        sched = [m for m in a.state["schedule"] if m.get("state") == "unstarted"]
        self.empty("No pro matches are live right now")
        nxt = next((m for m in sched if a.watchlist.is_strong(m)), None)
        tag = "Next match you follow"
        if nxt is None:
            nxt = next((m for m in sched if a.watchlist.is_followed(m)), None)
            tag = "Next match in your leagues"
        if nxt is None and sched:
            nxt, tag = sched[0], "Next pro match"
        if nxt:
            self.section(tag)
            c = tk.Frame(self.body, bg=C.COLOR_BG)
            c.pack(fill="x", padx=px(18))
            big = tk.Frame(c, bg=C.COLOR_SURFACE, highlightbackground=C.COLOR_GOLD, highlightthickness=1)
            big.pack(fill="x")
            label(big, f"{nxt['team1_name']}  vs  {nxt['team2_name']}", 16, True).pack(pady=(px(14), px(2)))
            label(big, f"{nxt['league_name']}" + (f" · {nxt['block_name']}" if nxt.get('block_name') else "")
                  + f" · Bo{nxt.get('best_of', 1)}", 9, fg=C.COLOR_TEXT_MUTED).pack()
            label(big, format_relative_time(nxt["start_time_utc"]).replace("in ", "Starts in "), 20, True,
                  fg=C.COLOR_CYAN).pack(pady=(px(8), 0))
            label(big, format_local_match_time(nxt["start_time_utc"]), 9, fg=C.COLOR_TEXT_MUTED).pack(
                pady=(0, px(14)))
        later = [m for m in sched if m is not nxt and a.watchlist.is_followed(m)][:4]
        if later:
            self.section("Coming up")
            for m in later:
                cards.match_row(self.body, a, m).pack(fill="x", padx=px(18), pady=px(4))
        row = tk.Frame(self.body, bg=C.COLOR_BG)
        row.pack(pady=px(18))
        button(row, "Full schedule  →", lambda: a.show_tab("schedule"), bg=C.COLOR_GOLD, fg=C.COLOR_BG,
               hover_bg=C.COLOR_GOLD_HOVER).pack()

    # ---- live card
    def _live_card(self, m: Dict[str, Any], st: Optional[Dict[str, Any]]) -> None:
        a = self.app
        reasons = a.watchlist.reasons(m, st)
        strong = any(r.strong for r in reasons)
        outer = tk.Frame(self.body, bg=C.COLOR_GOLD if strong else C.COLOR_BORDER)
        outer.pack(fill="x", padx=px(18), pady=px(6))
        c = tk.Frame(outer, bg=C.COLOR_SURFACE)
        c.pack(fill="both", expand=True, padx=1, pady=1)

        top = tk.Frame(c, bg=C.COLOR_SURFACE)
        top.pack(fill="x", padx=px(14), pady=(px(10), 0))
        pill(top, "● LIVE", C.COLOR_LIVE, fg="white").pack(side="left")
        label(top, f"  {m['league_name']}" + (f" · {m['block_name']}" if m.get("block_name") else ""), 9, True,
              fg=C.COLOR_TEXT_MUTED).pack(side="left")
        hidden = cards.scores_hidden(a, m)
        g = next((x for x in m.get("games", []) if x.get("state") == "inProgress"), None)
        if g and not hidden:
            label(top, f"Game {g.get('number')} · Best of {m.get('best_of', 1)}", 9, True,
                  fg=C.COLOR_CYAN).pack(side="right")
        else:  # the game number would reveal the series score (Game 5 of a Bo5 means 2-2)
            label(top, f"Best of {m.get('best_of', 1)}", 9, True, fg=C.COLOR_CYAN).pack(side="right")
        mid = tk.Frame(c, bg=C.COLOR_SURFACE)
        mid.pack(fill="x", padx=px(14), pady=px(8))
        mid.grid_columnconfigure(0, weight=1, uniform="s")
        mid.grid_columnconfigure(2, weight=1, uniform="s")
        for col, i in ((0, 1), (2, 2)):
            side = tk.Frame(mid, bg=C.COLOR_SURFACE)
            side.grid(row=0, column=col)
            code, name = m[f"team{i}_code"], m[f"team{i}_name"]
            cards.logo(side, a, m.get(f"team{i}_image", ""), 56, code).pack()
            nm = tk.Frame(side, bg=C.COLOR_SURFACE)
            nm.pack()
            label(nm, name, 12, True).pack(side="left")
            cards.team_star(nm, a, code, name).pack(side="left", padx=px(4))
        s1, s2 = cards.score_text(a, m)
        center = tk.Frame(mid, bg=C.COLOR_SURFACE)
        center.grid(row=0, column=1, padx=px(10))
        label(center, f"{s1}  :  {s2}", 26, True, fg=C.COLOR_TEXT_DIM if hidden else C.COLOR_TEXT_PRIMARY).pack()
        label(center, "series", 8, fg=C.COLOR_TEXT_DIM).pack()

        if st:
            self._stats_panel(c, m, st, hidden)
        else:
            label(c, "In-game stats are not available for this broadcast yet.", 8,
                  fg=C.COLOR_TEXT_DIM).pack(pady=(0, px(4)))

        bottom = tk.Frame(c, bg=C.COLOR_SURFACE)
        bottom.pack(fill="x", padx=px(14), pady=(px(4), px(12)))
        cards.reason_chips(bottom, reasons).pack(side="left")
        button(bottom, "▶ Watch live", lambda: a.watch(m), bg=C.COLOR_LIVE, fg="white",
               hover_bg="#ff5b70").pack(side="right")
        if hidden:
            button(bottom, "Reveal scores", lambda: a.reveal(m["match_id"]), size=8, bold=False,
                   fg=C.COLOR_TEXT_MUTED).pack(side="right", padx=px(8))

    def _stats_panel(self, parent, m, st, hidden: bool) -> None:
        a = self.app
        # Work out which listed team is on blue side this game.
        blue_is_team1 = st.get("blue", {}).get("team_id") == m.get("team1_id") or \
            st.get("blue_team_id") == m.get("team1_id")
        sides = [("blue", 1 if blue_is_team1 else 2), ("red", 2 if blue_is_team1 else 1)]
        box = tk.Frame(parent, bg=C.COLOR_BG_DARK)
        box.pack(fill="x", padx=px(14), pady=(0, px(6)))

        if hidden:
            label(box, "In-game stats hidden (spoiler mode)", 9, fg=C.COLOR_TEXT_DIM).pack(pady=px(10))
        else:
            grid = tk.Frame(box, bg=C.COLOR_BG_DARK)
            grid.pack(fill="x", padx=px(10), pady=px(8))
            heads = ["", "Kills", "Gold", "Towers", "Dragons", "Barons", "Inhibs"]
            for col, h in enumerate(heads):
                grid.grid_columnconfigure(col, weight=1 if col else 2)
                label(grid, h, 8, True, fg=C.COLOR_TEXT_DIM, bg=C.COLOR_BG_DARK).grid(row=0, column=col)
            for row, (side, ti) in enumerate(sides, start=1):
                d = st.get(side) or {}
                color = C.COLOR_BLUE_SIDE if side == "blue" else C.COLOR_RED_SIDE
                label(grid, f"■ {m[f'team{ti}_code']}", 10, True, fg=color, bg=C.COLOR_BG_DARK).grid(
                    row=row, column=0, sticky="w")
                vals = [d.get("kills", 0), f"{d.get('gold', 0) / 1000:.1f}k", d.get("towers", 0),
                        len(d.get("dragons", [])), d.get("barons", 0), d.get("inhibitors", 0)]
                for col, v in enumerate(vals, start=1):
                    label(grid, str(v), 11, True, bg=C.COLOR_BG_DARK).grid(row=row, column=col)
            bg_gold = (st.get("blue") or {}).get("gold", 0)
            rg_gold = (st.get("red") or {}).get("gold", 0)
            diff = bg_gold - rg_gold
            if bg_gold or rg_gold:
                lead_code = m[f"team{sides[0][1]}_code"] if diff > 0 else m[f"team{sides[1][1]}_code"]
                txt = "Gold even" if abs(diff) < 500 else f"{lead_code} +{abs(diff) / 1000:.1f}k gold"
                label(box, txt, 9, True, fg=C.COLOR_GOLD, bg=C.COLOR_BG_DARK).pack(pady=(0, px(6)))

        lineups = tk.Frame(box, bg=C.COLOR_BG_DARK)
        lineups.pack(fill="x", padx=px(10), pady=(0, px(8)))
        followed = {p.lower() for p in a.settings.get("followed_players", [])}
        for col, (side, ti) in enumerate(sides):
            lineups.grid_columnconfigure(col, weight=1, uniform="l")
            colf = tk.Frame(lineups, bg=C.COLOR_BG_DARK)
            colf.grid(row=0, column=col, sticky="nwe", padx=px(6))
            col_head = tk.Frame(colf, bg=C.COLOR_BG_DARK)
            col_head.pack(anchor="w", pady=(0, px(2)))
            cards.logo(col_head, a, m.get(f"team{ti}_image", ""), 16, m[f"team{ti}_code"]).pack(side="left", padx=(0, px(4)))
            label(col_head, f"{m[f'team{ti}_code']} ({side} side)", 8, True,
                  fg=C.COLOR_BLUE_SIDE if side == "blue" else C.COLOR_RED_SIDE, bg=C.COLOR_BG_DARK).pack(side="left")
            for p in (st.get(side) or {}).get("players", []):
                is_f = p.get("name", "").lower() in followed
                row = tk.Frame(colf, bg=C.COLOR_BG_DARK)
                row.pack(fill="x")
                label(row, f"{role_label(p.get('role')):<8}", 8, fg=C.COLOR_TEXT_DIM, bg=C.COLOR_BG_DARK,
                      width=8, anchor="w").pack(side="left")
                label(row, ("★ " if is_f else "") + p.get("name", ""), 9, is_f,
                      fg=C.COLOR_GOLD if is_f else C.COLOR_TEXT_PRIMARY, bg=C.COLOR_BG_DARK).pack(side="left")
                label(row, p.get("champion", ""), 8, fg=C.COLOR_TEXT_MUTED, bg=C.COLOR_BG_DARK).pack(side="right")


# =============================================================================
# SCHEDULE
# =============================================================================
RANGES = (("upcoming", "Upcoming"), ("today", "Today"), ("results", "Results"))


class ScheduleView(View):
    deps = ("schedule", "live", "catalog")
    minute_refresh = True

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.scroll.pack_forget()
        self.filters = tk.Frame(self, bg=C.COLOR_BG)
        self.filters.pack(fill="x", padx=px(18), pady=(px(12), px(4)))
        self.scroll.pack(fill="both", expand=True)

    def _filters(self) -> None:
        clear(self.filters)
        s = self.app.settings
        cur = s.get("schedule_filter_range", "upcoming")
        for key, text in RANGES:
            on = key == cur
            button(self.filters, text, lambda k=key: self._set("schedule_filter_range", k), size=9,
                   bg=C.COLOR_GOLD if on else C.COLOR_SURFACE, fg=C.COLOR_BG if on else C.COLOR_TEXT_PRIMARY,
                   hover_bg=C.COLOR_GOLD_HOVER if on else C.COLOR_BORDER).pack(side="left", padx=(0, px(4)))
        fo = s.get("schedule_filter_followed", False)
        button(self.filters, ("★ " if fo else "☆ ") + "Followed only",
               lambda: self._set("schedule_filter_followed", not fo), size=9,
               bg=C.COLOR_CYAN_DIM if fo else C.COLOR_SURFACE,
               fg=C.COLOR_TEXT_PRIMARY).pack(side="left", padx=(px(12), px(4)))

        leagues = sorted({(m["league_slug"], m["league_name"]) for m in self.app.state["schedule"]},
                         key=lambda x: x[1].lower())
        sel = s.get("schedule_filter_league", "")
        names = dict(leagues)
        mb = tk.Menubutton(self.filters, text=f"League: {names.get(sel, 'All')}  ▾", font=font(9, True),
                           bg=C.COLOR_SURFACE, fg=C.COLOR_TEXT_PRIMARY, activebackground=C.COLOR_BORDER,
                           activeforeground=C.COLOR_TEXT_PRIMARY, relief="flat", padx=px(10), pady=px(4),
                           cursor="hand2")
        menu = tk.Menu(mb, tearoff=0, bg=C.COLOR_SURFACE, fg=C.COLOR_TEXT_PRIMARY,
                       activebackground=C.COLOR_GOLD, activeforeground=C.COLOR_BG, font=font(9))
        menu.add_command(label="All leagues", command=lambda: self._set("schedule_filter_league", ""))
        for slug, name in leagues:
            menu.add_command(label=name, command=lambda sl=slug: self._set("schedule_filter_league", sl))
        mb.configure(menu=menu)
        mb.pack(side="left", padx=px(4))
        label(self.filters, "Times in your local time zone", 8, fg=C.COLOR_TEXT_DIM).pack(side="right")

    def _set(self, key: str, value) -> None:
        self.app.settings.set(key, value)
        self.app.bump("prefs")

    def filtered(self) -> List[Dict[str, Any]]:
        a, s = self.app, self.app.settings
        rng = s.get("schedule_filter_range", "upcoming")
        league = s.get("schedule_filter_league", "")
        followed_only = s.get("schedule_filter_followed", False)
        live_ids = {m["match_id"]: m for m in a.state["live"]}
        now = utcnow()
        today = datetime.datetime.now().astimezone().date()
        out = []
        for m in a.state["schedule"]:
            m = live_ids.get(m["match_id"], m)  # live data is fresher
            dt = parse_iso_datetime(m.get("start_time_utc", ""))
            if not dt:
                continue
            if league and m["league_slug"] != league:
                continue
            if followed_only and not a.watchlist.is_followed(m):
                continue
            if rng == "upcoming" and m["state"] == "completed":
                continue
            if rng == "today" and dt.astimezone().date() != today:
                continue
            if rng == "results" and (m["state"] != "completed" or now - dt > datetime.timedelta(days=7)):
                continue
            out.append(m)
        out.sort(key=lambda m: m["start_time_utc"], reverse=(rng == "results"))
        return out[:80]

    def _build(self) -> None:
        self._filters()
        clear(self.body)
        matches = self.filtered()
        if not self.app.state["schedule"]:
            self.empty("Loading schedule…", "Fetching matches from the LoL Esports API.")
            return
        if not matches:
            hint = "Try turning off 'Followed only' or picking another league."
            self.empty("No matches for these filters", hint)
            return
        day = None
        for m in matches:
            d = format_local_day(m["start_time_utc"])
            if d != day:
                day = d
                self.section(d)
            cards.match_row(self.body, self.app, m).pack(fill="x", padx=px(18), pady=px(4))
        tk.Frame(self.body, bg=C.COLOR_BG, height=px(16)).pack()


# =============================================================================
# 24/7 STREAM
# =============================================================================
class StreamView(View):
    deps = ("stream", "catalog")
    minute_refresh = True

    def _build(self) -> None:
        clear(self.body)
        a = self.app
        events = a.state["stream"]
        if not events:
            self.empty("Loading the 24/7 broadcast schedule…", f"Source: {C.STREAM_SITE_URL}")
            return
        now = utcnow()
        cur = now_airing(events, now)
        self.section("Now on Twitch", f"twitch.tv/{C.TWITCH_CHANNEL}")
        hero = tk.Frame(self.body, bg=C.COLOR_SURFACE, highlightbackground=C.COLOR_LIVE if cur else C.COLOR_BORDER,
                        highlightthickness=1)
        hero.pack(fill="x", padx=px(18))
        if cur:
            top = tk.Frame(hero, bg=C.COLOR_SURFACE)
            top.pack(fill="x", padx=px(14), pady=(px(12), 0))
            pill(top, "● ON AIR", C.COLOR_LIVE, fg="white").pack(side="left")
            if cur.get("is_banger"):
                pill(top, "S-TIER BANGER", C.COLOR_BANGER, fg="white").pack(side="left", padx=px(6))
            started = parse_iso_datetime(cur["start_utc"])
            mins = int((now - started).total_seconds() // 60) if started else 0
            label(top, f"started {mins // 60}h {mins % 60}m ago" if mins >= 60 else f"started {mins}m ago",
                  9, fg=C.COLOR_TEXT_MUTED).pack(side="right")
            label(hero, event_title(cur), 20, True).pack(anchor="w", padx=px(14), pady=(px(6), 0))
            label(hero, event_subtitle(cur), 10, fg=C.COLOR_TEXT_MUTED).pack(anchor="w", padx=px(14))
            nxt = upcoming(events, now, limit=1)
            if nxt:
                label(hero, f"Up next: {event_title(nxt[0])}  ·  {format_relative_time(nxt[0]['start_utc'], now)}",
                      9, fg=C.COLOR_CYAN).pack(anchor="w", padx=px(14), pady=(px(6), 0))
        else:
            label(hero, "Off air or between tournaments", 14, True, fg=C.COLOR_TEXT_MUTED).pack(
                anchor="w", padx=px(14), pady=(px(12), 0))
            nxt = upcoming(events, now, limit=1)
            if nxt:
                label(hero, f"Next: {event_title(nxt[0])} · {format_relative_time(nxt[0]['start_utc'], now)}",
                      10, fg=C.COLOR_CYAN).pack(anchor="w", padx=px(14))
        btns = tk.Frame(hero, bg=C.COLOR_SURFACE)
        btns.pack(fill="x", padx=px(14), pady=px(12))
        button(btns, "▶ Watch on Twitch", lambda: a.open_url(C.TWITCH_CHANNEL_URL), bg="#9146ff", fg="white",
               hover_bg="#a970ff").pack(side="left")
        button(btns, "Full schedule on lolworlds.com ↗", lambda: a.open_url(C.STREAM_SITE_URL), size=9,
               bold=False).pack(side="left", padx=px(8))

        banger = next_banger(events, now)
        if banger:
            b = tk.Frame(self.body, bg=C.COLOR_SURFACE, highlightbackground=C.COLOR_BANGER, highlightthickness=1)
            b.pack(fill="x", padx=px(18), pady=(px(10), 0))
            label(b, "NEXT S-TIER BANGER", 8, True, fg=C.COLOR_BANGER).pack(anchor="w", padx=px(14), pady=(px(8), 0))
            label(b, f"{event_title(banger)}   ·   {event_subtitle(banger)}", 12, True).pack(anchor="w", padx=px(14))
            label(b, f"{format_local_match_time(banger['start_utc'])}  ({format_relative_time(banger['start_utc'], now)})",
                  9, fg=C.COLOR_TEXT_MUTED).pack(anchor="w", padx=px(14), pady=(0, px(8)))

        ups = upcoming(events, now, limit=40)
        day = None
        for e in ups:
            d = format_local_day(e["start_utc"])
            if d != day:
                day = d
                self.section(d)
            self._row(e, now)
        if not ups:
            self.empty("No upcoming rebroadcasts are scheduled yet.")
        tk.Frame(self.body, bg=C.COLOR_BG, height=px(16)).pack()

    def _row(self, e: Dict[str, Any], now) -> None:
        reasons = self.app.watchlist.stream_reasons(e)
        row = tk.Frame(self.body, bg=C.COLOR_SURFACE,
                       highlightbackground=C.COLOR_GOLD if reasons else C.COLOR_BORDER, highlightthickness=1)
        row.pack(fill="x", padx=px(18), pady=px(3))
        label(row, format_local_match_time(e["start_utc"]).split(", ")[-1], 10, True, fg=C.COLOR_CYAN,
              width=9, anchor="w").pack(side="left", padx=(px(12), px(6)), pady=px(8))
        mid = tk.Frame(row, bg=C.COLOR_SURFACE)
        mid.pack(side="left", fill="x", expand=True)
        title_box = tk.Frame(mid, bg=C.COLOR_SURFACE)
        title_box.pack(anchor="w")
        if e.get("kind") == "match" and (e.get("team1") or e.get("team2")):
            t1, t2 = e.get("team1", ""), e.get("team2", "")
            cat = self.app.state.get("catalog")
            img1 = cat.team_image(t1) if cat else ""
            img2 = cat.team_image(t2) if cat else ""
            if img1 or t1:
                cards.logo(title_box, self.app, img1, 16, t1[:3]).pack(side="left", padx=(0, px(4)))
                label(title_box, t1, 11, True).pack(side="left")
            label(title_box, " vs ", 9, fg=C.COLOR_TEXT_DIM).pack(side="left", padx=px(2))
            if img2 or t2:
                cards.logo(title_box, self.app, img2, 16, t2[:3]).pack(side="left", padx=(0, px(4)))
                label(title_box, t2, 11, True).pack(side="left")
        else:
            label(title_box, event_title(e), 11, True).pack(side="left")
        label(mid, event_subtitle(e), 8, fg=C.COLOR_TEXT_MUTED).pack(anchor="w")
        right = tk.Frame(row, bg=C.COLOR_SURFACE)
        right.pack(side="right", padx=px(12))
        if e.get("is_banger"):
            pill(right, "BANGER", C.COLOR_BANGER, fg="white").pack(side="right", padx=px(3))
        for r in reasons:
            pill(right, f"★ {r.label}", C.COLOR_GOLD).pack(side="right", padx=px(3))
        label(right, format_relative_time(e["start_utc"], now), 8, fg=C.COLOR_TEXT_DIM).pack(side="right", padx=px(6))


# =============================================================================
# WATCHLIST
# =============================================================================
TOP_LEAGUES = ("LCK", "LPL", "LEC", "LCS", "LCP", "CBLOL")


class WatchlistView(View):
    deps = ("catalog",)

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.mode = "teams"
        self.query = tk.StringVar()
        self.expanded: Optional[str] = None
        self.scroll.pack_forget()
        bar = tk.Frame(self, bg=C.COLOR_BG)
        bar.pack(fill="x", padx=px(18), pady=(px(12), px(4)))
        self.modebar = tk.Frame(bar, bg=C.COLOR_BG)
        self.modebar.pack(side="left")
        entry_wrap = tk.Frame(bar, bg=C.COLOR_BORDER)
        entry_wrap.pack(side="right")
        self.entry = tk.Entry(entry_wrap, textvariable=self.query, font=font(10), bg=C.COLOR_SURFACE,
                              fg=C.COLOR_TEXT_PRIMARY, insertbackground=C.COLOR_GOLD, relief="flat", width=28)
        self.entry.pack(padx=1, pady=1, ipady=px(4), ipadx=px(6))
        label(bar, "Search", 9, fg=C.COLOR_TEXT_MUTED).pack(side="right", padx=px(6))
        self._after = None
        self.query.trace_add("write", lambda *_: self._debounce())
        self.scroll.pack(fill="both", expand=True)

    def _debounce(self):
        if self._after:
            self.after_cancel(self._after)
        self._after = self.after(250, lambda: (self.scroll.to_top(), self.render()))

    def signature(self) -> tuple:
        return super().signature() + (self.mode, self.query.get().strip().lower(), self.expanded)

    def _modebar(self):
        clear(self.modebar)
        for key, text in (("teams", "Teams"), ("players", "Players"), ("regions", "Regions"), ("leagues", "Leagues")):
            on = key == self.mode
            button(self.modebar, text, lambda k=key: self._set_mode(k),
                   bg=C.COLOR_GOLD if on else C.COLOR_SURFACE, fg=C.COLOR_BG if on else C.COLOR_TEXT_PRIMARY,
                   hover_bg=C.COLOR_GOLD_HOVER if on else C.COLOR_BORDER).pack(side="left", padx=(0, px(4)))

    def _set_mode(self, mode):
        self.mode, self.expanded = mode, None
        self.scroll.to_top()
        self.app.request_render(self)

    def _build(self) -> None:
        self._modebar()
        clear(self.body)
        self._following()
        cat = self.app.state["catalog"]
        if cat.empty and self.mode not in ("leagues", "regions"):
            self.empty("Loading the team directory…", "Downloading teams and rosters from Riot (about 1.5 MB, "
                       "refreshed once a day).")
            return
        {"teams": self._teams, "players": self._players, "regions": self._regions, "leagues": self._leagues}[self.mode]()
        tk.Frame(self.body, bg=C.COLOR_BG, height=px(16)).pack()

    # ---- following summary
    def _following(self) -> None:
        s = self.app.settings
        teams, players = s.followed_teams(), s.get("followed_players", [])
        regions = s.followed_regions()
        leagues = s.get("followed_leagues", [])
        self.section("Following", f"{len(teams)} teams · {len(players)} players · {len(regions)} regions · {len(leagues)} leagues")
        wrap = tk.Frame(self.body, bg=C.COLOR_BG)
        wrap.pack(fill="x", padx=px(18))
        if not (teams or players or regions or leagues):
            label(wrap, "Star teams, players, and regions below (or on any match card) to follow them.", 9,
                  fg=C.COLOR_TEXT_MUTED).pack(anchor="w")
        chips = [(f"🌐 {r}", lambda r=r: self.app.toggle_region(r), C.COLOR_CYAN_DIM) for r in regions]
        chips += [(f"★ {t.get('name') or t['code']}", lambda t=t: self.app.toggle_team(t["code"], t.get("name", "")),
                  C.COLOR_GOLD) for t in teams]
        chips += [(f"★ {p}", lambda p=p: self.app.toggle_player(p), C.COLOR_CYAN_DIM) for p in players]
        # Wrap by estimated text width (Tk has no flow layout).
        budget, used, row = max(px(500), self.winfo_width() - px(80)), 0, None
        for text, cb, color in chips:
            w = px(len(text) * 8 + 40)
            if row is None or used + w > budget:
                row = tk.Frame(wrap, bg=C.COLOR_BG)
                row.pack(fill="x", anchor="w")
                used = 0
            self._chip(row, text, cb, color=color)
            used += w

    def _chip(self, parent, text, on_remove, color=C.COLOR_GOLD):
        chip = tk.Frame(parent, bg=color)
        chip.pack(side="left", padx=(0, px(4)), pady=px(2))
        fg = C.COLOR_BG if color == C.COLOR_GOLD else C.COLOR_TEXT_PRIMARY
        tk.Label(chip, text=text, font=font(9, True), bg=color, fg=fg, padx=px(6)).pack(side="left")
        x = tk.Label(chip, text="✕", font=font(9, True), bg=color, fg=fg, cursor="hand2", padx=px(4))
        x.pack(side="left")
        x.bind("<Button-1>", lambda e: on_remove())
        Tooltip(x, "Unfollow")

    def _follow_btn(self, parent, on: bool, command) -> tk.Label:
        return button(parent, "★ Following" if on else "☆ Follow", command, size=8,
                      bg=C.COLOR_GOLD if on else C.COLOR_SURFACE_HOVER, fg=C.COLOR_BG if on else C.COLOR_TEXT_PRIMARY,
                      hover_bg=C.COLOR_GOLD_HOVER if on else C.COLOR_BORDER)

    # ---- teams
    def _teams(self) -> None:
        a = self.app
        cat = a.state["catalog"]
        q = self.query.get().strip()
        if q:
            teams = cat.search_teams(q, limit=50)
            self.section("Teams", f"{len(teams)} result(s) for “{q}”")
        else:
            teams = [t for t in cat.teams if t.get("league_name", "").upper() in TOP_LEAGUES]
            teams.sort(key=lambda t: (TOP_LEAGUES.index(t["league_name"].upper()), t["name"].lower()))
            self.section("Major-league teams", "search to find any of the "
                         f"{len(cat.teams)} active teams")
        if not teams:
            self.empty("No teams match that search")
        league = None
        for t in teams:
            if not q and t["league_name"] != league:
                league = t["league_name"]
                label(self.body, league, 9, True, fg=C.COLOR_TEXT_MUTED).pack(anchor="w", padx=px(20),
                                                                           pady=(px(8), px(2)))
            self._team_row(t)

    def _team_row(self, t: Dict[str, Any]) -> None:
        a = self.app
        on = a.settings.is_team_followed(t["code"], t["name"])
        row = tk.Frame(self.body, bg=C.COLOR_SURFACE, highlightthickness=1,
                       highlightbackground=C.COLOR_GOLD if on else C.COLOR_BORDER)
        row.pack(fill="x", padx=px(18), pady=px(2))
        head = tk.Frame(row, bg=C.COLOR_SURFACE)
        head.pack(fill="x")
        cards.logo(head, a, t.get("image", ""), 28, t["code"]).pack(side="left", padx=px(10), pady=px(6))
        label(head, t["name"], 10, True).pack(side="left")
        label(head, f"  {t['code']} · {t.get('league_name', '')}", 9, fg=C.COLOR_TEXT_MUTED).pack(side="left")
        self._follow_btn(head, on, lambda: a.toggle_team(t["code"], t["name"])).pack(side="right", padx=px(10))
        is_open = self.expanded == t["slug"]
        tog = button(head, "▾ Roster" if not is_open else "▴ Roster", lambda: self._expand(t["slug"]), size=8,
                     bold=False, bg=C.COLOR_SURFACE, fg=C.COLOR_TEXT_MUTED)
        tog.pack(side="right")
        if is_open:
            roster = a.state["catalog"].players_by_team.get(t["slug"], [])
            body = tk.Frame(row, bg=C.COLOR_BG_DARK)
            body.pack(fill="x", padx=px(10), pady=(0, px(8)))
            label(body, "Registered roster (includes academy/substitute players)", 8, fg=C.COLOR_TEXT_DIM,
                  bg=C.COLOR_BG_DARK).pack(anchor="w", padx=px(8), pady=(px(4), 0))
            for p in roster:
                self._player_line(body, p, show_team=False)

    def _expand(self, slug):
        self.expanded = None if self.expanded == slug else slug
        self.app.request_render(self)

    # ---- players
    def _players(self) -> None:
        cat = self.app.state["catalog"]
        q = self.query.get().strip()
        if not q:
            followed = self.app.settings.get("followed_players", [])
            self.section("Players", "type a name to search every registered pro player")
            if followed:
                for name in followed:
                    for p in cat.teams_by_player.get(name.lower(), [])[:3] or []:
                        self._player_line(self.body, p, show_team=True)
            return
        hits = cat.search_players(q, limit=60)
        self.section("Players", f"{len(hits)} result(s) for “{q}”")
        if not hits:
            self.empty("No players match that search")
        for p in hits:
            self._player_line(self.body, p, show_team=True)

    def _player_line(self, parent, p, show_team: bool) -> None:
        a = self.app
        on = a.settings.is_player_followed(p.name)
        bg = parent.cget("bg") if parent is not self.body else C.COLOR_SURFACE
        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x", padx=px(18) if parent is self.body else px(8), pady=1)
        label(row, role_label(p.role), 8, fg=C.COLOR_TEXT_DIM, bg=bg, width=8, anchor="w").pack(side="left",
                                                                                              padx=px(8), pady=px(4))
        label(row, p.name, 10, True, fg=C.COLOR_GOLD if on else C.COLOR_TEXT_PRIMARY, bg=bg).pack(side="left")
        if p.real_name:
            label(row, f"  {p.real_name}", 8, fg=C.COLOR_TEXT_DIM, bg=bg).pack(side="left")
        if show_team:
            cat = a.state.get("catalog")
            img = cat.team_image(p.team_code, p.team_name) if cat else ""
            cards.logo(row, a, img, 18, p.team_code).pack(side="left", padx=(px(6), px(2)))
            label(row, f"{p.team_name} ({p.team_code})", 9, fg=C.COLOR_TEXT_MUTED, bg=bg).pack(side="left")
        self._follow_btn(row, on, lambda: a.toggle_player(p.name)).pack(side="right", padx=px(8))

    # ---- regions
    def _regions(self) -> None:
        a = self.app
        q = self.query.get().strip().lower()
        regions = list(C.MAJOR_REGIONS)
        if q:
            regions = [r for r in regions if q in r["name"].lower() or q in r["code"].lower()
                       or any(q in l.lower() for l in r.get("leagues", []))]
        self.section("Regions & Tournaments", "follow competitive ecosystems to track all of their matches")
        row = tk.Frame(self.body, bg=C.COLOR_BG)
        row.pack(fill="x", padx=px(18), pady=(0, px(6)))
        button(row, "★ Follow All Major Regions",
               lambda: a.follow_all_regions(), size=8, bold=False).pack(side="left")
        button(row, "Unfollow All Regions",
               lambda: a.unfollow_all_regions(), size=8, bold=False).pack(side="left", padx=px(6))
        if not regions:
            self.empty("No regions match that search")
            return
        for r in regions:
            on = a.settings.is_region_followed(r["name"]) or a.settings.is_region_followed(r["code"])
            card = tk.Frame(self.body, bg=C.COLOR_SURFACE, highlightthickness=1,
                            highlightbackground=C.COLOR_GOLD if on else C.COLOR_BORDER)
            card.pack(fill="x", padx=px(18), pady=px(2))
            head = tk.Frame(card, bg=C.COLOR_SURFACE)
            head.pack(fill="x", padx=px(12), pady=px(8))
            label(head, r.get("badge", "🌐"), 14).pack(side="left", padx=(0, px(8)))
            label(head, r["name"], 11, True, fg=C.COLOR_GOLD if on else C.COLOR_TEXT_PRIMARY).pack(side="left")
            leagues_str = " · ".join(r.get("leagues", []))
            label(head, f"  ({leagues_str})", 9, fg=C.COLOR_TEXT_MUTED).pack(side="left")
            self._follow_btn(head, on, lambda reg=r["name"]: a.toggle_region(reg)).pack(side="right")

    # ---- leagues
    def _leagues(self) -> None:
        a = self.app
        leagues = a.state["catalog"].leagues
        if not leagues:
            self.empty("Loading leagues…")
            return
        q = self.query.get().strip().lower()
        if q:
            leagues = [l for l in leagues if q in l["name"].lower() or q in (l.get("region") or "").lower()]
        self.section("Leagues", "matches from followed leagues show in 'Followed only' and on the Live tab")
        row = tk.Frame(self.body, bg=C.COLOR_BG)
        row.pack(fill="x", padx=px(18), pady=(0, px(6)))
        button(row, "Follow the international events (Worlds, MSI, First Stand)",
               lambda: a.follow_leagues(["worlds", "msi", "first_stand"]), size=8, bold=False).pack(side="left")
        region = None
        for l in sorted(leagues, key=lambda l: (l.get("region") != "INTERNATIONAL", l.get("region") or "", l["priority"])):
            if l.get("region") != region:
                region = l.get("region")
                label(self.body, (region or "Other").title(), 9, True, fg=C.COLOR_TEXT_MUTED).pack(
                    anchor="w", padx=px(20), pady=(px(8), px(2)))
            on = a.settings.is_league_followed(l["slug"])
            r = tk.Frame(self.body, bg=C.COLOR_SURFACE, highlightthickness=1,
                         highlightbackground=C.COLOR_GOLD if on else C.COLOR_BORDER)
            r.pack(fill="x", padx=px(18), pady=px(2))
            cards.logo(r, a, l.get("image", ""), 24, l["name"][:3]).pack(side="left", padx=px(10), pady=px(5))
            label(r, l["name"], 10, True).pack(side="left")
            self._follow_btn(r, on, lambda s=l["slug"]: a.toggle_league(s)).pack(side="right", padx=px(10))


# =============================================================================
# SETTINGS
# =============================================================================
class SettingsView(View):
    deps = ("update", "status", "update_progress")

    def _build(self) -> None:
        clear(self.body)
        a, s = self.app, self.app.settings

        self.section("Display")
        self._toggle("Spoiler mode", "Hide all scores, results and in-game stats until you reveal a match.",
                     s.get("spoiler_mode", False), a.toggle_spoiler)

        self.section("System Tray")
        self._toggle("Close button minimizes to system tray",
                     "Keep RiftWatch running in the background notification area when the window is closed.",
                     s.get("minimize_to_tray_on_close", True),
                     lambda: (s.set("minimize_to_tray_on_close", not s.get("minimize_to_tray_on_close", True)), a.bump("prefs")))

        self.section("Startup")
        self._toggle("Start RiftWatch with Windows", "Launch automatically when you sign in.",
                     s.get("start_with_windows", False), a.toggle_autostart)

        self.section("Watchlist Setup")
        wbox = tk.Frame(self.body, bg=C.COLOR_SURFACE)
        wbox.pack(fill="x", padx=px(18), pady=px(4))
        wtxt = tk.Frame(wbox, bg=C.COLOR_SURFACE)
        wtxt.pack(side="left", padx=px(12), pady=px(10))
        label(wtxt, "Watchlist Setup Wizard", 10, True).pack(anchor="w")
        label(wtxt, "Quickly select regions, international tournaments, popular teams, and star players.", 8,
              fg=C.COLOR_TEXT_MUTED).pack(anchor="w")
        button(wbox, "Run Setup Wizard", a.open_onboarding_wizard, size=9).pack(side="right", padx=px(10))

        self.section("Support RiftWatch")
        sbox = tk.Frame(self.body, bg=C.COLOR_SURFACE)
        sbox.pack(fill="x", padx=px(18), pady=px(4))
        stxt = tk.Frame(sbox, bg=C.COLOR_SURFACE)
        stxt.pack(side="left", padx=px(12), pady=px(10))
        label(stxt, "Enjoying RiftWatch & the 24/7 Twitch Broadcast?", 10, True, fg=C.COLOR_GOLD).pack(anchor="w")
        label(stxt, "RiftWatch is 100% free and open-source. Support ongoing development and streaming servers on Ko-fi.", 8,
              fg=C.COLOR_TEXT_MUTED).pack(anchor="w")
        button(sbox, "☕ Support on Ko-fi ↗", lambda: a.open_url(C.KOFI_URL), bg="#720e9e", fg="white",
               hover_bg="#8c19bd", size=9).pack(side="right", padx=px(10))

        self.section("Updates", f"you are running v{__version__}")
        self._toggle("Check for updates automatically", "Looks for a new GitHub release every 6 hours.",
                     s.get("auto_update_check", True),
                     lambda: (s.set("auto_update_check", not s.get("auto_update_check", True)), a.bump("prefs")))
        box = tk.Frame(self.body, bg=C.COLOR_SURFACE)
        box.pack(fill="x", padx=px(18), pady=px(4))
        info, prog = a.state["update"], a.state.get("update_progress")
        if prog:
            label(box, prog, 10, True, fg=C.COLOR_CYAN).pack(side="left", padx=px(12), pady=px(10))
        elif info:
            label(box, f"Version {info['tag']} is available.", 10, True, fg=C.COLOR_GOLD).pack(
                side="left", padx=px(12), pady=px(10))
            button(box, "⬆ Update & restart", a.install_update, bg=C.COLOR_GOLD, fg=C.COLOR_BG,
                   hover_bg=C.COLOR_GOLD_HOVER).pack(side="right", padx=px(10))
            button(box, "Release notes ↗", lambda: a.open_url(info["html_url"]), size=8, bold=False).pack(
                side="right")
        else:
            checked = a.state.get("update_checked")
            label(box, "You're up to date." if checked else "Not checked yet this session.", 10,
                  fg=C.COLOR_TEXT_MUTED).pack(side="left", padx=px(12), pady=px(10))
            button(box, "Check now", a.check_updates).pack(side="right", padx=px(10))

        self.section("Data sources")
        names = {"schedule": "Match schedule (LoL Esports API)", "live": "Live matches (LoL Esports API)",
                 "stream": "24/7 stream schedule (lolworlds.com)", "catalog": "Teams & rosters (LoL Esports API)"}
        for key, name in names.items():
            st = a.state["status"].get(key)
            r = tk.Frame(self.body, bg=C.COLOR_SURFACE)
            r.pack(fill="x", padx=px(18), pady=1)
            if st is None:
                dot, col, txt = "○", C.COLOR_TEXT_DIM, "waiting"
            elif st["ok"]:
                dot, col = "●", C.COLOR_CYAN
                txt = ("cached copy is fresh" if st.get("detail") == "cached" else
                       "updated " + datetime.datetime.fromtimestamp(st["at"]).strftime("%I:%M:%S %p").lstrip("0"))
            else:
                dot, col, txt = "●", C.COLOR_LIVE, st.get("detail") or "error"
            label(r, dot, 10, fg=col).pack(side="left", padx=(px(12), px(6)), pady=px(6))
            label(r, name, 9, True).pack(side="left")
            label(r, txt, 9, fg=C.COLOR_TEXT_MUTED).pack(side="right", padx=px(12))
        row = tk.Frame(self.body, bg=C.COLOR_BG)
        row.pack(fill="x", padx=px(18), pady=px(8))
        button(row, "Refresh team directory now", lambda: a.worker_request("catalog"), size=8).pack(side="left")
        button(row, "Open data folder", lambda: os.startfile(str(C.APPDATA_DIR)), size=8, bold=False).pack(
            side="left", padx=px(6))

        self.section("About")
        about = tk.Frame(self.body, bg=C.COLOR_BG)
        about.pack(fill="x", padx=px(18))
        label(about, f"RiftWatch v{__version__} · © 2026 Monocle Productions LLC · MIT License", 9,
              fg=C.COLOR_TEXT_MUTED).pack(anchor="w")
        label(about, "RiftWatch is an unofficial fan project. It is not endorsed by Riot Games and does not "
                     "reflect the views or opinions of Riot Games or anyone officially involved in producing or "
                     "managing League of Legends. League of Legends and Riot Games are trademarks or registered "
                     "trademarks of Riot Games, Inc.", 8, fg=C.COLOR_TEXT_DIM, wraplength=px(640),
              justify="left").pack(anchor="w", pady=px(6))
        button(about, "Project page on GitHub ↗", lambda: a.open_url(C.GITHUB_PROJECT_URL), size=8,
               bold=False).pack(anchor="w", pady=(0, px(16)))

    def _toggle(self, title: str, desc: str, on: bool, command) -> None:
        r = tk.Frame(self.body, bg=C.COLOR_SURFACE)
        r.pack(fill="x", padx=px(18), pady=px(2))
        txt = tk.Frame(r, bg=C.COLOR_SURFACE)
        txt.pack(side="left", padx=px(12), pady=px(8))
        label(txt, title, 10, True).pack(anchor="w")
        label(txt, desc, 8, fg=C.COLOR_TEXT_MUTED).pack(anchor="w")
        b = button(r, "ON" if on else "OFF", command, size=9, padx=14,
                   bg=C.COLOR_CYAN_DIM if on else C.COLOR_BORDER, fg=C.COLOR_TEXT_PRIMARY)
        b.pack(side="right", padx=px(12))
