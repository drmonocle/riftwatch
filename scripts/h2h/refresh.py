"""Rebuild the live all-time head-to-head table for RiftWatch.

Starts from the bundled src/all_time_h2h.json (every game up to BASE_CUTOFF, all tournaments)
and adds every completed series since then from the lolesports API, across every league.
Writes {"cutoff", "pairs", ...} to the output path; the app downloads it and counts schedule
results from `cutoff` on itself, so nothing is counted twice.

    python scripts/h2h/refresh.py out/h2h.json

Run every few hours by .github/workflows/h2h-data.yml. Standard library only.
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_PATH = os.path.join(ROOT, "src", "all_time_h2h.json")
# Per-pair series history from the catalog (h2h-refresh/series_from_catalog.py), same cutoff.
BASE_SERIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "base_series.json")
RECENT_N = 10
INTL_LEAGUE = re.compile(r"world|msi|mid-season|first stand", re.I)
BASE_CUTOFF = "2026-09-26T00:00:00Z"  # keep in sync with BUNDLED_H2H_CUTOFF in src/helpers.ts
# keep in sync with CODE_ALIASES in src/helpers.ts
CODE_ALIASES = {"TLAW": "TL", "MKOI": "MDK", "KRX": "DRX", "DNS": "KDF", "DNF": "KDF"}

API = "https://esports-api.lolesports.com/persisted/gw"
# Public key used by the lolesports.com web client (same one the app uses).
HEADERS = {"x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z", "User-Agent": "RiftWatch-H2H/1.0"}
# A match still marked unstarted this long after its start time is treated as postponed, not pending.
STALE_PENDING = timedelta(hours=48)


def get(path, **params):
    url = f"{API}/{path}?" + urllib.parse.urlencode({"hl": "en-US", **params})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as r:
                return json.load(r)["data"]
        except Exception as e:  # network blip or 5xx: retry with backoff
            if attempt == 4:
                raise RuntimeError(f"{url}: {e}")
            time.sleep(2 * (attempt + 1))


def norm(code):
    c = (code or "").strip().upper()
    return CODE_ALIASES.get(c, c)


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def league_events(league_id, since):
    """Every match event for a league from `since` up to the newest page."""
    events = []
    page = get("getSchedule", leagueId=league_id)["schedule"]
    while True:
        evs = [e for e in page.get("events", []) if e.get("type") == "match" and e.get("startTime")]
        events += [e for e in evs if parse_time(e["startTime"]) >= since]
        older = page.get("pages", {}).get("older")
        if not older or not evs or min(parse_time(e["startTime"]) for e in evs) < since:
            return events
        page = get("getSchedule", leagueId=league_id, pageToken=older)["schedule"]


def main(out_path):
    now = datetime.now(timezone.utc)
    base_cutoff = parse_time(BASE_CUTOFF)
    base = json.load(open(BASE_PATH, encoding="utf-8"))

    events = {}
    for league in get("getLeagues")["leagues"]:
        for e in league_events(league["id"], base_cutoff):
            events[e["match"]["id"]] = e

    # Stop just before the earliest match that has started but isn't finished, so a series that
    # is in progress right now is left to the app instead of being cut in half.
    pending = [parse_time(e["startTime"]) for e in events.values()
               if e.get("state") != "completed" and now - STALE_PENDING <= parse_time(e["startTime"]) <= now]
    cutoff = min([now] + pending)

    pairs = defaultdict(lambda: [0, 0])
    for k, (aw, bw) in base.items():
        a, b = k.split("__")
        a, b = norm(a), norm(b)
        if a > b:
            a, b, aw, bw = b, a, bw, aw
        pairs[(a, b)][0] += aw
        pairs[(a, b)][1] += bw

    # Series history for the H2H details view: catalog history plus the new series.
    series = {}
    if os.path.exists(BASE_SERIES_PATH):
        series = json.load(open(BASE_SERIES_PATH, encoding="utf-8"))
    new_series = []

    added = 0
    for e in events.values():
        start = parse_time(e["startTime"])
        if e.get("state") != "completed" or not (base_cutoff <= start < cutoff):
            continue
        t1, t2 = e["match"]["teams"]
        a, b = norm(t1.get("code")), norm(t2.get("code"))
        aw = (t1.get("result") or {}).get("gameWins") or 0
        bw = (t2.get("result") or {}).get("gameWins") or 0
        if not a or not b or a == b or "TBD" in (a, b) or aw + bw == 0:
            continue
        if a > b:
            a, b, aw, bw = b, a, bw, aw
        pairs[(a, b)][0] += aw
        pairs[(a, b)][1] += bw
        added += 1
        league = (e.get("league") or {}).get("name") or ""
        new_series.append((f"{a}__{b}", start.strftime("%Y-%m-%d"), league, aw, bw))

    for key, date, league, aw, bw in sorted(new_series, key=lambda s: s[1], reverse=True):
        entry = series.setdefault(key, {"intl": [0, 0], "recent": []})
        if INTL_LEAGUE.search(league):
            entry["intl"][0] += aw
            entry["intl"][1] += bw
        entry["recent"].insert(0, [date, league, aw, bw])
    for entry in series.values():
        entry["recent"].sort(key=lambda s: s[0], reverse=True)
        del entry["recent"][RECENT_N:]

    out = {
        "version": 2,
        "generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cutoff": cutoff.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "baseCutoff": BASE_CUTOFF,
        "seriesAdded": added,
        "pairs": {f"{a}__{b}": v for (a, b), v in sorted(pairs.items())},
    }
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(os.path.join(out_dir, "series"), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    # Shard the series history by the first character of the pair key (A-Z, else "0"), so the
    # app fetches one small file when a meter is tapped instead of the whole history.
    shards = {}
    for key, entry in series.items():
        shards.setdefault(shard_of(key), {})[key] = entry
    for name, data in shards.items():
        with open(os.path.join(out_dir, "series", f"{name}.json"), "w", encoding="utf-8", newline="") as f:
            json.dump(dict(sorted(data.items())), f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(events)} events since {BASE_CUTOFF}; added {added} completed series; "
          f"{len(out['pairs'])} pairs; cutoff {out['cutoff']}; {len(series)} pairs with history in {len(shards)} shards")


def shard_of(key):
    c = key[:1].upper()
    return c if "A" <= c <= "Z" else "0"


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "h2h.json")
