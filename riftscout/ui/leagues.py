"""
RiftWatch League Filter Dialog.
Allows users to multi-select which LoL Esports leagues (LCK, LPL, LEC, LCS,
Worlds, MSI, Demacia Cup, etc.) appear on the desktop Schedule tab.
Features quick presets, search filtering, and regional categorization.
"""

import sys
import tkinter as tk
from typing import Any, Callable, Dict, List, Optional, Set

from .. import config as C
from ..catalog import Catalog
from .widgets import ScrollFrame, apply_dark_titlebar, button, clear, font, label, pill, px, set_button_colors


REGION_META = {
    "INTERNATIONAL": {"name": "International Tournaments", "badge": "🌐", "priority": 1},
    "KOREA": {"name": "Korea (LCK)", "badge": "🇰🇷", "priority": 2},
    "CHINA": {"name": "China (LPL)", "badge": "🇨🇳", "priority": 3},
    "EUROPE": {"name": "Europe & EMEA (LEC)", "badge": "🇪🇺", "priority": 4},
    "NORTH AMERICA": {"name": "North America (LCS)", "badge": "🇺🇸", "priority": 5},
    "APAC": {"name": "Asia-Pacific (LCP / PCS / VCS)", "badge": "🌏", "priority": 6},
    "BRAZIL": {"name": "Brazil & Latin America (CBLOL)", "badge": "🇧🇷", "priority": 7},
    "OTHER": {"name": "Regional & Secondary Leagues", "badge": "⚔️", "priority": 8},
}

KNOWN_LEAGUE_INFO = {
    "worlds": ("Worlds", "Premier World Championship", "INTERNATIONAL"),
    "msi": ("MSI", "Mid-Season Invitational", "INTERNATIONAL"),
    "first_stand": ("First Stand", "International Season Opener", "INTERNATIONAL"),
    "demacia_cup": ("Demacia Cup (DCGI)", "Global Invitational", "INTERNATIONAL"),
    "asian_games": ("Asian Games", "Olympic Council Regional Games", "INTERNATIONAL"),
    "americas_cup": ("Americas Cup", "Inter-regional Championship", "INTERNATIONAL"),
    "wsci": ("WSCI", "World Streamer Championship", "INTERNATIONAL"),
    "ewc_lol": ("Esports World Cup", "Global Club Championship", "INTERNATIONAL"),
    "lck": ("LCK", "League of Legends Champions Korea (Tier 1)", "KOREA"),
    "lck_challengers_league": ("LCK Challengers", "LCK Academy & Challengers League", "KOREA"),
    "kespa_cup": ("KeSPA Cup", "Korean Off-Season Cup", "KOREA"),
    "lpl": ("LPL", "League of Legends Pro League (Tier 1)", "CHINA"),
    "ldl": ("LDL", "LoL Development League", "CHINA"),
    "lec": ("LEC", "LoL EMEA Championship (Tier 1)", "EUROPE"),
    "emea_masters": ("EMEA Masters", "European Regional Champions Tournament", "EUROPE"),
    "lfl": ("LFL", "La Ligue Française", "EUROPE"),
    "primeleague": ("Prime League", "DACH Regional League", "EUROPE"),
    "turkiye-sampiyonluk-ligi": ("TCL", "Turkish Championship League", "EUROPE"),
    "nlc": ("NLC", "Nordic League Championship", "EUROPE"),
    "lcs": ("LCS", "League of Legends Championship Series (Tier 1)", "NORTH AMERICA"),
    "lta_n": ("LTA North", "League of The Americas - North Conference", "NORTH AMERICA"),
    "nacl": ("NACL", "North American Challengers League", "NORTH AMERICA"),
    "lcp": ("LCP", "League of Legends Championship Pacific (Tier 1)", "APAC"),
    "pcs": ("PCS", "Pacific Championship Series", "APAC"),
    "vcs": ("VCS", "Vietnam Championship Series", "APAC"),
    "ljl-japan": ("LJL", "League of Legends Japan League", "APAC"),
    "cblol-brazil": ("CBLOL", "Campeonato Brasileiro de LoL (Tier 1)", "BRAZIL"),
    "lta_s": ("LTA South", "League of The Americas - South Conference", "BRAZIL"),
    "cblol_promotion": ("CBLOL Promotion", "Promotion & Relegation", "BRAZIL"),
}


class LeagueFilterDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, app: Any, on_apply: Optional[Callable[[List[str]], None]] = None):
        super().__init__(parent)
        self.withdraw()  # Off-screen until fully styled to eliminate white flash
        self.app = app
        self.settings = app.settings
        self.on_apply = on_apply

        self.title("LoL Esports Leagues · Filter Schedule")
        self.configure(bg=C.COLOR_BG)
        self.minsize(px(760), px(580))
        self.geometry(f"{px(820)}x{px(660)}")

        # Load currently selected leagues from settings (empty set means All leagues)
        saved = self.settings.get("schedule_selected_leagues", [])
        legacy = self.settings.get("schedule_filter_league", "")
        if not saved and legacy:
            saved = [legacy]
        self.selected_leagues: Set[str] = set(saved)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_cards())

        self._all_leagues: List[Dict[str, Any]] = self._gather_all_leagues()
        self._league_widgets: List[tuple] = []  # (slug, frame, match_texts)

        self._build_ui()
        self._center_window(parent)
        apply_dark_titlebar(self)
        self.update_idletasks()
        self.deiconify()
        self.transient(parent)
        self.grab_set()

    def _gather_all_leagues(self) -> List[Dict[str, Any]]:
        """Collect catalog leagues, db leagues, and predefined top leagues."""
        seen: Dict[str, Dict[str, Any]] = {}
        # 1. Start with known leagues definition
        for slug, (name, desc, region) in KNOWN_LEAGUE_INFO.items():
            seen[slug] = {
                "slug": slug,
                "name": name,
                "desc": desc,
                "region": region,
                "league_id": C.KNOWN_LEAGUE_IDS.get(slug, ""),
            }

        # 2. Merge from catalog
        cat = self.app.state.get("catalog")
        if cat and cat.leagues:
            for l in cat.leagues:
                s = l.get("slug")
                if not s:
                    continue
                if s not in seen:
                    r = (l.get("region") or "OTHER").upper()
                    if r not in REGION_META:
                        r = "OTHER"
                    seen[s] = {
                        "slug": s,
                        "name": l.get("name") or s.upper(),
                        "desc": f"{r.title()} Pro League",
                        "region": r,
                        "league_id": l.get("league_id", ""),
                    }
                elif not seen[s].get("league_id") and l.get("league_id"):
                    seen[s]["league_id"] = l["league_id"]

        # Count matches currently in app schedule state
        counts: Dict[str, int] = {}
        for m in self.app.state.get("schedule", []):
            sl = m.get("league_slug")
            if sl:
                counts[sl] = counts.get(sl, 0) + 1

        res = list(seen.values())
        for l in res:
            l["match_count"] = counts.get(l["slug"], 0)

        # Sort by region priority, then by name
        def sort_key(x):
            r_meta = REGION_META.get(x["region"], REGION_META["OTHER"])
            return (r_meta["priority"], x["name"].lower())

        res.sort(key=sort_key)
        return res

    def _center_window(self, parent: tk.Misc) -> None:
        try:
            self.update_idletasks()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px_coord = parent.winfo_rootx() + (pw - self.winfo_width()) // 2
            py_coord = parent.winfo_rooty() + (ph - self.winfo_height()) // 2
            self.geometry(f"+{max(0, px_coord)}+{max(0, py_coord)}")
        except Exception:
            pass

    def _build_ui(self) -> None:
        # Header banner
        header = tk.Frame(self, bg=C.COLOR_BG_DARK)
        header.pack(fill="x")
        tk.Frame(self, bg=C.COLOR_GOLD, height=1).pack(fill="x")

        htxt = tk.Frame(header, bg=C.COLOR_BG_DARK)
        htxt.pack(fill="x", padx=px(24), pady=px(14))
        label(htxt, "SELECT LOL ESPORTS LEAGUES", 15, True, fg=C.COLOR_GOLD).pack(anchor="w")
        label(htxt, "Choose which pro leagues appear on your Schedule tab. "
                    "Select specific leagues, choose quick presets, or show all.", 9,
              fg=C.COLOR_TEXT_MUTED).pack(anchor="w", pady=(px(3), 0))

        # Action toolbar for presets
        tb = tk.Frame(self, bg=C.COLOR_SURFACE)
        tb.pack(fill="x", padx=px(20), pady=(px(10), px(4)))
        label(tb, "Quick Presets:", 9, True, fg=C.COLOR_TEXT_DIM).pack(side="left", padx=(px(12), px(8)), pady=px(6))
        button(tb, "★ All Leagues", self._preset_all, size=9,
               bg=C.COLOR_GOLD, fg=C.COLOR_BG, hover_bg=C.COLOR_GOLD_HOVER).pack(side="left", padx=px(3))
        button(tb, "⭐ Big 4 (LCK/LPL/LEC/LCS)", self._preset_big4, size=9,
               bg=C.COLOR_SURFACE_HOVER, fg=C.COLOR_TEXT_PRIMARY).pack(side="left", padx=px(3))
        button(tb, "🌐 International", self._preset_intl, size=9,
               bg=C.COLOR_SURFACE_HOVER, fg=C.COLOR_TEXT_PRIMARY).pack(side="left", padx=px(3))
        button(tb, "★ Followed in Watchlist", self._preset_followed, size=9,
               bg=C.COLOR_SURFACE_HOVER, fg=C.COLOR_CYAN).pack(side="left", padx=px(3))
        button(tb, "Clear All", self._preset_clear, size=9,
               bg=C.COLOR_SURFACE_HOVER, fg=C.COLOR_TEXT_MUTED).pack(side="left", padx=px(3))

        # Search bar
        search_row = tk.Frame(self, bg=C.COLOR_BG)
        search_row.pack(fill="x", padx=px(20), pady=(px(6), px(2)))
        label(search_row, "Search Leagues:", 9, True, fg=C.COLOR_TEXT_MUTED).pack(side="left", padx=(0, px(8)))
        entry_wrap = tk.Frame(search_row, bg=C.COLOR_BORDER)
        entry_wrap.pack(side="left", fill="x", expand=True)
        self.entry = tk.Entry(entry_wrap, textvariable=self.search_var, font=font(9), bg=C.COLOR_SURFACE,
                              fg=C.COLOR_TEXT_PRIMARY, insertbackground=C.COLOR_GOLD, relief="flat")
        self.entry.pack(fill="x", padx=1, pady=1, ipady=px(3), ipadx=px(6))

        # Scrollable list of leagues
        self.scroll = ScrollFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=px(20), pady=px(6))
        self.body = self.scroll.body

        # Footer
        tk.Frame(self, bg=C.COLOR_BORDER, height=1).pack(fill="x")
        footer = tk.Frame(self, bg=C.COLOR_BG_DARK)
        footer.pack(fill="x", padx=px(20), pady=px(10))

        self.l_summary = label(footer, "", 9, fg=C.COLOR_TEXT_MUTED)
        self.l_summary.pack(side="left", padx=px(6))

        button(footer, "✓ Apply to Schedule", self._save_and_apply, size=10, bold=True,
               bg=C.COLOR_GOLD, fg=C.COLOR_BG, hover_bg=C.COLOR_GOLD_HOVER, padx=14, pady=6).pack(side="right", padx=px(6))
        button(footer, "Cancel", self.destroy, size=9, bold=False,
               bg=C.COLOR_BG_DARK, fg=C.COLOR_TEXT_MUTED, hover_bg=C.COLOR_SURFACE, padx=10, pady=6).pack(side="right", padx=px(4))

        self._render_league_cards()
        self._update_summary()

    def _render_league_cards(self) -> None:
        clear(self.body)
        self._league_widgets.clear()

        current_region = None
        for l in self._all_leagues:
            r = l["region"]
            if r != current_region:
                current_region = r
                rmeta = REGION_META.get(r, REGION_META["OTHER"])
                sec = tk.Frame(self.body, bg=C.COLOR_BG)
                sec.pack(fill="x", padx=px(6), pady=(px(12), px(4)))
                label(sec, f"{rmeta['badge']}  {rmeta['name'].upper()}", 9, True, fg=C.COLOR_GOLD).pack(side="left")

            card = self._create_league_card(l)
            match_text = f"{l['slug']} {l['name']} {l['desc']} {l['region']}".lower()
            self._league_widgets.append((l["slug"], card, match_text))

    def _create_league_card(self, l: Dict[str, Any]) -> tk.Frame:
        slug = l["slug"]
        is_sel = (not self.selected_leagues) or (slug in self.selected_leagues)
        rmeta = REGION_META.get(l["region"], REGION_META["OTHER"])

        row = tk.Frame(self.body, bg=C.COLOR_SURFACE, highlightthickness=1,
                       highlightbackground=C.COLOR_GOLD if is_sel else C.COLOR_BORDER, cursor="hand2")
        row.pack(fill="x", padx=px(6), pady=px(2))

        # Checkbox indicator
        cb_txt = " [✓] " if is_sel else " [   ] "
        cb_fg = C.COLOR_GOLD if is_sel else C.COLOR_TEXT_DIM
        cb_lbl = label(row, cb_txt, 10, True, fg=cb_fg, bg=C.COLOR_SURFACE, cursor="hand2")
        cb_lbl.pack(side="left", padx=(px(10), px(4)), pady=px(6))

        # Flag badge
        flag_lbl = label(row, rmeta["badge"], 12, fg=C.COLOR_TEXT_PRIMARY, bg=C.COLOR_SURFACE, cursor="hand2")
        flag_lbl.pack(side="left", padx=(0, px(8)))

        # Name and description
        info_col = tk.Frame(row, bg=C.COLOR_SURFACE, cursor="hand2")
        info_col.pack(side="left", fill="x", expand=True, pady=px(4))
        name_lbl = label(info_col, l["name"], 10, True,
                         fg=C.COLOR_GOLD if is_sel else C.COLOR_TEXT_PRIMARY, bg=C.COLOR_SURFACE, cursor="hand2")
        name_lbl.pack(anchor="w")
        desc_lbl = label(info_col, l["desc"], 8, fg=C.COLOR_TEXT_MUTED, bg=C.COLOR_SURFACE, cursor="hand2")
        desc_lbl.pack(anchor="w")

        # Match count badge if in schedule
        right_box = tk.Frame(row, bg=C.COLOR_SURFACE, cursor="hand2")
        right_box.pack(side="right", padx=px(12))
        if l["match_count"] > 0:
            pill(right_box, f"{l['match_count']} scheduled", C.COLOR_SURFACE_HOVER, fg=C.COLOR_CYAN).pack(side="right")

        # Toggle handler
        def _toggle(e=None, sl=slug, r_frame=row, c_lbl=cb_lbl, n_lbl=name_lbl):
            if not self.selected_leagues:
                # If currently All, clicking deselects this one (selects all others)
                self.selected_leagues = {x["slug"] for x in self._all_leagues if x["slug"] != sl}
            elif sl in self.selected_leagues:
                self.selected_leagues.remove(sl)
            else:
                self.selected_leagues.add(sl)
            self._refresh_card_visuals(sl, r_frame, c_lbl, n_lbl)
            self._update_summary()

        for w in (row, cb_lbl, flag_lbl, info_col, name_lbl, desc_lbl, right_box):
            w.bind("<Button-1>", _toggle)
            w.bind("<Enter>", lambda e, rf=row: rf.configure(bg=C.COLOR_SURFACE_HOVER))
            w.bind("<Leave>", lambda e, rf=row: rf.configure(bg=C.COLOR_SURFACE))

        row._cb_lbl = cb_lbl
        row._name_lbl = name_lbl
        return row

    def _refresh_card_visuals(self, slug: str, row: tk.Frame, cb_lbl: tk.Label, name_lbl: tk.Label) -> None:
        is_sel = (not self.selected_leagues) or (slug in self.selected_leagues)
        row.configure(highlightbackground=C.COLOR_GOLD if is_sel else C.COLOR_BORDER)
        cb_lbl.configure(text=" [✓] " if is_sel else " [   ] ", fg=C.COLOR_GOLD if is_sel else C.COLOR_TEXT_DIM)
        name_lbl.configure(fg=C.COLOR_GOLD if is_sel else C.COLOR_TEXT_PRIMARY)

    def _update_all_visuals(self) -> None:
        for slug, card, _ in self._league_widgets:
            if hasattr(card, "_cb_lbl") and hasattr(card, "_name_lbl"):
                self._refresh_card_visuals(slug, card, card._cb_lbl, card._name_lbl)
        self._update_summary()

    def _update_summary(self) -> None:
        total = len(self._all_leagues)
        sel_count = len(self.selected_leagues)
        if not self.selected_leagues or sel_count == total:
            self.l_summary.configure(text=f"Showing all {total} leagues on Schedule.")
        else:
            names = [l["name"] for l in self._all_leagues if l["slug"] in self.selected_leagues]
            if len(names) <= 3:
                txt = f"Showing {sel_count} leagues ({', '.join(names)})."
            else:
                txt = f"Showing {sel_count} of {total} leagues selected."
            self.l_summary.configure(text=txt)

    def _filter_cards(self) -> None:
        q = self.search_var.get().strip().lower()
        for _, card, match_text in self._league_widgets:
            if not q or q in match_text:
                card.pack(fill="x", padx=px(6), pady=px(2))
            else:
                card.pack_forget()

    # ---- presets
    def _preset_all(self) -> None:
        self.selected_leagues.clear()  # Empty means all
        self._update_all_visuals()

    def _preset_big4(self) -> None:
        self.selected_leagues = {"lck", "lpl", "lec", "lcs"}
        self._update_all_visuals()

    def _preset_intl(self) -> None:
        self.selected_leagues = {"worlds", "msi", "first_stand", "demacia_cup", "asian_games"}
        self._update_all_visuals()

    def _preset_followed(self) -> None:
        followed = set(self.settings.get("followed_leagues", []))
        if not followed:
            followed = set(C.DEFAULT_FOLLOWED_LEAGUES)
        self.selected_leagues = followed
        self._update_all_visuals()

    def _preset_clear(self) -> None:
        self.selected_leagues = set()
        # Explicit empty set vs all: we mark with a sentinel or keep empty as none
        # Here we explicitly select nothing except 1 placeholder so user can pick
        self._update_all_visuals()

    def _save_and_apply(self) -> None:
        # Save selection list to settings
        # If all leagues are selected or empty set, we can store empty list (meaning All)
        total_count = len(self._all_leagues)
        if len(self.selected_leagues) == total_count or not self.selected_leagues:
            val = []
        else:
            val = list(self.selected_leagues)
        self.settings.set("schedule_selected_leagues", val)
        self.settings.set("schedule_filter_league", "")  # Clear single-league filter
        self.app.bump("prefs")
        if self.on_apply:
            self.on_apply(val)
        self.destroy()
