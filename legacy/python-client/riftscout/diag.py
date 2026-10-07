"""
RiftScout command-line diagnostics: `py -3.12 -m riftscout --diag`
Checks every data source and reports what actually worked.
"""

import sys

from . import __app_name__, __version__
from . import catalog as catalog_mod
from .data import DataCoordinator, format_local_match_time, format_relative_time
from .settings import SettingsManager
from .stream import StreamScheduleReader, event_subtitle, event_title, next_banger, now_airing, upcoming
from .updater import check_for_updates
from .watchlist import Watchlist


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    results = {}
    print("=" * 70)
    print(f"  {__app_name__} v{__version__} - data source diagnostics")
    print("=" * 70)

    sm = SettingsManager()
    teams = ", ".join(t.get("name") or t["code"] for t in sm.followed_teams()) or "(none)"
    print("\n[Following]")
    print(f"  Teams:   {teams}")
    print(f"  Players: {', '.join(sm.get('followed_players', [])) or '(none)'}")
    print(f"  Leagues: {', '.join(sm.get('followed_leagues', []))}")

    print("\n[Team directory]")
    cat = catalog_mod.load_cached()
    if cat.empty or catalog_mod.catalog_age_sec() > 86400:
        fresh = catalog_mod.refresh()
        cat = fresh or cat
    results["catalog"] = not cat.empty
    print(f"  {len(cat.teams)} teams, {len(cat.players)} roster entries, {len(cat.leagues)} leagues"
          if not cat.empty else "  FAILED to load")
    wl = Watchlist(sm, cat)

    coord = DataCoordinator()
    print("\n[Live matches]")
    live = coord.fetch_live_matches()
    results["live"] = live is not None
    if live is None:
        print("  FAILED (Riot live API unreachable)")
    elif not live:
        print("  Nothing live right now")
    for m in live or []:
        star = "★" if wl.is_strong(m) else " "
        score = "vs" if sm.get("spoiler_mode", False) else f"{m['team1_score']}-{m['team2_score']}"
        print(f"  {star} {m['league_name']}: {m['team1_code']} {score} {m['team2_code']} (Bo{m['best_of']})")

    print("\n[Upcoming pro matches]")
    sched = coord.fetch_schedule()
    results["schedule"] = sched is not None
    if sched is None:
        print("  FAILED (Riot schedule API unreachable)")
    for m in [m for m in sched or [] if m["state"] == "unstarted"][:8]:
        star = "★" if wl.is_strong(m) else ("·" if wl.is_followed(m) else " ")
        print(f"  {star} {format_local_match_time(m['start_time_utc'])} ({format_relative_time(m['start_time_utc'])})"
              f"  {m['league_name']}: {m['team1_code']} vs {m['team2_code']}")

    print("\n[24/7 Twitch rebroadcast]")
    events = StreamScheduleReader().fetch()
    results["stream"] = events is not None
    if events is None:
        print("  FAILED (stream schedule unreachable)")
    else:
        cur = now_airing(events)
        print(f"  On now:  {event_title(cur)}  ({event_subtitle(cur)})" if cur else "  On now:  off air / unknown")
        for e in upcoming(events, limit=3):
            print(f"  Next:    {format_local_match_time(e['start_utc'])}  {event_title(e)}  ({event_subtitle(e)})")
        b = next_banger(events)
        if b:
            print(f"  Banger:  {event_title(b)} {format_relative_time(b['start_utc'])}")

    print("\n[Updates]")
    info = check_for_updates()
    print(f"  {info['tag']} available: {info['html_url']}" if info else "  No newer release published")

    print("\n" + "=" * 70)
    ok = [k for k, v in results.items() if v]
    bad = [k for k, v in results.items() if not v]
    print(f"  Sources OK: {', '.join(ok) or 'none'}" + (f"   FAILED: {', '.join(bad)}" if bad else ""))
    print("=" * 70)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
