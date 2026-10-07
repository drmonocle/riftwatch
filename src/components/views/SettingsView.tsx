import React, { useState } from "react";
import { AppSettings } from "../../types";
import {
  Monitor,
  Bell,
  Minimize2,
  Trash2,
  RefreshCw,
  ExternalLink,
  ShieldAlert,
  FolderOpen,
  Heart,
  Check,
  Globe,
  Radio,
} from "lucide-react";

interface SettingsViewProps {
  settings: AppSettings;
  onUpdateSettings: (s: Partial<AppSettings>) => void;
  onOpenUrl: (url: string) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  settings,
  onUpdateSettings,
  onOpenUrl,
}) => {
  const [cacheCleared, setCacheCleared] = useState(false);

  const handleClearCache = () => {
    localStorage.removeItem("riftwatch_settings");
    setCacheCleared(true);
    setTimeout(() => setCacheCleared(false), 2500);
  };

  const handleResetWatchlist = () => {
    onUpdateSettings({
      followedTeams: [],
      followedPlayers: [],
      followedLeagues: ["worlds", "msi", "first_stand"],
      followedRegions: ["INTERNATIONAL", "KOREA", "CHINA", "EUROPE", "NORTH AMERICA", "APAC", "BRAZIL"],
    });
  };

  return (
    <div className="p-4 space-y-6 max-w-4xl mx-auto overflow-y-auto h-full select-none text-xs">
      {/* 1. Display & Live Ticker Bar */}
      <section className="space-y-3">
        <h2 className="text-xs font-bold text-[#c8aa6e] uppercase tracking-wider flex items-center gap-1.5">
          <Monitor className="w-3.5 h-3.5 text-[#0ac8b9]" />
          Display & Live Ticker Bar
        </h2>

        <div className="space-y-2">
          {/* Spoiler Mode */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Spoiler Mode</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Hide all match scores, game results, and in-game statistics until manually revealed.
              </div>
            </div>
            <button
              onClick={() => onUpdateSettings({ spoilerMode: !settings.spoilerMode })}
              className={`px-3 py-1 font-bold rounded text-xs transition-colors ${
                settings.spoilerMode
                  ? "bg-[#0ac8b9] text-[#091428]"
                  : "bg-[#1e282d] text-[#7e8e9f] hover:text-[#f0e6d2]"
              }`}
            >
              {settings.spoilerMode ? "ON" : "OFF"}
            </button>
          </div>

          {/* Live Ticker Mode Selector */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-lg bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Live Ticker Bar Mode</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Display real-time scores, countdowns, and 24/7 stream highlights.
              </div>
            </div>
            <div className="flex items-center gap-1 bg-[#091428] p-1 rounded border border-[#1e282d]">
              {(["docked", "detached", "hidden"] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => {
                    onUpdateSettings({ tickerMode: mode });
                    import("@tauri-apps/api/core").then(({ invoke }) => {
                      if (mode === "detached") {
                        invoke("show_ticker").catch(() => {});
                      } else {
                        invoke("hide_ticker").catch(() => {});
                      }
                    }).catch(() => {});
                  }}
                  className={`px-3 py-1 text-xs font-semibold rounded transition-all capitalize ${
                    settings.tickerMode === mode
                      ? "bg-[#c8aa6e] text-[#091428]"
                      : "text-[#7e8e9f] hover:text-[#f0e6d2]"
                  }`}
                >
                  {mode === "detached" ? "⧉ Detached HUD" : mode}
                </button>
              ))}
            </div>
          </div>

          {/* Detached Pin Always on Top */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Detached Ticker Always on Top</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Keep the floating desktop HUD bar pinned above full-screen games and browser windows.
              </div>
            </div>
            <button
              onClick={() => {
                const nextVal = !settings.tickerTopmost;
                onUpdateSettings({ tickerTopmost: nextVal });
                import("@tauri-apps/api/core").then(({ invoke }) => {
                  invoke("set_ticker_topmost", { topmost: nextVal }).catch(() => {});
                }).catch(() => {});
              }}
              className={`px-3 py-1 font-bold rounded text-xs transition-colors ${
                settings.tickerTopmost
                  ? "bg-[#0ac8b9] text-[#091428]"
                  : "bg-[#1e282d] text-[#7e8e9f] hover:text-[#f0e6d2]"
              }`}
            >
              {settings.tickerTopmost ? "ON" : "OFF"}
            </button>
          </div>

          {/* Ticker Rotation Speed */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Ticker Rotation Interval</div>
              <div className="text-[11px] text-[#7e8e9f]">
                How long each match or highlight stays visible on the ribbon before rotating.
              </div>
            </div>
            <div className="flex items-center gap-1 bg-[#091428] p-1 rounded border border-[#1e282d]">
              {[3, 5, 8, 12].map((sec) => (
                <button
                  key={sec}
                  onClick={() => onUpdateSettings({ tickerCycleSec: sec })}
                  className={`px-2.5 py-1 text-xs font-semibold rounded transition-all ${
                    (settings.tickerCycleSec || 5) === sec
                      ? "bg-[#0ac8b9] text-[#091428]"
                      : "text-[#7e8e9f] hover:text-[#f0e6d2]"
                  }`}
                >
                  {sec}s
                </button>
              ))}
            </div>
          </div>

          {/* Default Tab on Launch */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-lg bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Default Tab on Launch</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Choose which view opens automatically when starting RiftWatch.
              </div>
            </div>
            <div className="flex items-center gap-1 bg-[#091428] p-1 rounded border border-[#1e282d]">
              {(["live", "schedule", "stream", "watchlist"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => onUpdateSettings({ defaultTab: t })}
                  className={`px-2.5 py-1 text-xs font-semibold rounded transition-all capitalize ${
                    settings.defaultTab === t
                      ? "bg-[#c8aa6e] text-[#091428]"
                      : "text-[#7e8e9f] hover:text-[#f0e6d2]"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 2. Desktop Notifications & Alerts */}
      <section className="space-y-3">
        <h2 className="text-xs font-bold text-[#c8aa6e] uppercase tracking-wider flex items-center gap-1.5">
          <Bell className="w-3.5 h-3.5 text-[#0ac8b9]" />
          Desktop Notifications & Alerts
        </h2>

        <div className="space-y-2">
          <div className="flex items-center justify-between p-3 rounded-lg bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Live Kickoff Alerts</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Display desktop notifications when followed teams or players begin a match.
              </div>
            </div>
            <button
              onClick={() => onUpdateSettings({ notifyKickoff: !settings.notifyKickoff })}
              className={`px-3 py-1 font-bold rounded text-xs transition-colors ${
                settings.notifyKickoff ? "bg-[#0ac8b9] text-[#091428]" : "bg-[#1e282d] text-[#7e8e9f]"
              }`}
            >
              {settings.notifyKickoff ? "ON" : "OFF"}
            </button>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Pre-match 15m Countdown</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Display a reminder notification 15 minutes before your followed pro matches go live.
              </div>
            </div>
            <button
              onClick={() => onUpdateSettings({ notifyPregame: !settings.notifyPregame })}
              className={`px-3 py-1 font-bold rounded text-xs transition-colors ${
                settings.notifyPregame ? "bg-[#0ac8b9] text-[#091428]" : "bg-[#1e282d] text-[#7e8e9f]"
              }`}
            >
              {settings.notifyPregame ? "ON" : "OFF"}
            </button>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">24/7 Stream & S-Tier Banger Alerts</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Notify when S-Tier legendary marathon games begin on Twitch and YouTube.
              </div>
            </div>
            <button
              onClick={() => onUpdateSettings({ notifyStream: !settings.notifyStream })}
              className={`px-3 py-1 font-bold rounded text-xs transition-colors ${
                settings.notifyStream ? "bg-[#0ac8b9] text-[#091428]" : "bg-[#1e282d] text-[#7e8e9f]"
              }`}
            >
              {settings.notifyStream ? "ON" : "OFF"}
            </button>
          </div>
        </div>
      </section>

      {/* 3. System Tray & Startup */}
      <section className="space-y-3">
        <h2 className="text-xs font-bold text-[#c8aa6e] uppercase tracking-wider flex items-center gap-1.5">
          <Minimize2 className="w-3.5 h-3.5 text-[#0ac8b9]" />
          System Tray & Startup
        </h2>

        <div className="space-y-2">
          <div className="flex items-center justify-between p-3 rounded-lg bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Close Button Minimizes to System Tray</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Keep RiftWatch running silently in the Windows notification area when you click the window X button.
              </div>
            </div>
            <button
              onClick={() => onUpdateSettings({ minimizeToTrayOnClose: !settings.minimizeToTrayOnClose })}
              className={`px-3 py-1 font-bold rounded text-xs transition-colors ${
                settings.minimizeToTrayOnClose
                  ? "bg-[#0ac8b9] text-[#091428]"
                  : "bg-[#1e282d] text-[#7e8e9f]"
              }`}
            >
              {settings.minimizeToTrayOnClose ? "ON" : "OFF"}
            </button>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Start RiftWatch with Windows</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Launch automatically in the background when you sign in to Windows.
              </div>
            </div>
            <button
              onClick={() => onUpdateSettings({ startWithWindows: !settings.startWithWindows })}
              className={`px-3 py-1 font-bold rounded text-xs transition-colors ${
                settings.startWithWindows ? "bg-[#0ac8b9] text-[#091428]" : "bg-[#1e282d] text-[#7e8e9f]"
              }`}
            >
              {settings.startWithWindows ? "ON" : "OFF"}
            </button>
          </div>
        </div>
      </section>

      {/* 4. Watchlist Management */}
      <section className="space-y-3">
        <h2 className="text-xs font-bold text-[#c8aa6e] uppercase tracking-wider flex items-center gap-1.5">
          <Globe className="w-3.5 h-3.5 text-[#c8aa6e]" />
          Watchlist & Following Status
        </h2>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-lg bg-[#0a1420] border border-[#1e282d]">
          <div>
            <div className="font-bold text-[#f0e6d2] text-xs">Active Tracked Entities</div>
            <div className="text-[11px] text-[#c8aa6e] mt-0.5">
              {settings.followedTeams.length} teams · {settings.followedPlayers.length} players ·{" "}
              {settings.followedRegions.length} regions · {settings.followedLeagues.length} leagues
            </div>
          </div>
          <button
            onClick={handleResetWatchlist}
            className="px-3 py-1.5 rounded bg-[#091428] border border-[#e84057]/40 text-[#e84057] hover:bg-[#e84057] hover:text-white font-semibold text-xs transition-colors"
          >
            Reset All Follows
          </button>
        </div>
      </section>

      {/* 5. 24/7 Stream Rebroadcasts */}
      <section className="space-y-3">
        <h2 className="text-xs font-bold text-[#c8aa6e] uppercase tracking-wider flex items-center gap-1.5">
          <Radio className="w-3.5 h-3.5 text-[#0ac8b9]" />
          24/7 Stream Rebroadcasts (Twitch & YouTube)
        </h2>

        <div className="p-3.5 rounded-lg bg-[#0a1420] border border-[#1e282d] space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <div className="font-bold text-[#0ac8b9] text-xs">
                Twitch: twitch.tv/LoLWorldChampionship · YouTube: @LoLWorldChampionships
              </div>
              <div className="text-[11px] text-[#7e8e9f] mt-0.5">
                Continuous curated tournament broadcast marathon synced with lolworlds.com.
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => onOpenUrl("https://www.twitch.tv/LoLWorldChampionship")}
                className="px-3 py-1 rounded bg-[#9146ff] hover:bg-[#a970ff] text-white font-bold text-xs transition-colors"
              >
                Twitch ↗
              </button>
              <button
                onClick={() => onOpenUrl("https://www.youtube.com/@LoLWorldChampionships/live")}
                className="px-3 py-1 rounded bg-[#cc0000] hover:bg-[#e60000] text-white font-bold text-xs transition-colors"
              >
                YouTube ↗
              </button>
              <button
                onClick={() => onOpenUrl("https://lolworlds.com")}
                className="px-3 py-1 rounded bg-[#091428] border border-[#1e282d] text-[#7e8e9f] hover:text-[#f0e6d2] font-semibold text-xs transition-colors"
              >
                Schedule ↗
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 6. Data Sources & Storage Diagnostics */}
      <section className="space-y-3">
        <h2 className="text-xs font-bold text-[#c8aa6e] uppercase tracking-wider flex items-center gap-1.5">
          <RefreshCw className="w-3.5 h-3.5 text-[#0ac8b9]" />
          Data Sources & Diagnostics
        </h2>

        <div className="grid gap-1.5">
          {[
            { name: "LoL Esports Schedule Feed", endpoint: "esports-api.lolesports.com/getSchedule" },
            { name: "Live Game State Feed", endpoint: "esports-api.lolesports.com/getLive" },
            { name: "24/7 Stream Marathon Schedule", endpoint: "lolworlds.com/api.ashx?type=schedule-json" },
            { name: "Global Teams & Rosters Directory", endpoint: "esports-api.lolesports.com/getTeams" },
          ].map((ds) => (
            <div
              key={ds.name}
              className="flex items-center justify-between p-2.5 rounded bg-[#0a1420] border border-[#1e282d] text-[11px]"
            >
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#0ac8b9]" />
                <span className="text-[#f0e6d2] font-medium">{ds.name}</span>
              </div>
              <span className="text-[#7e8e9f] font-mono text-[10px]">{ds.endpoint}</span>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2 pt-1">
          <button
            onClick={handleClearCache}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#0a1420] border border-[#1e282d] hover:border-[#e84057] text-[#7e8e9f] hover:text-[#e84057] transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{cacheCleared ? "Cache Cleared!" : "Clear Cache"}</span>
          </button>
        </div>
      </section>

      {/* 7. Support & About */}
      <section className="p-4 rounded-lg bg-[#0a1420] border border-[#720e9e]/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="font-bold text-[#f0e6d2] flex items-center gap-1.5 text-sm">
            <Heart className="w-4 h-4 text-[#ff4655] fill-current" />
            Support RiftWatch
          </div>
          <div className="text-[11px] text-[#7e8e9f] mt-0.5">
            RiftWatch is 100% free and open-source. Help fund 24/7 broadcast servers and active development.
          </div>
        </div>
        <button
          onClick={() => onOpenUrl("https://ko-fi.com/monocle")}
          className="flex items-center gap-1.5 px-4 py-2 rounded bg-[#720e9e] hover:bg-[#8c19bd] text-white font-bold text-xs transition-colors shrink-0"
        >
          <span>Support on Ko-fi</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </button>
      </section>

      {/* Footer */}
      <footer className="pt-2 text-[11px] text-[#7e8e9f] space-y-1">
        <div className="flex items-center justify-between">
          <div>RiftWatch Desktop v0.3.1 · Rust & Webview2 · MIT License</div>
          <button
            onClick={() => onOpenUrl("https://github.com/drmonocle/riftwatch")}
            className="hover:text-[#c8aa6e] underline"
          >
            GitHub Repository ↗
          </button>
        </div>
        <div className="text-[10px] text-[#536675]">
          RiftWatch is an unofficial fan project and is not endorsed by Riot Games. League of Legends is a trademark of Riot Games, Inc.
        </div>
      </footer>
    </div>
  );
};
