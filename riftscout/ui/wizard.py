"""
RiftWatch Onboarding Wizard.
Provides a streamlined first-launch experience for new users to follow
their favorite regions, international tournaments, pro teams, and star players.
Can also be re-launched anytime from the Settings tab.
"""

import tkinter as tk
from typing import Dict, List, Set

from .. import config as C
from . import cards
from .widgets import ScrollFrame, apply_dark_titlebar, button, font, label, pill, px


class OnboardingWizard(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.withdraw()
        self.app = app
        self.settings = app.settings

        self.title("Welcome to RiftWatch - Setup Wizard")
        self.configure(bg=C.COLOR_BG)
        self.minsize(px(780), px(580))
        self.geometry(f"{px(860)}x{px(660)}")

        # Track local selections before saving
        self.selected_regions: Set[str] = set(self.settings.followed_regions())
        if not self.selected_regions:
            self.selected_regions = set(C.DEFAULT_FOLLOWED_REGIONS)

        self.selected_teams: Dict[str, str] = {
            t["code"]: t.get("name", t["code"]) for t in self.settings.followed_teams()
        }
        self.selected_players: Set[str] = set(self.settings.get("followed_players", []))
        self.selected_leagues: Set[str] = set(self.settings.get("followed_leagues", []))
        if not self.selected_leagues:
            self.selected_leagues = set(C.DEFAULT_FOLLOWED_LEAGUES)

        self._build_ui()
        self._center_window(parent)
        apply_dark_titlebar(self)
        self.update_idletasks()
        self.deiconify()
        self.transient(parent)
        self.grab_set()

    def _center_window(self, parent):
        try:
            self.update_idletasks()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px_coord = parent.winfo_rootx() + (pw - self.winfo_width()) // 2
            py_coord = parent.winfo_rooty() + (ph - self.winfo_height()) // 2
            self.geometry(f"+{max(0, px_coord)}+{max(0, py_coord)}")
        except Exception:
            pass

    def _build_ui(self):
        # Header banner
        header = tk.Frame(self, bg=C.COLOR_BG_DARK)
        header.pack(fill="x")
        tk.Frame(self, bg=C.COLOR_GOLD, height=1).pack(fill="x")

        htxt = tk.Frame(header, bg=C.COLOR_BG_DARK)
        htxt.pack(fill="x", padx=px(24), pady=px(14))
        label(htxt, "WELCOME TO RIFTWATCH", 16, True, fg=C.COLOR_GOLD).pack(anchor="w")
        label(htxt, "Select the regions, pro teams, and star players you want to track on your desktop. "
                    "You can customize these anytime in the Watchlist tab.", 10,
              fg=C.COLOR_TEXT_MUTED, wraplength=px(800), justify="left").pack(anchor="w", pady=(px(4), 0))

        # Action toolbar for presets
        tb = tk.Frame(self, bg=C.COLOR_SURFACE)
        tb.pack(fill="x", padx=px(20), pady=(px(10), px(4)))
        label(tb, "Quick Presets:", 9, True, fg=C.COLOR_TEXT_DIM).pack(side="left", padx=(px(12), px(8)), pady=px(6))
        button(tb, "★ Recommended All-Stars", self._preset_recommended, size=9,
               bg=C.COLOR_GOLD, fg=C.COLOR_BG, hover_bg=C.COLOR_GOLD_HOVER).pack(side="left", padx=px(4))
        button(tb, "Select All Major Regions", self._select_all_regions, size=9,
               bg=C.COLOR_SURFACE_HOVER, fg=C.COLOR_TEXT_PRIMARY).pack(side="left", padx=px(4))
        button(tb, "Clear All", self._clear_all, size=9,
               bg=C.COLOR_SURFACE_HOVER, fg=C.COLOR_TEXT_MUTED).pack(side="left", padx=px(4))

        # Main scrollable body
        self.scroll = ScrollFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=px(20), pady=px(6))
        self.body = self.scroll.body

        # Footer
        tk.Frame(self, bg=C.COLOR_BORDER, height=1).pack(fill="x")
        footer = tk.Frame(self, bg=C.COLOR_BG_DARK)
        footer.pack(fill="x", padx=px(20), pady=px(12))

        button(footer, "✓ Save & Launch RiftWatch", self._save_and_close, size=11, bold=True,
               bg=C.COLOR_GOLD, fg=C.COLOR_BG, hover_bg=C.COLOR_GOLD_HOVER, padx=18, pady=8).pack(side="right", padx=px(6))
        button(footer, "Skip for Now", self._skip, size=9, bold=False,
               bg=C.COLOR_BG_DARK, fg=C.COLOR_TEXT_MUTED, hover_bg=C.COLOR_SURFACE).pack(side="right", padx=px(8))

        self._render_sections()

    def _render_sections(self):
        for w in self.body.winfo_children():
            w.destroy()

        self._render_regions_section()
        self._render_teams_section()
        self._render_players_section()

    # ---- 1. REGIONS & TOURNAMENTS
    def _render_regions_section(self):
        sec = tk.Frame(self.body, bg=C.COLOR_BG)
        sec.pack(fill="x", pady=(px(10), px(4)))
        label(sec, "1. MAJOR REGIONS & TOURNAMENTS", 11, True, fg=C.COLOR_GOLD).pack(anchor="w")
        label(sec, "Follow entire competitive ecosystems to get alerts and matches in your feed.", 9,
              fg=C.COLOR_TEXT_MUTED).pack(anchor="w")

        grid = tk.Frame(self.body, bg=C.COLOR_BG)
        grid.pack(fill="x", pady=px(6))

        for idx, r in enumerate(C.MAJOR_REGIONS):
            code = r["code"]
            is_on = code in self.selected_regions
            card = tk.Frame(grid, bg=C.COLOR_SURFACE,
                            highlightbackground=C.COLOR_GOLD if is_on else C.COLOR_BORDER,
                            highlightthickness=1)
            card.pack(fill="x", pady=px(2))

            top = tk.Frame(card, bg=C.COLOR_SURFACE)
            top.pack(fill="x", padx=px(12), pady=px(6))

            label(top, r.get("badge", "🌐"), 14).pack(side="left", padx=(0, px(8)))
            label(top, r["name"], 11, True, fg=C.COLOR_GOLD if is_on else C.COLOR_TEXT_PRIMARY).pack(side="left")
            leagues_str = " · ".join(r.get("leagues", []))
            label(top, f"  ({leagues_str})", 9, fg=C.COLOR_TEXT_MUTED).pack(side="left")

            btn = button(top, "★ Following" if is_on else "☆ Follow",
                         lambda c=code: self._toggle_region(c), size=8,
                         bg=C.COLOR_GOLD if is_on else C.COLOR_SURFACE_HOVER,
                         fg=C.COLOR_BG if is_on else C.COLOR_TEXT_PRIMARY,
                         hover_bg=C.COLOR_GOLD_HOVER if is_on else C.COLOR_BORDER)
            btn.pack(side="right")

    def _toggle_region(self, code: str):
        if code in self.selected_regions:
            self.selected_regions.remove(code)
        else:
            self.selected_regions.add(code)
        self.scroll.keep_scroll(self._render_sections)

    # ---- 2. POPULAR PRO TEAMS
    def _render_teams_section(self):
        sec = tk.Frame(self.body, bg=C.COLOR_BG)
        sec.pack(fill="x", pady=(px(16), px(4)))
        label(sec, "2. POPULAR PRO TEAMS", 11, True, fg=C.COLOR_GOLD).pack(anchor="w")
        label(sec, "Star your favorite teams across LCK, LPL, LEC, and LCS for priority live alerts.", 9,
              fg=C.COLOR_TEXT_MUTED).pack(anchor="w")

        grid = tk.Frame(self.body, bg=C.COLOR_BG)
        grid.pack(fill="x", pady=px(6))

        cat = self.app.state.get("catalog")
        # 2-column layout for teams
        col1 = tk.Frame(grid, bg=C.COLOR_BG)
        col1.pack(side="left", fill="both", expand=True, padx=(0, px(4)))
        col2 = tk.Frame(grid, bg=C.COLOR_BG)
        col2.pack(side="left", fill="both", expand=True, padx=(px(4), 0))

        for idx, t in enumerate(C.POPULAR_TEAMS):
            col = col1 if idx % 2 == 0 else col2
            code = t["code"]
            is_on = code in self.selected_teams
            card = tk.Frame(col, bg=C.COLOR_SURFACE,
                            highlightbackground=C.COLOR_GOLD if is_on else C.COLOR_BORDER,
                            highlightthickness=1)
            card.pack(fill="x", pady=px(2))

            row = tk.Frame(card, bg=C.COLOR_SURFACE)
            row.pack(fill="x", padx=px(10), pady=px(6))

            img_url = cat.team_image(code, t["name"]) if cat else ""
            cards.logo(row, self.app, img_url, 24, code).pack(side="left", padx=(0, px(8)))

            txt = tk.Frame(row, bg=C.COLOR_SURFACE)
            txt.pack(side="left", fill="x", expand=True)
            label(txt, t["name"], 10, True, fg=C.COLOR_GOLD if is_on else C.COLOR_TEXT_PRIMARY).pack(anchor="w")
            label(txt, f"{code} · {t.get('league', '')}", 8, fg=C.COLOR_TEXT_MUTED).pack(anchor="w")

            btn = button(row, "★" if is_on else "☆",
                         lambda c=code, n=t["name"]: self._toggle_team(c, n), size=10,
                         bg=C.COLOR_GOLD if is_on else C.COLOR_SURFACE_HOVER,
                         fg=C.COLOR_BG if is_on else C.COLOR_TEXT_PRIMARY,
                         hover_bg=C.COLOR_GOLD_HOVER if is_on else C.COLOR_BORDER, padx=8)
            btn.pack(side="right")

    def _toggle_team(self, code: str, name: str):
        if code in self.selected_teams:
            del self.selected_teams[code]
        else:
            self.selected_teams[code] = name
        self.scroll.keep_scroll(self._render_sections)

    # ---- 3. STAR PLAYERS
    def _render_players_section(self):
        sec = tk.Frame(self.body, bg=C.COLOR_BG)
        sec.pack(fill="x", pady=(px(16), px(4)))
        label(sec, "3. STAR PLAYERS", 11, True, fg=C.COLOR_GOLD).pack(anchor="w")
        label(sec, "Track individual players so any match they play is highlighted with their name.", 9,
              fg=C.COLOR_TEXT_MUTED).pack(anchor="w")

        grid = tk.Frame(self.body, bg=C.COLOR_BG)
        grid.pack(fill="x", pady=px(6))

        cat = self.app.state.get("catalog")
        col1 = tk.Frame(grid, bg=C.COLOR_BG)
        col1.pack(side="left", fill="both", expand=True, padx=(0, px(4)))
        col2 = tk.Frame(grid, bg=C.COLOR_BG)
        col2.pack(side="left", fill="both", expand=True, padx=(px(4), 0))

        for idx, p in enumerate(C.POPULAR_PLAYERS):
            col = col1 if idx % 2 == 0 else col2
            pname = p["name"]
            is_on = pname in self.selected_players
            card = tk.Frame(col, bg=C.COLOR_SURFACE,
                            highlightbackground=C.COLOR_GOLD if is_on else C.COLOR_BORDER,
                            highlightthickness=1)
            card.pack(fill="x", pady=px(2))

            row = tk.Frame(card, bg=C.COLOR_SURFACE)
            row.pack(fill="x", padx=px(10), pady=px(6))

            pill(row, p.get("role", "Pro").upper(), C.COLOR_CYAN_DIM, fg="white", size=7).pack(side="left", padx=(0, px(6)))

            img_url = cat.team_image(p.get("team", "")) if cat else ""
            cards.logo(row, self.app, img_url, 18, p.get("team", "")).pack(side="left", padx=(0, px(6)))

            txt = tk.Frame(row, bg=C.COLOR_SURFACE)
            txt.pack(side="left", fill="x", expand=True)
            label(txt, pname, 10, True, fg=C.COLOR_GOLD if is_on else C.COLOR_TEXT_PRIMARY).pack(anchor="w")
            label(txt, p.get("team", ""), 8, fg=C.COLOR_TEXT_MUTED).pack(anchor="w")

            btn = button(row, "★" if is_on else "☆",
                         lambda n=pname: self._toggle_player(n), size=10,
                         bg=C.COLOR_GOLD if is_on else C.COLOR_SURFACE_HOVER,
                         fg=C.COLOR_BG if is_on else C.COLOR_TEXT_PRIMARY,
                         hover_bg=C.COLOR_GOLD_HOVER if is_on else C.COLOR_BORDER, padx=8)
            btn.pack(side="right")

    def _toggle_player(self, name: str):
        if name in self.selected_players:
            self.selected_players.remove(name)
        else:
            self.selected_players.add(name)
        self.scroll.keep_scroll(self._render_sections)

    # ---- PRESETS
    def _preset_recommended(self):
        self.selected_regions = {r["code"] for r in C.MAJOR_REGIONS if r["code"] in (
            "INTERNATIONAL", "KOREA", "EUROPE", "NORTH AMERICA", "CHINA"
        )}
        self.selected_teams = {t["code"]: t["name"] for t in C.POPULAR_TEAMS}
        self.selected_players = {p["name"] for p in C.POPULAR_PLAYERS}
        self._render_sections()

    def _select_all_regions(self):
        self.selected_regions = {r["code"] for r in C.MAJOR_REGIONS}
        self._render_sections()

    def _clear_all(self):
        self.selected_regions.clear()
        self.selected_teams.clear()
        self.selected_players.clear()
        self._render_sections()

    # ---- COMMIT
    def _save_and_close(self):
        # Save regions
        self.settings.set("followed_regions", sorted(self.selected_regions))
        # Ensure default tournament leagues are saved
        leagues = set(self.selected_leagues)
        for r_code in self.selected_regions:
            for r in C.MAJOR_REGIONS:
                if r["code"] == r_code:
                    for l in r.get("leagues", []):
                        slug = l.lower().replace(" ", "_")
                        leagues.add(slug)
        self.settings.set("followed_leagues", sorted(leagues))

        # Save teams
        team_list = [{"code": code, "name": name} for code, name in self.selected_teams.items()]
        self.settings.set("followed_teams", team_list)

        # Save players
        self.settings.set("followed_players", sorted(self.selected_players))

        # Mark onboarding complete
        self.settings.set("onboarding_completed", True)

        self.app.bump("prefs")
        self.destroy()

    def _skip(self):
        self.settings.set("onboarding_completed", True)
        self.destroy()
