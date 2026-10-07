"""
The five main tabs. Each view declares which state keys it depends on; the app
only re-renders a view when one of those changes (or once a minute for views
that show relative times), and only while it is visible.
"""

import datetime
import os
import tkinter as tk
from typing import Any, Callable, Dict, List, Optional, Tuple

from .. import __version__
from .. import config as C
from ..catalog import role_label
from ..data import (format_local_day, format_local_match_time, format_relative_time,
                    parse_iso_datetime, utcnow)
from ..stream import event_subtitle, event_title, next_banger, now_airing, upcoming
from . import cards
from .widgets import ScrollFrame, button, clear, font, label, pill, px, Tooltip, set_button_colors


class View(tk.Frame):
    deps: tuple = ()
    minute_refresh = False

    def __init__(self, parent, app):
        super().__init__(parent, bg=C.COLOR_BG)
        self.app = app
        self.scroll = ScrollFrame(self)
        self.scroll.pack(fill="both", expand=True)

    @property
    def body(self) -> tk.Frame:
        return self.scroll.body

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
class _LiveCardBinding:
    def __init__(self, match_id: str, hidden: bool, has_stats: bool, blue_ti: int, red_ti: int):
        self.match_id = match_id
        self.hidden = hidden
        self.has_stats = has_stats
        self.blue_ti = blue_ti
        self.red_ti = red_ti
        self.lbl_game: Optional[tk.Label] = None
        self.lbl_score: Optional[tk.Label] = None
        self.lbl_diff: Optional[tk.Label] = None
        self.stat_cells: Dict[str, List[tk.Label]] = {"blue": [], "red": []}
        self.player_champs: Dict[str, List[tk.Label]] = {"blue": [], "red": []}


class LiveView(View):
    deps = ("live", "livestats", "schedule", "catalog")
    minute_refresh = True

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._live_bindings: Dict[str, _LiveCardBinding] = {}

    def render(self) -> None:
        if self._try_update_inplace():
            return
        self.scroll.keep_scroll(self._build)

    def _try_update_inplace(self) -> bool:
        a = self.app
        live = list(a.state.get("live", []))
        if not live or not getattr(self, "_live_bindings", None):
            return False
        cur_ids = [m.get("match_id") for m in live if m.get("match_id")]
        if list(self._live_bindings.keys()) != cur_ids:
            return False
        stats = a.state.get("livestats", {})

        for m in live:
            mid = m.get("match_id")
            b = self._live_bindings.get(mid)
            if not b or not b.lbl_score or not b.lbl_score.winfo_exists():
                return False
            hidden = cards.scores_hidden(a, m)
            if hidden != b.hidden:
                return False
            st = stats.get(mid)
            if bool(st) != b.has_stats:
                return False
            if st and not hidden:
                blue_is_team1 = st.get("blue", {}).get("team_id") == m.get("team1_id") or \
                    st.get("blue_team_id") == m.get("team1_id")
                blue_ti = 1 if blue_is_team1 else 2
                red_ti = 2 if blue_is_team1 else 1
                if blue_ti != b.blue_ti or red_ti != b.red_ti:
                    return False
                for side in ("blue", "red"):
                    curr_p = (st.get(side) or {}).get("players", [])
                    if len(curr_p) != len(b.player_champs.get(side, [])):
                        return False

        for m in live:
            mid = m.get("match_id")
            b = self._live_bindings[mid]
            st = stats.get(mid)
            hidden = b.hidden

            g = next((x for x in m.get("games", []) if x.get("state") == "inProgress"), None)
            if b.lbl_game and b.lbl_game.winfo_exists():
                if g and not hidden:
                    b.lbl_game.configure(text=f"Game {g.get('number')} · Best of {m.get('best_of', 1)}")
                else:
                    b.lbl_game.configure(text=f"Best of {m.get('best_of', 1)}")

            s1, s2 = cards.score_text(a, m)
            if b.lbl_score and b.lbl_score.winfo_exists():
                b.lbl_score.configure(text=f"{s1}  :  {s2}",
                                      fg=C.COLOR_TEXT_DIM if hidden else C.COLOR_TEXT_PRIMARY)

            if st and not hidden:
                sides = [("blue", b.blue_ti), ("red", b.red_ti)]
                for side, ti in sides:
                    d = st.get(side) or {}
                    vals = [
                        str(d.get("kills", 0)),
                        f"{d.get('gold', 0) / 1000:.1f}k",
                        str(d.get("towers", 0)),
                        str(len(d.get("dragons", []))),
                        str(d.get("barons", 0)),
                        str(d.get("inhibitors", 0)),
                    ]
                    cells = b.stat_cells.get(side, [])
                    for cell, val in zip(cells, vals):
                        if cell.winfo_exists():
                            cell.configure(text=val)

                bg_gold = (st.get("blue") or {}).get("gold", 0)
                rg_gold = (st.get("red") or {}).get("gold", 0)
                diff = bg_gold - rg_gold
                if b.lbl_diff and b.lbl_diff.winfo_exists():
                    if bg_gold or rg_gold:
                        lead_code = m[f"team{sides[0][1]}_code"] if diff > 0 else m[f"team{sides[1][1]}_code"]
                        txt = "Gold even" if abs(diff) < 500 else f"{lead_code} +{abs(diff) / 1000:.1f}k gold"
                        b.lbl_diff.configure(text=txt)
                    else:
                        b.lbl_diff.configure(text="")

                for side in ("blue", "red"):
                    curr_p = (st.get(side) or {}).get("players", [])
                    champ_lbls = b.player_champs.get(side, [])
                    for p_data, c_lbl in zip(curr_p, champ_lbls):
                        if c_lbl.winfo_exists():
                            c_lbl.configure(text=p_data.get("champion", ""))

        return True

    def _build(self) -> None:
        self._live_bindings.clear()
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
        border = C.COLOR_GOLD if strong else C.COLOR_BORDER
        c = tk.Frame(self.body, bg=C.COLOR_SURFACE, highlightbackground=border, highlightthickness=1)
        c.pack(fill="x", padx=px(18), pady=px(6))

        hidden = cards.scores_hidden(a, m)
        blue_is_team1 = False
        if st:
            blue_is_team1 = st.get("blue", {}).get("team_id") == m.get("team1_id") or \
                st.get("blue_team_id") == m.get("team1_id")
        blue_ti = 1 if blue_is_team1 else 2
        red_ti = 2 if blue_is_team1 else 1
        binding = _LiveCardBinding(m["match_id"], hidden, bool(st), blue_ti, red_ti)
        self._live_bindings[m["match_id"]] = binding

        top = tk.Frame(c, bg=C.COLOR_SURFACE)
        top.pack(fill="x", padx=px(14), pady=(px(10), 0))
        pill(top, "● LIVE", C.COLOR_LIVE, fg="white").pack(side="left")
        label(top, f"  {m['league_name']}" + (f" · {m['block_name']}" if m.get("block_name") else ""), 9, True,
              fg=C.COLOR_TEXT_MUTED).pack(side="left")
        g = next((x for x in m.get("games", []) if x.get("state") == "inProgress"), None)
        if g and not hidden:
            lbl_game = label(top, f"Game {g.get('number')} · Best of {m.get('best_of', 1)}", 9, True,
                             fg=C.COLOR_CYAN)
        else:  # the game number would reveal the series score (Game 5 of a Bo5 means 2-2)
            lbl_game = label(top, f"Best of {m.get('best_of', 1)}", 9, True, fg=C.COLOR_CYAN)
        lbl_game.pack(side="right")
        binding.lbl_game = lbl_game

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
        lbl_score = label(center, f"{s1}  :  {s2}", 26, True,
                          fg=C.COLOR_TEXT_DIM if hidden else C.COLOR_TEXT_PRIMARY)
        lbl_score.pack()
        binding.lbl_score = lbl_score
        label(center, "series", 8, fg=C.COLOR_TEXT_DIM).pack()

        if st:
            self._stats_panel(c, m, st, hidden, binding)
        else:
            label(c, "In-game stats are not available for this broadcast yet.", 8,
                  fg=C.COLOR_TEXT_DIM).pack(pady=(0, px(4)))

        bottom = tk.Frame(c, bg=C.COLOR_SURFACE)
        bottom.pack(fill="x", padx=px(14), pady=(px(4), px(12)))
        cards.reason_chips(bottom, reasons).pack(side="left")
        button(bottom, "▶ Watch live", lambda m=m: a.watch(m), bg=C.COLOR_LIVE, fg="white",
               hover_bg="#ff5b70").pack(side="right")
        if hidden:
            button(bottom, "Reveal scores", lambda mid=m["match_id"]: a.reveal(mid), size=8, bold=False,
                   fg=C.COLOR_TEXT_MUTED).pack(side="right", padx=px(8))

    def _stats_panel(self, parent, m, st, hidden: bool, binding: Optional[_LiveCardBinding] = None) -> None:
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
                    c_lbl = label(grid, str(v), 11, True, bg=C.COLOR_BG_DARK)
                    c_lbl.grid(row=row, column=col)
                    if binding:
                        binding.stat_cells[side].append(c_lbl)
            bg_gold = (st.get("blue") or {}).get("gold", 0)
            rg_gold = (st.get("red") or {}).get("gold", 0)
            diff = bg_gold - rg_gold
            if bg_gold or rg_gold:
                lead_code = m[f"team{sides[0][1]}_code"] if diff > 0 else m[f"team{sides[1][1]}_code"]
                txt = "Gold even" if abs(diff) < 500 else f"{lead_code} +{abs(diff) / 1000:.1f}k gold"
            else:
                txt = ""
            diff_lbl = label(box, txt, 9, True, fg=C.COLOR_GOLD, bg=C.COLOR_BG_DARK)
            diff_lbl.pack(pady=(0, px(6)))
            if binding:
                binding.lbl_diff = diff_lbl

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
                c_lbl = label(row, p.get("champion", ""), 8, fg=C.COLOR_TEXT_MUTED, bg=C.COLOR_BG_DARK)
                c_lbl.pack(side="right")
                if binding:
                    binding.player_champs[side].append(c_lbl)


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

        self._range_btns = {}
        for key, text in RANGES:
            b = button(self.filters, text, lambda k=key: self._set("schedule_filter_range", k), size=9)
            b.pack(side="left", padx=(0, px(4)))
            self._range_btns[key] = b

        self._btn_fo = button(self.filters, "☆ Followed only",
                              lambda: self._set("schedule_filter_followed",
                                                not self.app.settings.get("schedule_filter_followed", False)),
                              size=9)
        self._btn_fo.pack(side="left", padx=(px(12), px(4)))

        self._btn_leagues = button(self.filters, "🏆 Leagues: All  ▾", self.open_league_selector, size=9,
                                   tooltip="Click to select individual LoL Esports leagues for the schedule")
        self._btn_leagues.pack(side="left", padx=px(4))
        self._mb_league = self._btn_leagues  # Backwards compatibility alias
        label(self.filters, "Times in your local time zone", 8, fg=C.COLOR_TEXT_DIM).pack(side="right")
        self._known_leagues = None
        self._visible_count = 25

    def open_league_selector(self) -> None:
        from .leagues import LeagueFilterDialog
        LeagueFilterDialog(self.winfo_toplevel(), self.app, on_apply=self._on_leagues_applied)

    def _on_leagues_applied(self, selected_slugs: List[str]) -> None:
        self._visible_count = 25
        if hasattr(self.app, "worker"):
            self.app.worker.request("schedule")
        self.after(1, self.render)

    def _update_filters(self) -> None:
        s = self.app.settings
        cur = s.get("schedule_filter_range", "upcoming")
        for key, b in self._range_btns.items():
            on = key == cur
            set_button_colors(b, C.COLOR_GOLD if on else C.COLOR_SURFACE,
                              C.COLOR_BG if on else C.COLOR_TEXT_PRIMARY)
            b.configure(text=dict(RANGES).get(key, key))

        fo = s.get("schedule_filter_followed", False)
        set_button_colors(self._btn_fo, C.COLOR_CYAN_DIM if fo else C.COLOR_SURFACE,
                          C.COLOR_TEXT_PRIMARY)
        self._btn_fo.configure(text=("★ " if fo else "☆ ") + "Followed only")

        selected = s.get("schedule_selected_leagues", [])
        legacy = s.get("schedule_filter_league", "")
        if not selected and legacy:
            selected = [legacy]

        if not selected:
            self._btn_leagues.configure(text="🏆 Leagues: All  ▾")
            set_button_colors(self._btn_leagues, C.COLOR_SURFACE, C.COLOR_TEXT_PRIMARY)
        elif len(selected) == 1:
            slug = selected[0]
            cat = self.app.state.get("catalog")
            name = slug.upper()
            if cat and hasattr(cat, "league_by_slug"):
                l_obj = cat.league_by_slug.get(slug)
                if l_obj:
                    name = l_obj.get("name", name)
            self._btn_leagues.configure(text=f"🏆 League: {name}  ▾")
            set_button_colors(self._btn_leagues, C.COLOR_GOLD, C.COLOR_BG)
        elif len(selected) <= 3:
            names = [s.upper() for s in selected]
            self._btn_leagues.configure(text=f"🏆 Leagues: {', '.join(names)}  ▾")
            set_button_colors(self._btn_leagues, C.COLOR_GOLD, C.COLOR_BG)
        else:
            self._btn_leagues.configure(text=f"🏆 Leagues ({len(selected)} Selected)  ▾")
            set_button_colors(self._btn_leagues, C.COLOR_GOLD, C.COLOR_BG)

    def _set(self, key: str, value) -> None:
        self.app.settings.set(key, value)
        self._visible_count = 25
        self._update_filters()
        self.after(1, self.render)

    def _show_more(self) -> None:
        self._visible_count += 25
        self.after(1, self.render)

    def filtered(self) -> List[Dict[str, Any]]:
        a, s = self.app, self.app.settings
        rng = s.get("schedule_filter_range", "upcoming")
        selected_leagues = set(s.get("schedule_selected_leagues", []))
        legacy_league = s.get("schedule_filter_league", "")
        if legacy_league and not selected_leagues:
            selected_leagues = {legacy_league}

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
            if selected_leagues and m["league_slug"] not in selected_leagues:
                continue
            if followed_only and not a.watchlist.is_followed(m):
                continue
            if rng == "upcoming" and m["state"] == "completed":
                continue
            if rng == "today" and dt.astimezone().date() != today:
                continue
            if rng == "results" and (m["state"] != "completed" or now - dt > datetime.timedelta(days=14)):
                continue
            out.append(m)
        out.sort(key=lambda m: m["start_time_utc"], reverse=(rng == "results"))
        return out[:150]

    def _build(self) -> None:
        self._update_filters()
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
        visible_matches = matches[:self._visible_count]
        for m in visible_matches:
            d = format_local_day(m["start_time_utc"])
            if d != day:
                day = d
                self.section(d)
            cards.match_row(self.body, self.app, m).pack(fill="x", padx=px(18), pady=px(4))
        if len(matches) > len(visible_matches):
            remaining = len(matches) - len(visible_matches)
            show_n = min(25, remaining)
            row = tk.Frame(self.body, bg=C.COLOR_BG)
            row.pack(fill="x", padx=px(18), pady=px(12))
            button(row, f"▼ Show {show_n} more match{'es' if show_n != 1 else ''} ({remaining} remaining)",
                   self._show_more, size=9, bg=C.COLOR_SURFACE, fg=C.COLOR_CYAN,
                   hover_bg=C.COLOR_SURFACE_HOVER).pack(fill="x")
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
        online = a.state.get("stream_online", True)
        self.section("24/7 Broadcast Replays", f"twitch.tv/{C.TWITCH_CHANNEL} · youtube.com/{C.YOUTUBE_CHANNEL}")
        is_live = cur and (online is not False)
        hero = tk.Frame(self.body, bg=C.COLOR_SURFACE, highlightbackground=C.COLOR_LIVE if is_live else C.COLOR_BORDER,
                        highlightthickness=1)
        hero.pack(fill="x", padx=px(18))
        if cur and is_live:
            top = tk.Frame(hero, bg=C.COLOR_SURFACE)
            top.pack(fill="x", padx=px(14), pady=(px(12), 0))
            pill(top, "24/7 STREAM", C.COLOR_CYAN_DIM, fg=C.COLOR_TEXT_PRIMARY).pack(side="left")
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
            top = tk.Frame(hero, bg=C.COLOR_SURFACE)
            top.pack(fill="x", padx=px(14), pady=(px(12), 0))
            pill(top, "OFFLINE", C.COLOR_BORDER, fg=C.COLOR_TEXT_MUTED).pack(side="left")
            label(hero, "Stream Offline", 18, True, fg=C.COLOR_TEXT_MUTED).pack(
                anchor="w", padx=px(14), pady=(px(6), 0))
            label(hero, "The 24/7 broadcast is currently offline on Twitch and YouTube.", 10,
                  fg=C.COLOR_TEXT_DIM).pack(anchor="w", padx=px(14))
            nxt = upcoming(events, now, limit=1)
            if nxt:
                label(hero, f"Next scheduled rebroadcast: {event_title(nxt[0])} · {format_relative_time(nxt[0]['start_utc'], now)}",
                      10, fg=C.COLOR_CYAN).pack(anchor="w", padx=px(14), pady=(px(4), 0))
        btns = tk.Frame(hero, bg=C.COLOR_SURFACE)
        btns.pack(fill="x", padx=px(14), pady=px(12))
        button(btns, "▶ Watch on Twitch", lambda: a.open_url(C.TWITCH_CHANNEL_URL), bg="#9146ff", fg="white",
               hover_bg="#a970ff").pack(side="left")
        button(btns, "▶ Watch on YouTube", lambda: a.open_url(C.YOUTUBE_LIVE_URL), bg="#cc0000", fg="white",
               hover_bg="#e60000").pack(side="left", padx=px(8))
        button(btns, "Full schedule on lolworlds.com ↗", lambda: a.open_url(C.STREAM_SITE_URL), size=9,
               bold=False).pack(side="left", padx=px(8))

        banger = next_banger(events, now)
        if banger:
            b = tk.Frame(self.body, bg=C.COLOR_SURFACE, highlightbackground=C.COLOR_BANGER, highlightthickness=1)
            b.pack(fill="x", padx=px(18), pady=(px(10), 0))
            b_top = tk.Frame(b, bg=C.COLOR_SURFACE)
            b_top.pack(fill="x", padx=px(14), pady=(px(8), 0))
            label(b_top, "NEXT S-TIER BANGER", 8, True, fg=C.COLOR_BANGER).pack(side="left")
            label(b, f"{event_title(banger)}   ·   {event_subtitle(banger)}", 12, True).pack(anchor="w", padx=px(14), pady=(px(2), 0))
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
        self.applied_query = ""
        self.expanded: Optional[str] = None
        self._row_bindings: Dict[str, Tuple[Any, ...]] = {}
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
        self.entry.bind("<Return>", lambda e: self._apply_search())
        self.entry.bind("<KP_Enter>", lambda e: self._apply_search())
        self.entry.bind("<Escape>", lambda e: self._clear_search())
        label(bar, "Search", 9, fg=C.COLOR_TEXT_MUTED).pack(side="right", padx=px(6))
        self._after = None
        self.query.trace_add("write", lambda *_: self._debounce())
        self.scroll.pack(fill="both", expand=True)

        self._mode_btns = {}
        for key, text in (("teams", "Teams"), ("players", "Players"), ("regions", "Regions"), ("leagues", "Leagues")):
            b = button(self.modebar, text, lambda k=key: self._set_mode(k), size=9)
            b.pack(side="left", padx=(0, px(4)))
            self._mode_btns[key] = b

    def _debounce(self):
        if self._after:
            try:
                self.after_cancel(self._after)
            except Exception:
                pass
            self._after = None
        # Fast debounce (40ms) when input is emptied, standard (280ms) while typing
        delay = 40 if not self.query.get().strip() else 280
        self._after = self.after(delay, self._apply_search)

    def _apply_search(self):
        if self._after:
            try:
                self.after_cancel(self._after)
            except Exception:
                pass
            self._after = None
        new_q = self.query.get().strip().lower()
        if new_q != self.applied_query:
            self.applied_query = new_q
            self.scroll.to_top()
            self.render()

    def _clear_search(self):
        self.query.set("")
        self._apply_search()

    def signature(self) -> tuple:
        return super().signature() + (self.mode, self.applied_query, self.expanded)

    def _update_modebar(self):
        for key, b in self._mode_btns.items():
            on = key == self.mode
            set_button_colors(b, C.COLOR_GOLD if on else C.COLOR_SURFACE,
                              C.COLOR_BG if on else C.COLOR_TEXT_PRIMARY)

    def _set_mode(self, mode):
        self.mode, self.expanded = mode, None
        new_q = self.query.get().strip().lower()
        if new_q != self.applied_query:
            self.applied_query = new_q
        self._update_modebar()
        self.scroll.to_top()
        self.after(1, lambda: self.app.request_render(self))

    def _build(self) -> None:
        self._update_modebar()
        self._row_bindings.clear()
        clear(self.body)
        self._build_following_container()
        self._refresh_following()
        cat = self.app.state["catalog"]
        if cat.empty and self.mode not in ("leagues", "regions"):
            self.empty("Loading the team directory…", "Downloading teams and rosters from Riot (about 1.5 MB, "
                       "refreshed once a day).")
            return
        {"teams": self._teams, "players": self._players, "regions": self._regions, "leagues": self._leagues}[self.mode]()
        tk.Frame(self.body, bg=C.COLOR_BG, height=px(16)).pack()

    # ---- following summary (isolated sub-container)
    def _build_following_container(self) -> None:
        self._following_section = tk.Frame(self.body, bg=C.COLOR_BG)
        self._following_section.pack(fill="x", padx=px(18), pady=(px(16), px(6)))
        label(self._following_section, "FOLLOWING", 10, True, fg=C.COLOR_GOLD).pack(side="left")
        self._following_count_lbl = label(self._following_section, "", 9, fg=C.COLOR_TEXT_MUTED)
        self._following_count_lbl.pack(side="left", padx=px(10))
        self._following_chips_frame = tk.Frame(self.body, bg=C.COLOR_BG)
        self._following_chips_frame.pack(fill="x", padx=px(18))

    def _refresh_following(self) -> None:
        if not hasattr(self, "_following_chips_frame") or not self._following_chips_frame.winfo_exists():
            return
        s = self.app.settings
        teams = s.followed_teams()
        players = s.get("followed_players", [])
        regions = s.followed_regions()
        leagues = s.get("followed_leagues", [])

        if hasattr(self, "_following_count_lbl") and self._following_count_lbl.winfo_exists():
            self._following_count_lbl.configure(
                text=f"{len(teams)} teams · {len(players)} players · {len(regions)} regions · {len(leagues)} leagues"
            )
        clear(self._following_chips_frame)

        if not (teams or players or regions or leagues):
            label(self._following_chips_frame,
                  "Star teams, players, and regions below (or on any match card) to follow them.",
                  9, fg=C.COLOR_TEXT_MUTED).pack(anchor="w")
            return

        chips = []
        for r in regions:
            chips.append((
                f"🌐 {r}",
                lambda reg=r: self._handle_toggle("region", reg.lower(), lambda: self.app.toggle_region(reg),
                                                  lambda: self.app.settings.is_region_followed(reg)),
                C.COLOR_CYAN_DIM
            ))
        for t in teams:
            code = t.get("code", "")
            name = t.get("name", "")
            chips.append((
                f"★ {name or code}",
                lambda c=code, n=name: self._handle_toggle("team", c.upper(), lambda: self.app.toggle_team(c, n),
                                                           lambda: self.app.settings.is_team_followed(c, n)),
                C.COLOR_GOLD
            ))
        for p in players:
            chips.append((
                f"★ {p}",
                lambda pl=p: self._handle_toggle("player", pl.lower(), lambda: self.app.toggle_player(pl),
                                                 lambda: self.app.settings.is_player_followed(pl)),
                C.COLOR_CYAN_DIM
            ))
        for l in leagues:
            chips.append((
                f"🏆 {l.upper()}",
                lambda lg=l: self._handle_toggle("league", lg.lower(), lambda: self.app.toggle_league(lg),
                                                 lambda: self.app.settings.is_league_followed(lg)),
                C.COLOR_GOLD
            ))

        budget = max(px(500), (self.winfo_width() or 800) - px(80))
        used = 0
        row = None
        for text, cb, color in chips:
            w = px(len(text) * 8 + 40)
            if row is None or used + w > budget:
                row = tk.Frame(self._following_chips_frame, bg=C.COLOR_BG)
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

    def _apply_button_state(self, btn: tk.Label, on: bool) -> None:
        if not btn or not btn.winfo_exists():
            return
        bg = C.COLOR_GOLD if on else C.COLOR_SURFACE_HOVER
        fg = C.COLOR_BG if on else C.COLOR_TEXT_PRIMARY
        hover_bg = C.COLOR_GOLD_HOVER if on else C.COLOR_BORDER
        text = "★ Following" if on else "☆ Follow"
        set_button_colors(btn, bg, fg, hover_bg)
        btn.configure(text=text)

    def _handle_toggle(self, kind: str, key: str, toggle_fn: Callable, check_fn: Callable) -> None:
        toggle_fn()
        # Keep rendered signature up-to-date so poll loop doesn't trigger full View.render()
        self.app.rendered["watchlist"] = self.signature()
        full_key = f"{kind}:{key}"
        binding = self._row_bindings.get(full_key)
        if binding:
            btn, row_frame, name_lbl = binding
            is_on = check_fn()
            self._apply_button_state(btn, is_on)
            if row_frame and row_frame.winfo_exists():
                row_frame.configure(highlightbackground=C.COLOR_GOLD if is_on else C.COLOR_BORDER)
            if name_lbl and name_lbl.winfo_exists():
                name_lbl.configure(fg=C.COLOR_GOLD if is_on else C.COLOR_TEXT_PRIMARY)
        self._refresh_following()

    def _follow_btn(self, parent, on: bool, command) -> tk.Label:
        return button(parent, "★ Following" if on else "☆ Follow", command, size=8,
                      bg=C.COLOR_GOLD if on else C.COLOR_SURFACE_HOVER, fg=C.COLOR_BG if on else C.COLOR_TEXT_PRIMARY,
                      hover_bg=C.COLOR_GOLD_HOVER if on else C.COLOR_BORDER)

    # ---- teams
    def _teams(self) -> None:
        a = self.app
        cat = a.state["catalog"]
        q = self.applied_query
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
        code, name = t["code"], t["name"]
        full_key = f"team:{code.upper()}"
        on = a.settings.is_team_followed(code, name)
        row = tk.Frame(self.body, bg=C.COLOR_SURFACE, highlightthickness=1,
                       highlightbackground=C.COLOR_GOLD if on else C.COLOR_BORDER)
        row.pack(fill="x", padx=px(18), pady=px(2))
        head = tk.Frame(row, bg=C.COLOR_SURFACE)
        head.pack(fill="x")
        cards.logo(head, a, t.get("image", ""), 28, code).pack(side="left", padx=px(10), pady=px(6))
        name_lbl = label(head, name, 10, True)
        name_lbl.pack(side="left")
        label(head, f"  {code} · {t.get('league_name', '')}", 9, fg=C.COLOR_TEXT_MUTED).pack(side="left")
        btn = self._follow_btn(
            head, on,
            lambda c=code, n=name: self._handle_toggle(
                "team", c.upper(), lambda: a.toggle_team(c, n), lambda: a.settings.is_team_followed(c, n)
            )
        )
        btn.pack(side="right", padx=px(10))
        self._row_bindings[full_key] = (btn, row, None)
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
        q = self.applied_query
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
        p_name = p.name
        full_key = f"player:{p_name.lower()}"
        on = a.settings.is_player_followed(p_name)
        bg = parent.cget("bg") if parent is not self.body else C.COLOR_SURFACE
        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x", padx=px(18) if parent is self.body else px(8), pady=1)
        label(row, role_label(p.role), 8, fg=C.COLOR_TEXT_DIM, bg=bg, width=8, anchor="w").pack(side="left",
                                                                                              padx=px(8), pady=px(4))
        name_lbl = label(row, p_name, 10, True, fg=C.COLOR_GOLD if on else C.COLOR_TEXT_PRIMARY, bg=bg)
        name_lbl.pack(side="left")
        if p.real_name:
            label(row, f"  {p.real_name}", 8, fg=C.COLOR_TEXT_DIM, bg=bg).pack(side="left")
        if show_team:
            cat = a.state.get("catalog")
            img = cat.team_image(p.team_code, p.team_name) if cat else ""
            cards.logo(row, a, img, 18, p.team_code).pack(side="left", padx=(px(6), px(2)))
            label(row, f"{p.team_name} ({p.team_code})", 9, fg=C.COLOR_TEXT_MUTED, bg=bg).pack(side="left")
        btn = self._follow_btn(
            row, on,
            lambda pl=p_name: self._handle_toggle(
                "player", pl.lower(), lambda: a.toggle_player(pl), lambda: a.settings.is_player_followed(pl)
            )
        )
        btn.pack(side="right", padx=px(8))
        self._row_bindings[full_key] = (btn, row if parent is self.body else None, name_lbl)

    # ---- regions
    def _batch_toggle_regions(self, follow: bool) -> None:
        if follow:
            self.app.follow_all_regions()
        else:
            self.app.unfollow_all_regions()
        self.app.rendered["watchlist"] = self.signature()
        for r in C.MAJOR_REGIONS:
            r_name = r["name"]
            binding = self._row_bindings.get(f"region:{r_name.lower()}")
            if binding:
                btn, card, name_lbl = binding
                is_on = self.app.settings.is_region_followed(r_name) or self.app.settings.is_region_followed(r["code"])
                self._apply_button_state(btn, is_on)
                if card and card.winfo_exists():
                    card.configure(highlightbackground=C.COLOR_GOLD if is_on else C.COLOR_BORDER)
                if name_lbl and name_lbl.winfo_exists():
                    name_lbl.configure(fg=C.COLOR_GOLD if is_on else C.COLOR_TEXT_PRIMARY)
        self._refresh_following()

    def _regions(self) -> None:
        a = self.app
        q = self.applied_query
        regions = list(C.MAJOR_REGIONS)
        if q:
            regions = [r for r in regions if q in r["name"].lower() or q in r["code"].lower()
                       or any(q in l.lower() for l in r.get("leagues", []))]
        self.section("Regions & Tournaments", "follow competitive ecosystems to track all of their matches")
        row = tk.Frame(self.body, bg=C.COLOR_BG)
        row.pack(fill="x", padx=px(18), pady=(0, px(6)))
        button(row, "★ Follow All Major Regions",
               lambda: self._batch_toggle_regions(True), size=8, bold=False).pack(side="left")
        button(row, "Unfollow All Regions",
               lambda: self._batch_toggle_regions(False), size=8, bold=False).pack(side="left", padx=px(6))
        if not regions:
            self.empty("No regions match that search")
            return
        for r in regions:
            r_name, r_code = r["name"], r["code"]
            full_key = f"region:{r_name.lower()}"
            on = a.settings.is_region_followed(r_name) or a.settings.is_region_followed(r_code)
            card = tk.Frame(self.body, bg=C.COLOR_SURFACE, highlightthickness=1,
                            highlightbackground=C.COLOR_GOLD if on else C.COLOR_BORDER)
            card.pack(fill="x", padx=px(18), pady=px(2))
            head = tk.Frame(card, bg=C.COLOR_SURFACE)
            head.pack(fill="x", padx=px(12), pady=px(8))
            label(head, r.get("badge", "🌐"), 14).pack(side="left", padx=(0, px(8)))
            name_lbl = label(head, r_name, 11, True, fg=C.COLOR_GOLD if on else C.COLOR_TEXT_PRIMARY)
            name_lbl.pack(side="left")
            leagues_str = " · ".join(r.get("leagues", []))
            label(head, f"  ({leagues_str})", 9, fg=C.COLOR_TEXT_MUTED).pack(side="left")
            btn = self._follow_btn(
                head, on,
                lambda reg=r_name, code=r_code: self._handle_toggle(
                    "region", reg.lower(), lambda: a.toggle_region(reg),
                    lambda: a.settings.is_region_followed(reg) or a.settings.is_region_followed(code)
                )
            )
            btn.pack(side="right")
            self._row_bindings[full_key] = (btn, card, name_lbl)

    # ---- leagues
    def _batch_follow_leagues(self, slugs: List[str]) -> None:
        self.app.follow_leagues(slugs)
        self.app.rendered["watchlist"] = self.signature()
        for s in slugs:
            binding = self._row_bindings.get(f"league:{s.lower()}")
            if binding:
                btn, r, _ = binding
                is_on = self.app.settings.is_league_followed(s)
                self._apply_button_state(btn, is_on)
                if r and r.winfo_exists():
                    r.configure(highlightbackground=C.COLOR_GOLD if is_on else C.COLOR_BORDER)
        self._refresh_following()

    def _leagues(self) -> None:
        a = self.app
        leagues = a.state["catalog"].leagues
        if not leagues:
            self.empty("Loading leagues…")
            return
        q = self.applied_query
        if q:
            leagues = [l for l in leagues if q in l["name"].lower() or q in (l.get("region") or "").lower()]
        self.section("Leagues", "matches from followed leagues show in 'Followed only' and on the Live tab")
        row = tk.Frame(self.body, bg=C.COLOR_BG)
        row.pack(fill="x", padx=px(18), pady=(0, px(6)))
        button(row, "Follow the international events (Worlds, MSI, First Stand)",
               lambda: self._batch_follow_leagues(["worlds", "msi", "first_stand"]), size=8, bold=False).pack(side="left")
        region = None
        for l in sorted(leagues, key=lambda l: (l.get("region") != "INTERNATIONAL", l.get("region") or "", l["priority"])):
            if l.get("region") != region:
                region = l.get("region")
                label(self.body, (region or "Other").title(), 9, True, fg=C.COLOR_TEXT_MUTED).pack(
                    anchor="w", padx=px(20), pady=(px(8), px(2)))
            slug, name = l["slug"], l["name"]
            full_key = f"league:{slug.lower()}"
            on = a.settings.is_league_followed(slug)
            r = tk.Frame(self.body, bg=C.COLOR_SURFACE, highlightthickness=1,
                         highlightbackground=C.COLOR_GOLD if on else C.COLOR_BORDER)
            r.pack(fill="x", padx=px(18), pady=px(2))
            cards.logo(r, a, l.get("image", ""), 24, name[:3]).pack(side="left", padx=px(10), pady=px(5))
            label(r, name, 10, True).pack(side="left")
            btn = self._follow_btn(
                r, on,
                lambda s=slug: self._handle_toggle(
                    "league", s.lower(), lambda: a.toggle_league(s), lambda: a.settings.is_league_followed(s)
                )
            )
            btn.pack(side="right", padx=px(10))
            self._row_bindings[full_key] = (btn, r, None)


# =============================================================================
# SETTINGS
# =============================================================================
class SettingsView(View):
    deps = ("update", "update_progress")

    def signature(self) -> tuple:
        # SettingsView handles all preference edits in-place with instant feedback.
        # Only rebuild when external updater state changes.
        return tuple(self.app.versions.get(d, 0) for d in self.deps)

    def _build(self) -> None:
        clear(self.body)
        a, s = self.app, self.app.settings

        self.section("Display & Experience")
        self._toggle("Spoiler mode", "Hide all scores, results and in-game stats until you reveal a match.",
                     s.get("spoiler_mode", False), lambda _: a.toggle_spoiler())

        # Live Ticker Bar Mode
        ticker_row = tk.Frame(self.body, bg=C.COLOR_SURFACE)
        ticker_row.pack(fill="x", padx=px(18), pady=px(2))
        ticker_txt = tk.Frame(ticker_row, bg=C.COLOR_SURFACE)
        ticker_txt.pack(side="left", padx=px(12), pady=px(8))
        label(ticker_txt, "Live Ticker Mode", 10, True).pack(anchor="w")
        label(ticker_txt, "Real-time scores, countdowns, and 24/7 stream highlights bar.", 8,
              fg=C.COLOR_TEXT_MUTED).pack(anchor="w")

        ticker_btns = tk.Frame(ticker_row, bg=C.COLOR_SURFACE)
        ticker_btns.pack(side="right", padx=px(12))
        cur_mode = a.get_ticker_mode()
        t_mode_btns = {}

        def _set_ticker_mode(mode: str):
            a.set_ticker_mode(mode)
            for m, btn in t_mode_btns.items():
                is_sel = (m == mode)
                btn.configure(
                    bg=C.COLOR_CYAN_DIM if is_sel else C.COLOR_BORDER,
                    fg=C.COLOR_TEXT_PRIMARY if is_sel else C.COLOR_TEXT_MUTED,
                )
                btn._base_bg = C.COLOR_CYAN_DIM if is_sel else C.COLOR_BORDER

        for m_key, m_label in (("docked", "Docked"), ("detached", "⧉ Detached HUD"), ("hidden", "Hidden")):
            is_sel = (m_key == cur_mode)
            b = button(ticker_btns, m_label,
                       lambda k=m_key: _set_ticker_mode(k),
                       size=8, padx=8, pady=3,
                       bg=C.COLOR_CYAN_DIM if is_sel else C.COLOR_BORDER,
                       fg=C.COLOR_TEXT_PRIMARY if is_sel else C.COLOR_TEXT_MUTED)
            b.pack(side="left", padx=px(2))
            t_mode_btns[m_key] = b

        self._toggle("Detached Ticker Always on Top",
                     "Keep the floating desktop ticker bar pinned above games and other windows.",
                     s.get("ticker_topmost", True),
                     lambda v: (s.set("ticker_topmost", v),
                                getattr(a, "detached_ticker_window", None) and a.detached_ticker_window.attributes("-topmost", v)))

        # Default tab selector
        tab_row = tk.Frame(self.body, bg=C.COLOR_SURFACE)
        tab_row.pack(fill="x", padx=px(18), pady=px(2))
        tab_txt = tk.Frame(tab_row, bg=C.COLOR_SURFACE)
        tab_txt.pack(side="left", padx=px(12), pady=px(8))
        label(tab_txt, "Default tab on launch", 10, True).pack(anchor="w")
        label(tab_txt, "Choose which view opens automatically when starting RiftWatch.", 8,
              fg=C.COLOR_TEXT_MUTED).pack(anchor="w")
        tab_btns = tk.Frame(tab_row, bg=C.COLOR_SURFACE)
        tab_btns.pack(side="right", padx=px(12))
        cur_def = s.get("default_tab", "live")
        tab_btns_map = {}

        def _set_default_tab(tab_key: str):
            s.set("default_tab", tab_key)
            for k, btn in tab_btns_map.items():
                is_sel = (k == tab_key)
                btn.configure(
                    bg=C.COLOR_GOLD if is_sel else C.COLOR_BORDER,
                    fg=C.COLOR_BG if is_sel else C.COLOR_TEXT_MUTED,
                )
                btn._base_bg = C.COLOR_GOLD if is_sel else C.COLOR_BORDER

        for t_key, t_label in (("live", "Live"), ("schedule", "Schedule"), ("stream", "24/7 Stream"), ("watchlist", "Watchlist")):
            is_sel = (t_key == cur_def)
            b = button(tab_btns, t_label,
                       lambda k=t_key: _set_default_tab(k),
                       size=8, padx=8, pady=3,
                       bg=C.COLOR_GOLD if is_sel else C.COLOR_BORDER,
                       fg=C.COLOR_BG if is_sel else C.COLOR_TEXT_MUTED)
            b.pack(side="left", padx=px(2))
            tab_btns_map[t_key] = b

        self.section("Desktop Notifications & Alerts")
        self._toggle("Live kickoff alerts",
                     "Display desktop toast notifications when followed teams or players begin a match.",
                     s.get("notify_kickoff", True),
                     lambda v: s.set("notify_kickoff", v))
        self._toggle("Pre-match 15m countdown",
                     "Display a reminder notification 15 minutes before followed matches start.",
                     s.get("notify_pregame", True),
                     lambda v: s.set("notify_pregame", v))
        self._toggle("24/7 stream broadcast alerts",
                     "Notify when the 24/7 stream goes online or S-Tier banger matches begin.",
                     s.get("notify_stream", True),
                     lambda v: s.set("notify_stream", v))

        self.section("System Tray & Startup")
        self._toggle("Close button minimizes to system tray",
                     "Keep RiftWatch running in the background notification area when the window is closed.",
                     s.get("minimize_to_tray_on_close", True),
                     lambda v: s.set("minimize_to_tray_on_close", v))
        self._toggle("Start RiftWatch with Windows", "Launch automatically when you sign in.",
                     s.get("start_with_windows", False), a.toggle_autostart)

        self.section("Watchlist & Following")
        wbox = tk.Frame(self.body, bg=C.COLOR_SURFACE)
        wbox.pack(fill="x", padx=px(18), pady=px(4))
        wtxt = tk.Frame(wbox, bg=C.COLOR_SURFACE)
        wtxt.pack(side="left", padx=px(12), pady=px(10))
        n_teams = len(s.followed_teams())
        n_players = len(s.get("followed_players", []))
        n_regions = len(s.get("followed_regions", []))
        n_leagues = len(s.get("followed_leagues", []))
        label(wtxt, "Watchlist Management", 10, True).pack(anchor="w")
        label(wtxt, f"Currently following {n_teams} teams · {n_players} players · {n_regions} regions · {n_leagues} leagues",
              8, fg=C.COLOR_GOLD).pack(anchor="w", pady=(px(2), 0))
        w_actions = tk.Frame(wbox, bg=C.COLOR_SURFACE)
        w_actions.pack(side="right", padx=px(10))
        button(w_actions, "Reset All Follows", a.reset_watchlist, size=8, bold=False,
               bg=C.COLOR_BORDER, fg=C.COLOR_TEXT_MUTED, hover_bg=C.COLOR_LIVE).pack(side="left", padx=px(4))

        self.section("24/7 Stream Rebroadcasts (Twitch & YouTube)")
        tbox = tk.Frame(self.body, bg=C.COLOR_SURFACE)
        tbox.pack(fill="x", padx=px(18), pady=px(4))
        ttxt = tk.Frame(tbox, bg=C.COLOR_SURFACE)
        ttxt.pack(side="left", padx=px(12), pady=px(10))
        label(ttxt, f"Twitch: twitch.tv/{C.TWITCH_CHANNEL}   ·   YouTube: {C.YOUTUBE_CHANNEL}", 10, True, fg=C.COLOR_CYAN).pack(anchor="w")
        label(ttxt, f"Schedule synced with {C.STREAM_SITE_URL} continuous marathon database.", 8,
              fg=C.COLOR_TEXT_MUTED).pack(anchor="w")
        t_actions = tk.Frame(tbox, bg=C.COLOR_SURFACE)
        t_actions.pack(side="right", padx=px(10))
        button(t_actions, "Watch on Twitch ↗", lambda: a.open_url(C.TWITCH_CHANNEL_URL),
               bg="#9146ff", fg="white", hover_bg="#a970ff", size=8).pack(side="left", padx=px(4))
        button(t_actions, "Watch on YouTube ↗", lambda: a.open_url(C.YOUTUBE_LIVE_URL),
               bg="#cc0000", fg="white", hover_bg="#e60000", size=8).pack(side="left", padx=px(4))
        button(t_actions, "View Schedule ↗", lambda: a.open_url(C.STREAM_SITE_URL), size=8, bold=False).pack(
            side="left", padx=px(4))

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

        self.section("Data Sources & Storage Diagnostics")
        names = {"schedule": "Match schedule (LoL Esports API)", "live": "Live matches (LoL Esports API)",
                 "stream": "24/7 stream schedule (lolworlds.com)", "catalog": "Teams & rosters (LoL Esports API)"}
        self._status_labels = {}
        for key, name in names.items():
            r = tk.Frame(self.body, bg=C.COLOR_SURFACE)
            r.pack(fill="x", padx=px(18), pady=1)
            dot_lbl = label(r, "○", 10, fg=C.COLOR_TEXT_DIM)
            dot_lbl.pack(side="left", padx=(px(12), px(6)), pady=px(6))
            label(r, name, 9, True).pack(side="left")
            txt_lbl = label(r, "waiting", 9, fg=C.COLOR_TEXT_MUTED)
            txt_lbl.pack(side="right", padx=px(12))
            self._status_labels[key] = (dot_lbl, txt_lbl)
            self._apply_status_item(key, a.state["status"].get(key))

        row = tk.Frame(self.body, bg=C.COLOR_BG)
        row.pack(fill="x", padx=px(18), pady=px(8))
        button(row, "Refresh team directory", lambda: a.worker_request("catalog"), size=8).pack(side="left")
        button(row, "Clear logo cache", a.clear_logo_cache, size=8, bold=False).pack(side="left", padx=px(6))
        button(row, "Open data folder", lambda: os.startfile(str(C.APPDATA_DIR)), size=8, bold=False).pack(
            side="left", padx=px(6))
        button(row, "View log file", a.open_logs, size=8, bold=False).pack(side="left", padx=px(6))

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

        state = {"on": bool(on)}
        b_ref: List[Optional[tk.Label]] = [None]

        def _on_click():
            new_val = not state["on"]
            state["on"] = new_val
            if b_ref[0]:
                b_ref[0].configure(
                    text="ON" if new_val else "OFF",
                    bg=C.COLOR_CYAN_DIM if new_val else C.COLOR_BORDER,
                )
                b_ref[0]._base_bg = C.COLOR_CYAN_DIM if new_val else C.COLOR_BORDER
            try:
                command(new_val)
            except TypeError:
                command()

        b = button(r, "ON" if on else "OFF", _on_click, size=9, padx=14,
                   bg=C.COLOR_CYAN_DIM if on else C.COLOR_BORDER, fg=C.COLOR_TEXT_PRIMARY)
        b.pack(side="right", padx=px(12))
        b_ref[0] = b

    def _apply_status_item(self, key: str, st: Optional[Dict[str, Any]]) -> None:
        if not hasattr(self, "_status_labels") or key not in self._status_labels:
            return
        dot_lbl, txt_lbl = self._status_labels[key]
        if st is None:
            dot, col, txt = "○", C.COLOR_TEXT_DIM, "waiting"
        elif st.get("ok"):
            dot, col = "●", C.COLOR_CYAN
            txt = ("cached copy is fresh" if st.get("detail") == "cached" else
                   "updated " + datetime.datetime.fromtimestamp(st["at"]).strftime("%I:%M:%S %p").lstrip("0"))
        else:
            dot, col, txt = "●", C.COLOR_LIVE, st.get("detail") or "error"
        dot_lbl.configure(text=dot, fg=col)
        txt_lbl.configure(text=txt)

    def update_status(self, key: str, st: Dict[str, Any]) -> None:
        try:
            self._apply_status_item(key, st)
        except Exception:
            pass
