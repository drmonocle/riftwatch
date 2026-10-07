import React, { useState, useEffect, useRef, useCallback } from "react";
import { AppSettings, Match, StreamEvent, CatalogData, AppUpdateInfo } from "./types";
import {
  loadSettings,
  saveSettings,
  fetchLiveMatches,
  fetchSchedule,
  fetchStreamSchedule,
  loadCachedCatalog,
  loadBundledCatalog,
  fetchLiveCatalog,
  checkForAppUpdate,
  EMPTY_CATALOG,
} from "./api";
import { APP_VERSION } from "./version";
import { reconcileLiveAndSchedule } from "./helpers";
import { Header } from "./components/Header";
import { Navigation, TabKey } from "./components/Navigation";
import { TickerBar } from "./components/TickerBar";
import { LiveView } from "./components/views/LiveView";
import { ScheduleView } from "./components/views/ScheduleView";
import { StreamView } from "./components/views/StreamView";
import { WatchlistView } from "./components/views/WatchlistView";
import { NewsView } from "./components/views/NewsView";
import { SettingsView } from "./components/views/SettingsView";

// The floating HUD is the same app loaded with ?mode=detached in its own window.
const IS_HUD_WINDOW = window.location.search.includes("mode=detached");

// How often each data source is re-fetched (ms)
const LIVE_POLL_MS = 60_000;
const LIVE_POLL_ACTIVE_MS = 30_000; // faster while a match is in progress
const SCHEDULE_POLL_MS = 5 * 60_000;
const STREAM_POLL_MS = 15 * 60_000;

export default function App() {
  const [settings, setSettings] = useState<AppSettings>(() => loadSettings());
  const settingsRef = useRef(settings);
  useEffect(() => {
    settingsRef.current = settings;
  }, [settings]);

  // The HUD window never shows the catalog, so skip loading it there.
  const [catalog, setCatalog] = useState<CatalogData>(() =>
    IS_HUD_WINDOW ? EMPTY_CATALOG : loadCachedCatalog() ?? EMPTY_CATALOG,
  );

  // Determine initial tab: on first launch, open directly to Watchlist so users configure their teams
  const [activeTab, setActiveTab] = useState<TabKey>(() => {
    try {
      const hasLaunched = localStorage.getItem("riftwatch_has_launched");
      if (!hasLaunched) {
        localStorage.setItem("riftwatch_has_launched", "true");
        return "watchlist";
      }
    } catch {}
    return loadSettings().defaultTab || "live";
  });

  const [liveMatches, setLiveMatches] = useState<Match[]>([]);
  const [schedule, setSchedule] = useState<Match[]>([]);
  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastSync, setLastSync] = useState<number | null>(null);
  const [syncFailed, setSyncFailed] = useState(false);
  const [updateInfo, setUpdateInfo] = useState<AppUpdateInfo | null>(null);
  const [isCheckingUpdate, setIsCheckingUpdate] = useState(false);

  // Sync settings across windows (main window and detached HUD window)
  useEffect(() => {
    const handleSync = () => {
      const fresh = loadSettings();
      settingsRef.current = fresh;
      setSettings(fresh);
    };
    window.addEventListener("riftwatch_settings_updated", handleSync);
    window.addEventListener("storage", handleSync);
    return () => {
      window.removeEventListener("riftwatch_settings_updated", handleSync);
      window.removeEventListener("storage", handleSync);
    };
  }, []);

  const handleUpdateSettings = useCallback((partial: Partial<AppSettings>) => {
    const updated = { ...settingsRef.current, ...partial };
    settingsRef.current = updated;
    setSettings(updated);
    saveSettings(updated);
  }, []);

  // Listen for tray menu events (main window only, with proper cleanup)
  useEffect(() => {
    if (IS_HUD_WINDOW) return;
    let cancelled = false;
    const unlisteners: Array<() => void> = [];

    import("@tauri-apps/api/event")
      .then(async ({ listen }) => {
        const offTab = await listen<string>("navigate_tab", (event) => {
          if (event.payload) setActiveTab(event.payload as TabKey);
        });
        const offHud = await listen("toggle_hud", () => {
          const next = settingsRef.current.tickerMode === "detached" ? "docked" : "detached";
          handleUpdateSettings({ tickerMode: next });
        });
        if (cancelled) {
          offTab();
          offHud();
        } else {
          unlisteners.push(offTab, offHud);
        }
      })
      .catch(() => {});

    return () => {
      cancelled = true;
      unlisteners.forEach((off) => off());
    };
  }, [handleUpdateSettings]);

  // ---------------------------------------------------------------
  // Data polling
  // ---------------------------------------------------------------
  const inFlight = useRef(false);
  const lastSchedule = useRef(0);
  const lastStream = useRef(0);
  const liveCount = useRef(0);

  const refreshData = useCallback(async (force = false) => {
    if (inFlight.current) return;
    inFlight.current = true;
    setIsRefreshing(true);
    const now = Date.now();
    const wantSchedule = force || now - lastSchedule.current >= SCHEDULE_POLL_MS - 1000;
    const wantStream = force || now - lastStream.current >= STREAM_POLL_MS - 1000;

    try {
      // allSettled: one source failing must never wipe the data we already have
      const [live, sched, stream] = await Promise.allSettled([
        fetchLiveMatches(),
        wantSchedule ? fetchSchedule() : Promise.resolve(null),
        wantStream ? fetchStreamSchedule() : Promise.resolve(null),
      ]);

      let nextLive = liveMatches;
      let nextSched = schedule;

      if (live.status === "fulfilled") {
        nextLive = live.value.matches;
      }
      if (sched.status === "fulfilled" && sched.value) {
        nextSched = sched.value;
        lastSchedule.current = now;
      }

      // Correlate live broadcasts with scheduled matches to surface live tournament slates
      const { finalLive, finalSchedule } = reconcileLiveAndSchedule(nextLive, nextSched);
      setLiveMatches(finalLive);
      setSchedule(finalSchedule);
      liveCount.current = finalLive.filter((m) => m.state === "inProgress").length;

      if (stream.status === "fulfilled" && stream.value) {
        setStreamEvents(stream.value);
        lastStream.current = now;
      }

      const anyFailed = [live, sched, stream].some((r) => r.status === "rejected");
      setSyncFailed(anyFailed);
      if (!anyFailed || live.status === "fulfilled") setLastSync(Date.now());
    } finally {
      inFlight.current = false;
      setIsRefreshing(false);
    }
  }, []);

  // Desktop keyboard shortcuts (F5, Ctrl+R, Ctrl+1..6, Ctrl+S, Ctrl+D)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept when user is typing in an input
      if (["INPUT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName)) {
        return;
      }

      if (e.key === "F5" || (e.ctrlKey && e.key.toLowerCase() === "r")) {
        e.preventDefault();
        refreshData(true);
      } else if (e.ctrlKey && e.key === "1") {
        e.preventDefault();
        setActiveTab("live");
      } else if (e.ctrlKey && e.key === "2") {
        e.preventDefault();
        setActiveTab("schedule");
      } else if (e.ctrlKey && e.key === "3") {
        e.preventDefault();
        setActiveTab("stream");
      } else if (e.ctrlKey && e.key === "4") {
        e.preventDefault();
        setActiveTab("watchlist");
      } else if (e.ctrlKey && e.key === "5") {
        e.preventDefault();
        setActiveTab("news");
      } else if (e.ctrlKey && e.key === "6") {
        e.preventDefault();
        setActiveTab("settings");
      } else if (e.ctrlKey && e.key.toLowerCase() === "s") {
        e.preventDefault();
        handleUpdateSettings({ spoilerMode: !settingsRef.current.spoilerMode });
      } else if (e.ctrlKey && e.key.toLowerCase() === "d") {
        e.preventDefault();
        handleUpdateSettings({
          tickerMode: settingsRef.current.tickerMode === "detached" ? "docked" : "detached",
        });
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleUpdateSettings, refreshData]);

  // Software update check
  const handleCheckForUpdate = useCallback(async () => {
    setIsCheckingUpdate(true);
    try {
      const info = await checkForAppUpdate(APP_VERSION);
      setUpdateInfo(info);
      if (info?.hasUpdate && settings.notifyKickoff) {
        import("@tauri-apps/api/core").then(({ invoke }) => {
          invoke("send_notification", {
            title: "⚡ RiftWatch Update Available",
            body: `Version v${info.latestVersion} is now available! Click to update.`,
          }).catch(() => {});
        });
      }
    } finally {
      setIsCheckingUpdate(false);
    }
  }, [settings.notifyKickoff]);

  // Check for updates on startup (main window only, delayed 2.5s)
  useEffect(() => {
    if (IS_HUD_WINDOW) return;
    const timer = setTimeout(() => {
      handleCheckForUpdate();
    }, 2500);
    return () => clearTimeout(timer);
  }, [handleCheckForUpdate]);

  // The HUD window only needs to poll while it is actually the active ticker.
  const pollingActive = !IS_HUD_WINDOW || settings.tickerMode === "detached";

  useEffect(() => {
    if (!pollingActive) return;
    let cancelled = false;
    let timer: number | undefined;

    const loop = async () => {
      if (!document.hidden) await refreshData();
      if (cancelled) return;
      timer = window.setTimeout(loop, liveCount.current > 0 ? LIVE_POLL_ACTIVE_MS : LIVE_POLL_MS);
    };
    const onVisible = () => {
      if (!document.hidden) refreshData();
    };

    loop();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [pollingActive, refreshData]);

  // ---------------------------------------------------------------
  // Native window sync (main window only; the HUD window just follows)
  // ---------------------------------------------------------------
  useEffect(() => {
    if (IS_HUD_WINDOW) return;
    import("@tauri-apps/api/core")
      .then(({ invoke }) => {
        if (settings.tickerMode === "detached") {
          invoke("show_ticker").catch(() => {});
        } else {
          invoke("hide_ticker").catch(() => {});
        }
      })
      .catch(() => {});
  }, [settings.tickerMode]);

  useEffect(() => {
    if (IS_HUD_WINDOW) return;
    import("@tauri-apps/api/core")
      .then(({ invoke }) => {
        invoke("set_ticker_topmost", { topmost: settings.tickerTopmost }).catch(() => {});
      })
      .catch(() => {});
  }, [settings.tickerTopmost]);

  // Tell the native side whether closing the window should hide to tray or quit
  useEffect(() => {
    if (IS_HUD_WINDOW) return;
    import("@tauri-apps/api/core")
      .then(({ invoke }) => {
        invoke("set_close_to_tray", { enabled: settings.minimizeToTrayOnClose }).catch(() => {});
      })
      .catch(() => {});
  }, [settings.minimizeToTrayOnClose]);

  // Synchronize Windows autostart on sign-in
  useEffect(() => {
    if (IS_HUD_WINDOW) return;
    import("@tauri-apps/api/core")
      .then(({ invoke }) => {
        invoke("set_autostart", { enabled: settings.startWithWindows }).catch(() => {});
      })
      .catch(() => {});
  }, [settings.startWithWindows]);

  // ---------------------------------------------------------------
  // Desktop Notifications (Kickoffs & S-Tier Bangers)
  // ---------------------------------------------------------------
  const notifiedKickoffs = useRef(new Set<string>());
  const notifiedBangers = useRef(new Set<string>());

  useEffect(() => {
    if (IS_HUD_WINDOW) return;
    if (!settings.notifyKickoff || liveMatches.length === 0) return;

    const followed = new Set(settings.followedTeams.map((t) => t.toUpperCase()));
    for (const m of liveMatches) {
      if (m.state === "inProgress" && !notifiedKickoffs.current.has(m.matchId)) {
        const isFollowed =
          followed.has(m.team1Code.toUpperCase()) || followed.has(m.team2Code.toUpperCase());
        if (isFollowed) {
          notifiedKickoffs.current.add(m.matchId);
          import("@tauri-apps/api/core")
            .then(({ invoke }) => {
              invoke("send_notification", {
                title: `🔴 MATCH LIVE: ${m.team1Code} vs ${m.team2Code}`,
                body: `${m.leagueName} match is now live! (Bo${m.bestOf})`,
              }).catch(() => {});
            })
            .catch(() => {});
        }
      }
    }
  }, [liveMatches, settings.notifyKickoff, settings.followedTeams]);

  useEffect(() => {
    if (IS_HUD_WINDOW) return;
    if (!settings.notifyStream || streamEvents.length === 0) return;

    const now = Date.now();
    for (const ev of streamEvents) {
      if (ev.isBanger && ev.utcIso) {
        const start = new Date(ev.utcIso).getTime();
        // Airing now (started within the last 45 minutes)
        if (now >= start && now - start < 45 * 60 * 1000) {
          const key = `banger-${ev.id}`;
          if (!notifiedBangers.current.has(key)) {
            notifiedBangers.current.add(key);
            const matchup =
              ev.team1 && ev.team2 ? `${ev.team1} vs ${ev.team2}` : ev.name || "Legendary Match";
            import("@tauri-apps/api/core")
              .then(({ invoke }) => {
                invoke("send_notification", {
                  title: `🔥 S-TIER BANGER AIRING NOW`,
                  body: `${matchup} (${ev.event} ${ev.season}) is playing on 24/7 stream!`,
                }).catch(() => {});
              })
              .catch(() => {});
          }
        }
      }
    }
  }, [streamEvents, settings.notifyStream]);

  // ---------------------------------------------------------------
  // Catalog (teams / players / leagues)
  // ---------------------------------------------------------------
  // First run: load the snapshot bundled with the app (kept out of the startup bundle).
  useEffect(() => {
    if (IS_HUD_WINDOW || catalog.teams.length > 0) return;
    loadBundledCatalog()
      .then((bundled) => setCatalog((prev) => (prev.teams.length > 0 ? prev : bundled)))
      .catch((e) => console.warn("Failed to load bundled catalog:", e));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Refresh from Riot in the background if the saved copy is older than 24 hours
  useEffect(() => {
    if (IS_HUD_WINDOW) return;
    const cached = loadCachedCatalog();
    const age = Date.now() - (cached?.updatedAt || 0);
    if (age > 24 * 60 * 60 * 1000) {
      fetchLiveCatalog(cached ?? undefined)
        .then((updated) => {
          if (updated) setCatalog(updated);
        })
        .catch(() => {});
    }
  }, []);

  const handleRefreshCatalog = async () => {
    setIsRefreshing(true);
    try {
      const updated = await fetchLiveCatalog(catalog);
      if (updated) setCatalog(updated);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleOpenUrl = (url: string) => {
    import("@tauri-apps/api/core")
      .then(({ invoke }) => {
        invoke("open_external_url", { url }).catch(() => {
          // Native side refused (not an http/https link) or isn't available (browser dev mode)
          if (/^https?:\/\//i.test(url)) window.open(url, "_blank");
        });
      })
      .catch(() => {
        if (/^https?:\/\//i.test(url)) window.open(url, "_blank");
      });
  };

  // If running in detached HUD mode (query parameter ?mode=detached)
  if (IS_HUD_WINDOW) {
    return (
      <div className="w-screen h-screen bg-[#080c14] overflow-hidden m-0 p-0 select-none">
        <TickerBar
          settings={settings}
          liveMatches={liveMatches}
          upcomingMatches={schedule}
          streamEvents={streamEvents}
          onSelectTab={() => {}}
          onUpdateSettings={handleUpdateSettings}
          isDetached={true}
        />
      </div>
    );
  }

  const syncLabel = syncFailed
    ? lastSync
      ? `Connection problem · showing data from ${new Date(lastSync).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`
      : "Can't reach the data sources right now"
    : lastSync
      ? `Updated ${new Date(lastSync).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`
      : "Loading…";

  return (
    <div className="flex flex-col h-screen w-screen bg-[#091428] text-[#f0e6d2] overflow-hidden select-none">
      {/* Header */}
      <Header
        settings={settings}
        onUpdateSettings={handleUpdateSettings}
        liveMatches={liveMatches}
        streamEvents={streamEvents}
        onRefresh={() => refreshData(true)}
        isRefreshing={isRefreshing}
        onSelectTab={setActiveTab}
        onOpenUrl={handleOpenUrl}
        updateInfo={updateInfo}
      />

      {/* Tab Navigation */}
      <Navigation activeTab={activeTab} onSelectTab={setActiveTab} liveCount={liveMatches.length} />

      {/* Docked Ticker Bar */}
      {settings.tickerMode === "docked" && (
        <TickerBar
          settings={settings}
          liveMatches={liveMatches}
          upcomingMatches={schedule}
          streamEvents={streamEvents}
          onSelectTab={setActiveTab}
          onUpdateSettings={handleUpdateSettings}
          isDetached={false}
        />
      )}

      {/* Main Content View Container */}
      <main className="flex-1 overflow-hidden relative">
        {activeTab === "live" && (
          <LiveView
            matches={liveMatches}
            schedule={schedule}
            settings={settings}
            catalog={catalog}
            onOpenUrl={handleOpenUrl}
            onSelectTab={setActiveTab}
            onUpdateSettings={handleUpdateSettings}
          />
        )}
        {activeTab === "schedule" && (
          <ScheduleView
            schedule={schedule}
            settings={settings}
            catalog={catalog}
            onOpenUrl={handleOpenUrl}
            onUpdateSettings={handleUpdateSettings}
          />
        )}
        {activeTab === "stream" && (
          <StreamView
            events={streamEvents}
            settings={settings}
            catalog={catalog}
            onOpenUrl={handleOpenUrl}
          />
        )}
        {activeTab === "watchlist" && (
          <WatchlistView
            settings={settings}
            catalog={catalog}
            onUpdateSettings={handleUpdateSettings}
            onRefreshCatalog={handleRefreshCatalog}
            isRefreshingCatalog={isRefreshing}
          />
        )}
        {activeTab === "news" && <NewsView onOpenUrl={handleOpenUrl} />}
        {activeTab === "settings" && (
          <SettingsView
            settings={settings}
            catalog={catalog}
            onUpdateSettings={handleUpdateSettings}
            onOpenUrl={handleOpenUrl}
            onRefreshCatalog={handleRefreshCatalog}
            updateInfo={updateInfo}
            onCheckForUpdate={handleCheckForUpdate}
            isCheckingUpdate={isCheckingUpdate}
          />
        )}
      </main>

      {/* Minimal Status Footer */}
      <footer className="bg-[#0a0e17] border-t border-[#1e282d] px-4 py-1 flex items-center justify-between text-[11px] text-[#7e8e9f] select-none">
        <div className="flex items-center gap-2">
          <span className={`w-1.5 h-1.5 rounded-full ${syncFailed ? "bg-[#e84057]" : "bg-[#0ac8b9]"}`} />
          <span>{syncLabel}</span>
        </div>
        <div className="flex items-center gap-3">
          {settings.spoilerMode && (
            <span className="text-[#c8aa6e] font-semibold">SPOILER MODE ACTIVE</span>
          )}
          <span
            onClick={() => handleOpenUrl("https://drmonocle.com")}
            className="hover:text-[#c8aa6e] cursor-pointer"
          >
            Monocle Productions LLC
          </span>
        </div>
      </footer>
    </div>
  );
}
