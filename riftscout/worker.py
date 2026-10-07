"""
RiftScout Background Worker
All network and disk I/O happens here, off the Tk main thread. Results are
posted to a queue that the UI drains with root.after(), so the window never
blocks on a slow API.
"""

import logging
import queue
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from . import catalog as catalog_mod
from . import config as C
from . import updater
from .data import DataCoordinator, current_game
from .settings import SettingsManager
from .stream import StreamScheduleReader

log = logging.getLogger(__name__)

MAX_LIVESTATS_GAMES = 4


class Worker(threading.Thread):
    def __init__(self, settings: SettingsManager, out: "queue.Queue[tuple]",
                 coordinator: Optional[DataCoordinator] = None,
                 stream_reader: Optional[StreamScheduleReader] = None,
                 db_path=None):
        super().__init__(name="riftscout-worker", daemon=True)
        self.settings = settings
        self.out = out
        self.db_path = db_path
        self.coord = coordinator or DataCoordinator(db_path=db_path)
        self.stream = stream_reader or StreamScheduleReader(db_path=db_path)
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._pending: set = set()      # requested by the UI, guarded by _lock
        self._forced_now: set = set()   # being processed in the current pass
        self._lock = threading.Lock()
        self.next_due: Dict[str, float] = {k: 0.0 for k in ("catalog", "schedule", "live", "stream", "update")}
        self.live: List[Dict[str, Any]] = []
        self.last_livestats = 0.0

    # ------------------------------------------------------------------ control
    def stop(self) -> None:
        self._stop.set()
        self._wake.set()

    def request(self, *jobs: str) -> None:
        """Ask for an immediate refresh of the named jobs ('all' = everything)."""
        with self._lock:
            self._pending.update(self.next_due if "all" in jobs else jobs)
        self._wake.set()

    def _post(self, kind: str, payload: Any) -> None:
        self.out.put((kind, payload))

    def _status(self, source: str, ok: bool, detail: str = "") -> None:
        self._post("status", {"source": source, "ok": ok, "detail": detail, "at": time.time()})

    # ------------------------------------------------------------------ jobs
    def _job_catalog(self, first: bool) -> None:
        if first:
            cached = catalog_mod.load_cached(self.db_path)
            if not cached.empty:
                self._post("catalog", cached)
        age = catalog_mod.catalog_age_sec(self.db_path)
        if age < C.INTERVAL_CATALOG_SEC and "catalog" not in self._forced_now:
            self._status("catalog", True, "cached")
            return
        cat = catalog_mod.refresh(self.db_path)
        if cat:
            self._post("catalog", cat)
            self._status("catalog", True)
        else:
            self._status("catalog", False, "Riot teams API unreachable")

    def _job_schedule(self) -> None:
        matches = self.coord.fetch_schedule()
        if matches is None:
            self._post("schedule", self.coord.cached_schedule())
            self._status("schedule", False, "Riot schedule API unreachable (showing cache)")
        else:
            self._post("schedule", self.coord.cached_schedule())
            self._status("schedule", True)

    def _job_live(self) -> None:
        live = self.coord.fetch_live_matches()
        if live is None:
            self._status("live", False, "Riot live API unreachable")
            return
        self.live = live
        self._post("live", live)
        self._status("live", True)

    def _job_livestats(self) -> None:
        stats: Dict[str, Any] = {}
        for m in self.live[:MAX_LIVESTATS_GAMES]:
            g = current_game(m)
            if not g:
                continue
            st = self.coord.fetch_live_stats(g["id"], [m.get("team1_code", ""), m.get("team2_code", "")])
            if st:
                st["game_number"] = g.get("number")
                st["blue_team_id"] = g.get("blue_team_id")
                stats[m["match_id"]] = st
        self._post("livestats", stats)

    def _job_stream(self) -> None:
        events = self.stream.fetch()
        if events is None:
            self._post("stream", self.stream.cached())
            self._status("stream", False, "Stream schedule unreachable (showing cache)")
        else:
            self._post("stream", events)
            self._status("stream", True)

    def _job_update(self) -> None:
        if not self.settings.get("auto_update_check", True) and "update" not in self._forced_now:
            return
        info = updater.check_for_updates()
        self._post("update", info)

    # ------------------------------------------------------------------ loop
    def _run_job(self, name: str, fn: Callable, *args) -> None:
        try:
            fn(*args)
        except Exception as exc:  # never let one job kill the thread
            log.exception("Worker job %s failed", name)
            self._status(name, False, str(exc)[:120])

    def run(self) -> None:
        # Serve cached data first so the UI paints instantly, then go live.
        try:
            self._post("schedule", self.coord.cached_schedule())
            self._post("stream", self.stream.cached())
        except Exception:
            log.exception("Could not read cache")
        self._run_job("catalog", self._job_catalog, True)
        self.next_due["catalog"] = time.time() + C.INTERVAL_CATALOG_SEC

        while not self._stop.is_set():
            self._wake.clear()
            now = time.time()
            with self._lock:
                self._forced_now, self._pending = self._pending, set()
            forced = self._forced_now

            if "live" in forced or now >= self.next_due["live"]:
                self._run_job("live", self._job_live)
                self.next_due["live"] = now + (C.INTERVAL_LIVE_POLL_SEC if self.live else 120)
            if "schedule" in forced or now >= self.next_due["schedule"]:
                self._run_job("schedule", self._job_schedule)
                self.next_due["schedule"] = now + (C.INTERVAL_LIVE_POLL_SEC if self.live else C.INTERVAL_IDLE_POLL_SEC)
            if self.live and ("live" in forced or now - self.last_livestats >= C.INTERVAL_LIVESTATS_SEC):
                self._run_job("livestats", self._job_livestats)
                self.last_livestats = now
            elif not self.live and self.last_livestats:
                self._post("livestats", {})
                self.last_livestats = 0.0
            if "stream" in forced or now >= self.next_due["stream"]:
                self._run_job("stream", self._job_stream)
                self.next_due["stream"] = now + C.INTERVAL_STREAM_POLL_SEC
            if "catalog" in forced or now >= self.next_due["catalog"]:
                self._run_job("catalog", self._job_catalog, False)
                self.next_due["catalog"] = now + C.INTERVAL_CATALOG_SEC
            if "update" in forced or now >= self.next_due["update"]:
                self._run_job("update", self._job_update)
                self.next_due["update"] = now + C.INTERVAL_UPDATE_CHECK_SEC

            self._forced_now = set()
            if forced:
                self._post("refresh_done", time.time())
            self._wake.wait(timeout=2.0)
