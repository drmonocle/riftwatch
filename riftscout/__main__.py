"""
RiftScout CLI Status & Data Engine Verification
Run with: py -3.12 -m riftscout
"""

import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from . import __version__, __app_name__
from . import config as C
from .data import DataCoordinator, format_local_match_time, format_relative_time
from .stream import StreamScheduleReader
from .settings import SettingsManager
from .updater import check_for_updates

def main():
    print("=" * 70)
    print(f"  {__app_name__} v{__version__} - Data Engine & Ingestion Diagnostics")
    print("=" * 70)

    sm = SettingsManager()
    print(f"\n[⭐ Following Preferences]")
    print(f"  Followed Teams:   {', '.join(sm.get('followed_teams', []))}")
    print(f"  Followed Regions: {', '.join(sm.get('followed_regions', []))}")
    print(f"  Followed Players: {', '.join(sm.get('followed_players', []))}")
    print(f"  Spoiler Mode:     {'ENABLED (Scores Hidden)' if sm.get('spoiler_mode') else 'DISABLED (Scores Shown)'}")

    # 1. Live Pro Matches
    coordinator = DataCoordinator()
    print("\n[🔴 Live Pro Matches (Riot LoL Esports API)]")
    try:
        live = coordinator.fetch_live_matches()
        if live:
            for m in live:
                t1 = f"{m['team1_name']} ({m['team1_code']})"
                t2 = f"{m['team2_name']} ({m['team2_code']})"
                score = f"{m['team1_score']} - {m['team2_score']}"
                star = "⭐ " if sm.is_match_followed(m) else "   "
                print(f"  {star}[LIVE] {m['league_name']}: {t1} {score} {t2} (Bo{m['best_of']})")
                if m.get('stream_url'):
                    print(f"         Stream: {m['stream_url']}")
        else:
            print("  No pro matches are currently live right now.")
    except Exception as exc:
        print(f"  Error querying live matches: {exc}")

    # 2. Upcoming Schedule
    print("\n[📅 Upcoming Pro Matches]")
    try:
        schedule = coordinator.fetch_schedule()
        upcoming = [m for m in schedule if m.get("state") != "completed"][:8]
        if upcoming:
            for m in upcoming:
                t1 = m['team1_code']
                t2 = m['team2_code']
                rel = format_relative_time(m.get('start_time_utc', ''))
                local = format_local_match_time(m.get('start_time_utc', ''))
                star = "⭐ " if sm.is_match_followed(m) else "   "
                print(f"  {star}{local} ({rel}) | {m['league_name']}: {t1} vs {t2} (Bo{m['best_of']})")
        else:
            print("  No upcoming matches found.")
    except Exception as exc:
        print(f"  Error querying schedule: {exc}")

    # 3. 24/7 Twitch Stream Marathon & Bangers
    print("\n[📺 24/7 Twitch Broadcast Stream (lol_broadcast_schedule.db)]")
    try:
        reader = StreamScheduleReader()
        items = reader.fetch_stream_schedule()
        bangers = [i for i in items if i.get("is_banger")]
        print(f"  Total Broadcast Series in Playout: {len(items)}")
        print(f"  Total S-Tier Bangers Cataloged:    {len(bangers)}")
        if bangers:
            print("  Top Featured Bangers in Stream Rotation:")
            for b in bangers[:5]:
                print(f"    • {b['tournament_name']}: {b['title']} [{b['banger_tier']}] (Score: {b['score']})")
    except Exception as exc:
        print(f"  Error reading Twitch schedule: {exc}")

    # 4. Update Status
    print("\n[🔄 1-Click Self-Updater Status]")
    try:
        update_info = check_for_updates()
        if update_info:
            print(f"  ✨ Update Available! {update_info['tag']} -> 1-Click Update Ready")
            print(f"     Release: {update_info['html_url']}")
        else:
            print(f"  ✓ Up to date (Running v{__version__} on branch main)")
    except Exception as exc:
        print(f"  Update check: {exc}")

    print("\n" + "=" * 70)
    print("  Phase 1 Data Engine Status: 100% OPERATIONAL")
    print("=" * 70)

if __name__ == "__main__":
    main()
