import React, { useState, useEffect } from "react";
import { AppSettings, Match, StreamEvent, CatalogData } from "./types";
import {
  loadSettings,
  saveSettings,
  fetchLiveMatches,
  fetchSchedule,
  fetchStreamSchedule,
  loadCatalog,
  fetchLiveCatalog,
} from "./api";
import { Header } from "./components/Header";
import { Navigation, TabKey } from "./components/Navigation";
import { TickerBar } from "./components/TickerBar";
import { LiveView } from "./components/views/LiveView";
import { ScheduleView } from "./components/views/ScheduleView";
import { StreamView } from "./components/views/StreamView";
import { WatchlistView } from "./components/views/WatchlistView";
import { NewsView } from "./components/views/NewsView";
import { SettingsView } from "./components/views/SettingsView";

export default function App() {
  const [settings, setSettings] = useState<AppSettings>(loadSettings());
  const [catalog, setCatalog] = useState<CatalogData>(loadCatalog());

  // Determine initial tab: on first launch, open directly to Watchlist so users configure their teams
  const [activeTab, setActiveTab] = useState<TabKey>(() => {
    try {
      const hasLaunched = localStorage.getItem("riftwatch_has_launched");
      if (!hasLaunched) {
        localStorage.setItem("riftwatch_has_launched", "true");
        return "watchlist";
      }
    } catch {}
    const s = loadSettings();
    return s.defaultTab || "live";
  });

  const [liveMatches, setLiveMatches] = useState<Match[]>([]);
  const [schedule, setSchedule] = useState<Match[]>([]);
  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Sync settings across windows (main window and detached HUD window)
  useEffect(() => {
    const handleSync = () => {
      setSettings(loadSettings());
    };
    window.addEventListener("riftwatch_settings_updated", handleSync);
    window.addEventListener("storage", handleSync);
    return () => {
      window.removeEventListener("riftwatch_settings_updated", handleSync);
      window.removeEventListener("storage", handleSync);
    };
  }, []);

  // Load initial data and poll periodically
  const refreshData = async () => {
    setIsRefreshing(true);
    try {
      const [liveRes, schedRes, streamRes] = await Promise.all([
        fetchLiveMatches(),
        fetchSchedule(),
        fetchStreamSchedule(),
      ]);
      setLiveMatches(liveRes.matches);
      setSchedule(schedRes);
      setStreamEvents(streamRes);
    } catch (err) {
      console.error("Error refreshing data:", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleUpdateSettings = (partial: Partial<AppSettings>) => {
    setSettings((prev) => {
      const updated = { ...prev, ...partial };
      saveSettings(updated);
      return updated;
    });
  };

  // Synchronize detached ticker window state with Tauri
  useEffect(() => {
    try {
      import("@tauri-apps/api/core").then(({ invoke }) => {
        if (settings.tickerMode === "detached") {
          invoke("show_ticker").catch(() => {});
        } else {
          invoke("hide_ticker").catch(() => {});
        }
      }).catch(() => {});
    } catch {
      // Fallback in web browser mode
    }
  }, [settings.tickerMode]);

  useEffect(() => {
    try {
      import("@tauri-apps/api/core").then(({ invoke }) => {
        invoke("set_ticker_topmost", { topmost: settings.tickerTopmost }).catch(() => {});
      }).catch(() => {});
    } catch {
      // Fallback in web browser mode
    }
  }, [settings.tickerTopmost]);

  // Auto-refresh catalog in background if older than 24 hours
  useEffect(() => {
    const age = Date.now() - (catalog.updatedAt || 0);
    if (age > 24 * 60 * 60 * 1000) {
      fetchLiveCatalog()
        .then((updated) => setCatalog(updated))
        .catch(() => {});
    }
  }, []);

  const handleRefreshCatalog = async () => {
    setIsRefreshing(true);
    try {
      const updated = await fetchLiveCatalog();
      setCatalog(updated);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleOpenUrl = (url: string) => {
    try {
      import("@tauri-apps/api/core")
        .then(({ invoke }) => {
          invoke("open_external_url", { url }).catch(() => {
            window.open(url, "_blank");
          });
        })
        .catch(() => {
          window.open(url, "_blank");
        });
    } catch {
      window.open(url, "_blank");
    }
  };

  // If running in detached HUD mode (query parameter ?mode=detached)
  const isHudOnly = window.location.search.includes("mode=detached");
  if (isHudOnly) {
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

  return (
    <div className="flex flex-col h-screen w-screen bg-[#091428] text-[#f0e6d2] overflow-hidden select-none">
      {/* Header */}
      <Header
        settings={settings}
        onUpdateSettings={handleUpdateSettings}
        liveMatches={liveMatches}
        streamEvents={streamEvents}
        onRefresh={refreshData}
        isRefreshing={isRefreshing}
        onSelectTab={setActiveTab}
        onOpenUrl={handleOpenUrl}
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
            onOpenUrl={handleOpenUrl}
            onSelectTab={setActiveTab}
          />
        )}
        {activeTab === "schedule" && (
          <ScheduleView schedule={schedule} settings={settings} onOpenUrl={handleOpenUrl} />
        )}
        {activeTab === "stream" && (
          <StreamView events={streamEvents} settings={settings} onOpenUrl={handleOpenUrl} />
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
          />
        )}
      </main>

      {/* Minimal Status Footer */}
      <footer className="bg-[#0a0e17] border-t border-[#1e282d] px-4 py-1 flex items-center justify-between text-[11px] text-[#7e8e9f] select-none">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#0ac8b9]" />
          <span>All data sources synchronized</span>
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
