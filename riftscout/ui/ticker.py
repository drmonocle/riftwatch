"""
RiftWatch Live Ticker Bar
Docked real-time sports ticker displaying live match scores, in-game gold differentials,
upcoming game countdowns, and 24/7 continuous stream highlights.
"""

from dataclasses import dataclass
import datetime
import logging
import tkinter as tk
from typing import Any, Dict, List, Optional

from .. import config as C
from ..data import format_relative_time, utcnow
from ..stream import event_subtitle, event_title, now_airing
from . import cards
from .widgets import button, font, px, Tooltip

log = logging.getLogger(__name__)


@dataclass
class TickerItem:
    kind: str  # "live", "upcoming", "stream", "result", "info"
    badge: str
    badge_bg: str
    badge_fg: str
    headline: str
    details: str
    tab_target: str
    tooltip: str = ""
    schedule_filter_range: Optional[str] = None
    match_id: Optional[str] = None


def gather_ticker_items(app) -> List[TickerItem]:
    """Compile prioritized real-time ticker items from current app state."""
    items: List[TickerItem] = []
    now = utcnow()

    # 1. Live pro matches in progress (Highest Priority)
    live_matches = app.state.get("live") or []
    for m in live_matches:
        t1 = m.get("team1_code") or m.get("team1_name") or "TBD"
        t2 = m.get("team2_code") or m.get("team2_name") or "TBD"
        league = m.get("league_name", "")
        hidden = cards.scores_hidden(app, m)

        if hidden:
            headline = f"{league} · {t1} vs {t2}"
            details = "Scores hidden (Spoiler mode)"
        else:
            s1, s2 = cards.score_text(app, m)
            headline = f"{league} · {t1} {s1} : {s2} {t2}"
            g = next((x for x in m.get("games", []) if x.get("state") == "inProgress"), None)
            g_str = f"Game {g.get('number')} of Bo{m.get('best_of', 1)}" if g else f"Best of {m.get('best_of', 1)}"

            # Live in-game stats & gold lead
            st = app.state.get("livestats", {}).get(m.get("match_id", ""))
            gold_str = ""
            if st:
                bg_gold = (st.get("blue") or {}).get("gold", 0)
                rg_gold = (st.get("red") or {}).get("gold", 0)
                diff = bg_gold - rg_gold
                if abs(diff) >= 500:
                    blue_is_team1 = (st.get("blue", {}).get("team_id") == m.get("team1_id") or
                                     st.get("blue_team_id") == m.get("team1_id"))
                    lead = t1 if ((diff > 0) == blue_is_team1) else t2
                    gold_str = f" · {lead} +{abs(diff) / 1000:.1f}k gold"
                elif bg_gold or rg_gold:
                    gold_str = " · Gold even"
            details = f"{g_str}{gold_str}"

        items.append(TickerItem(
            kind="live",
            badge="● LIVE",
            badge_bg=C.COLOR_LIVE,
            badge_fg="white",
            headline=headline,
            details=details,
            tab_target="live",
            tooltip=f"Click to jump to live match: {t1} vs {t2}",
            match_id=m.get("match_id"),
        ))

    # 2. 24/7 Continuous Twitch/YouTube Stream
    stream_events = app.state.get("stream") or []
    if stream_events and app.state.get("stream_online", True) is not False:
        cur = now_airing(stream_events, now=now)
        if cur:
            title = event_title(cur)
            sub = event_subtitle(cur)
            items.append(TickerItem(
                kind="stream",
                badge="📺 24/7 STREAM",
                badge_bg=C.COLOR_CYAN,
                badge_fg=C.COLOR_BG,
                headline=f"24/7 Marathon: {title}",
                details=f"{sub} · Airing now on Twitch & YouTube" if sub else "Airing now on Twitch & YouTube",
                tab_target="stream",
                tooltip=f"Click to jump to 24/7 Continuous Stream schedule",
            ))

    # 3. Upcoming matches scheduled for today or next 36h
    schedule = app.state.get("schedule") or []
    unstarted = [m for m in schedule if m.get("state") == "unstarted"]
    unstarted.sort(key=lambda x: x.get("start_time_utc") or x.get("start_utc") or "")

    followed_teams = {t.get("code") for t in app.settings.followed_teams() if t.get("code")}
    prioritized = []
    regular = []
    for m in unstarted:
        t1 = m.get("team1_code") or ""
        t2 = m.get("team2_code") or ""
        if t1 in followed_teams or t2 in followed_teams:
            prioritized.append(m)
        else:
            regular.append(m)

    upcoming_candidates = (prioritized + regular)[:3]
    for m in upcoming_candidates:
        t1 = m.get("team1_code") or m.get("team1_name") or "TBD"
        t2 = m.get("team2_code") or m.get("team2_name") or "TBD"
        league = m.get("league_name", "")
        start_iso = m.get("start_time_utc") or m.get("start_utc") or ""
        time_rel = format_relative_time(start_iso, now)
        items.append(TickerItem(
            kind="upcoming",
            badge="⏰ UPCOMING",
            badge_bg=C.COLOR_GOLD,
            badge_fg=C.COLOR_BG,
            headline=f"{league} · {t1} vs {t2}",
            details=f"Starts {time_rel}",
            tab_target="schedule",
            schedule_filter_range="upcoming",
            tooltip=f"Click to view schedule for {t1} vs {t2}",
            match_id=m.get("match_id"),
        ))

    # 4. Recent completed results from today
    completed = [m for m in schedule if m.get("state") == "completed"]
    completed.sort(key=lambda x: x.get("start_time_utc") or x.get("start_utc") or "", reverse=True)
    for m in completed[:2]:
        t1 = m.get("team1_code") or "TBD"
        t2 = m.get("team2_code") or "TBD"
        league = m.get("league_name", "")
        hidden = cards.scores_hidden(app, m)
        if hidden:
            headline = f"{league} · {t1} vs {t2}"
            details = "Result hidden (Spoiler mode)"
        else:
            s1, s2 = cards.score_text(app, m)
            headline = f"{league} · {t1} {s1} - {s2} {t2}"
            details = "FINAL"
        items.append(TickerItem(
            kind="result",
            badge="✓ FINAL",
            badge_bg=C.COLOR_SURFACE_HOVER,
            badge_fg=C.COLOR_TEXT_PRIMARY,
            headline=headline,
            details=details,
            tab_target="schedule",
            schedule_filter_range="results",
            tooltip=f"Click to view results for {t1} vs {t2}",
            match_id=m.get("match_id"),
        ))

    # 5. Fallback item when nothing is live or upcoming
    if not items:
        items.append(TickerItem(
            kind="info",
            badge="⚡ RIFTWATCH",
            badge_bg=C.COLOR_SURFACE_HOVER,
            badge_fg=C.COLOR_GOLD,
            headline="RiftWatch Live Ticker",
            details="All pro leagues monitored · Check Schedule for upcoming fixtures",
            tab_target="schedule",
            tooltip="Click to view full match schedule",
        ))

    return items


class TickerBar(tk.Frame):
    """
    Compact broadcast ticker bar docked below navigation tabs.
    Rotates live scores, countdowns, and continuous stream highlights.
    """

    def __init__(self, parent: tk.Misc, app: Any):
        super().__init__(parent, bg=C.COLOR_BG_DARK, highlightbackground=C.COLOR_BORDER,
                         highlightthickness=1, height=px(28))
        self.app = app
        self.items: List[TickerItem] = []
        self.index = 0
        self._timer: Optional[str] = None
        self._is_hovered = False

        self._build_ui()
        self.refresh_data()

    def _build_ui(self) -> None:
        self.pack_propagate(False)

        # Left badge pill
        self.pill = tk.Frame(self, bg=C.COLOR_SURFACE, cursor="hand2")
        self.pill.pack(side="left", padx=(px(8), px(6)), pady=px(3))
        self.l_badge = tk.Label(self.pill, text="⚡ TICKER", font=font(8, True),
                                bg=C.COLOR_SURFACE, fg=C.COLOR_GOLD, cursor="hand2",
                                padx=px(6), pady=px(1))
        self.l_badge.pack()

        # Vertical separator
        self.sep = tk.Frame(self, bg=C.COLOR_BORDER, width=1, height=px(14))
        self.sep.pack(side="left", padx=px(4))

        # Middle clickable headline & details
        self.content_frame = tk.Frame(self, bg=C.COLOR_BG_DARK, cursor="hand2")
        self.content_frame.pack(side="left", fill="both", expand=True, padx=px(6))

        self.l_headline = tk.Label(self.content_frame, text="", font=font(9, True),
                                   bg=C.COLOR_BG_DARK, fg=C.COLOR_TEXT_PRIMARY, cursor="hand2")
        self.l_headline.pack(side="left")

        self.l_dot = tk.Label(self.content_frame, text="  ·  ", font=font(8),
                              bg=C.COLOR_BG_DARK, fg=C.COLOR_TEXT_DIM, cursor="hand2")
        self.l_dot.pack(side="left")

        self.l_details = tk.Label(self.content_frame, text="", font=font(9, False),
                                  bg=C.COLOR_BG_DARK, fg=C.COLOR_TEXT_MUTED, cursor="hand2")
        self.l_details.pack(side="left")

        # Right controls
        right = tk.Frame(self, bg=C.COLOR_BG_DARK)
        right.pack(side="right", padx=px(8))

        self.l_counter = tk.Label(right, text="", font=font(8), bg=C.COLOR_BG_DARK, fg=C.COLOR_TEXT_DIM)
        self.l_counter.pack(side="left", padx=px(6))

        self.btn_prev = button(right, "◀", self.prev_item, size=7, bold=False, padx=4, pady=1,
                               bg=C.COLOR_BG_DARK, fg=C.COLOR_TEXT_MUTED, hover_bg=C.COLOR_SURFACE,
                               tooltip="Previous ticker update")
        self.btn_prev.pack(side="left", padx=1)

        self.btn_next = button(right, "▶", self.next_item, size=7, bold=False, padx=4, pady=1,
                               bg=C.COLOR_BG_DARK, fg=C.COLOR_TEXT_MUTED, hover_bg=C.COLOR_SURFACE,
                               tooltip="Next ticker update")
        self.btn_next.pack(side="left", padx=1)

        self.btn_hide = button(right, "✕", self.hide_bar, size=7, bold=False, padx=5, pady=1,
                               bg=C.COLOR_BG_DARK, fg=C.COLOR_TEXT_DIM, hover_bg=C.COLOR_LIVE,
                               tooltip="Hide ticker bar (re-enable in Settings)")
        self.btn_hide.pack(side="left", padx=(px(6), 0))

        # Bind hover and click events
        clickable = (self, self.pill, self.l_badge, self.content_frame, self.l_headline, self.l_dot, self.l_details)
        for w in clickable:
            w.bind("<Button-1>", lambda e: self._on_click())
            w.bind("<Enter>", lambda e: self._on_enter())
            w.bind("<Leave>", lambda e: self._on_leave())

    def _on_enter(self) -> None:
        self._is_hovered = True
        self.l_headline.configure(fg=C.COLOR_GOLD)
        self._cancel_timer()

    def _on_leave(self) -> None:
        self._is_hovered = False
        self.l_headline.configure(fg=C.COLOR_TEXT_PRIMARY)
        self._schedule_rotation(5500)

    def _on_click(self) -> None:
        if not self.items:
            return
        item = self.items[self.index % len(self.items)]
        if item.schedule_filter_range:
            self.app.settings.set("schedule_filter_range", item.schedule_filter_range)
        self.app.show_tab(item.tab_target)

    def _cancel_timer(self) -> None:
        if self._timer:
            try:
                self.after_cancel(self._timer)
            except Exception:
                pass
            self._timer = None

    def _schedule_rotation(self, delay_ms: int = 5500) -> None:
        self._cancel_timer()
        self._timer = self.after(delay_ms, self._auto_rotate)

    def _auto_rotate(self) -> None:
        self._timer = None
        if not self._is_hovered and len(self.items) > 1:
            self.index = (self.index + 1) % len(self.items)
            self._display_current()
        self._schedule_rotation(5500)

    def prev_item(self) -> None:
        if not self.items:
            return
        self.index = (self.index - 1) % len(self.items)
        self._display_current()
        if not self._is_hovered:
            self._schedule_rotation(6000)

    def next_item(self, auto: bool = False) -> None:
        if not self.items:
            return
        self.index = (self.index + 1) % len(self.items)
        self._display_current()
        if not self._is_hovered and not auto:
            self._schedule_rotation(6000)

    def refresh_data(self) -> None:
        """Gather fresh ticker data from state and update display smoothly."""
        old_count = len(self.items)
        self.items = gather_ticker_items(self.app)
        if not self.items:
            self.index = 0
        elif self.index >= len(self.items):
            self.index = 0
        self._display_current()
        if old_count <= 1 and len(self.items) > 1 and not self._timer:
            self._schedule_rotation(5500)

    def _display_current(self) -> None:
        if not self.items:
            return
        item = self.items[self.index % len(self.items)]
        self.pill.configure(bg=item.badge_bg)
        self.l_badge.configure(text=item.badge, bg=item.badge_bg, fg=item.badge_fg)
        self.l_headline.configure(text=item.headline)
        self.l_details.configure(text=item.details)

        if len(self.items) > 1:
            self.l_counter.configure(text=f"{self.index + 1}/{len(self.items)}")
            self.btn_prev.pack(side="left", padx=1)
            self.btn_next.pack(side="left", padx=1)
        else:
            self.l_counter.configure(text="")
            self.btn_prev.pack_forget()
            self.btn_next.pack_forget()

    def hide_bar(self) -> None:
        self._cancel_timer()
        self.app.set_ticker_visible(False)
