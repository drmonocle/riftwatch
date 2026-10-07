import React, { useState, useEffect } from "react";
import { AppSettings, Match, StreamEvent } from "./types";
import { loadSettings, saveSettings, fetchLiveMatches, fetchSchedule, fetchStreamSchedule } from "./api";
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
  const [activeTab, setActiveTab] = useState<TabKey>(settings.defaultTab || "live");
  const [liveMatches, setLiveMatches] = useState<Match[]>([]);
  const [schedule, setSchedule] = useState<Match[]>([]);
  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Load Initial Data
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
    // Auto-refresh interval (every 60s)
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
      // Fallback if running outside Tauri
    }
  }, [settings.tickerMode]);

  useEffect(() => {
    try {
      import("@tauri-apps/api/core").then(({ invoke }) => {
        invoke("set_ticker_topmost", { topmost: settings.tickerTopmost }).catch(() => {});
      }).catch(() => {});
    } catch {
      // Fallback if running outside Tauri
    }
  }, [settings.tickerTopmost]);

  const handleOpenUrl = (url: string) => {
    window.open(url, "_blank");
  };

  // If running in detached HUD mode standalone (query parameter ?mode=detached)
  const isHudOnly = window.location.search.includes("mode=detached");
  if (isHudOnly) {
    return (
      <div className="w-screen h-screen bg-transparent overflow-hidden">
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
    <div className="flex flex-col h-screen w-screen bg-[#091428] text-[#f0e6d2] overflow-hidden">
      {/* Header */}
      <Header
        settings={settings}
        onUpdateSettings={handleUpdateSettings}
        liveMatches={liveMatches}
        streamEvents={streamEvents}
        onRefresh={refreshData}
        isRefreshing={isRefreshing}
        onSelectTab={setActiveTab}
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

      {/* Detached HUD Overlay (when detached is selected) */}
      {settings.tickerMode === "detached" && (
        <div className="fixed top-2 left-1/2 -translate-x-1/2 z-50 w-[700px] shadow-2xl">
          <TickerBar
            settings={settings}
            liveMatches={liveMatches}
            upcomingMatches={schedule}
            streamEvents={streamEvents}
            onSelectTab={setActiveTab}
            onUpdateSettings={handleUpdateSettings}
            isDetached={true}
          />
        </div>
      )}

      {/* Main Content View Container */}
      <main className="flex-1 overflow-hidden relative">
        {activeTab === "live" && (
          <LiveView matches={liveMatches} settings={settings} onOpenUrl={handleOpenUrl} />
        )}
        {activeTab === "schedule" && (
          <ScheduleView schedule={schedule} settings={settings} onOpenUrl={handleOpenUrl} />
        )}
        {activeTab === "stream" && (
          <StreamView events={streamEvents} settings={settings} onOpenUrl={handleOpenUrl} />
        )}
        {activeTab === "watchlist" && (
          <WatchlistView settings={settings} onUpdateSettings={handleUpdateSettings} />
        )}
        {activeTab === "news" && <NewsView onOpenUrl={handleOpenUrl} />}
        {activeTab === "settings" && (
          <SettingsView
            settings={settings}
            onUpdateSettings={handleUpdateSettings}
            onOpenUrl={handleOpenUrl}
          />
        )}
      </main>

      {/* Minimal Footer */}
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
