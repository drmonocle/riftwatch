import React from "react";
import { AppSettings } from "../../types";
import { Bell, Monitor, Star, ShieldCheck, Heart, ExternalLink } from "lucide-react";

interface SettingsViewProps {
  settings: AppSettings;
  onUpdateSettings: (s: Partial<AppSettings>) => void;
  onOpenUrl: (url: string) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ settings, onUpdateSettings, onOpenUrl }) => {
  return (
    <div className="p-4 space-y-6 max-w-4xl mx-auto overflow-y-auto h-full select-none text-xs">
      {/* Display & Ticker Section */}
      <section className="space-y-3">
        <h2 className="text-xs font-bold text-[#c8aa6e] uppercase tracking-wider flex items-center gap-1.5">
          <Monitor className="w-3.5 h-3.5" />
          Display & Live Ticker Bar
        </h2>

        <div className="space-y-2">
          {/* Ticker Mode Selector */}
          <div className="flex items-center justify-between p-3 rounded bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Live Ticker Mode</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Docked inside window, detached floating desktop HUD, or completely hidden.
              </div>
            </div>
            <div className="flex items-center gap-1 bg-[#091428] p-1 rounded border border-[#1e282d]">
              {(["docked", "detached", "hidden"] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => onUpdateSettings({ tickerMode: mode })}
                  className={`px-3 py-1 text-xs font-semibold rounded transition-all capitalize ${
                    settings.tickerMode === mode
                      ? "bg-[#0ac8b9] text-[#091428]"
                      : "text-[#7e8e9f] hover:text-[#f0e6d2]"
                  }`}
                >
                  {mode === "detached" ? "⧉ Detached HUD" : mode}
                </button>
              ))}
            </div>
          </div>

          {/* Detached Pin Always on Top */}
          <div className="flex items-center justify-between p-3 rounded bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Detached Ticker Always on Top</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Keep the floating desktop HUD bar pinned above full-screen games and browser windows.
              </div>
            </div>
            <button
              onClick={() => onUpdateSettings({ tickerTopmost: !settings.tickerTopmost })}
              className={`px-3 py-1 font-bold rounded transition-colors ${
                settings.tickerTopmost
                  ? "bg-[#0ac8b9] text-[#091428]"
                  : "bg-[#1e282d] text-[#7e8e9f]"
              }`}
            >
              {settings.tickerTopmost ? "ON" : "OFF"}
            </button>
          </div>

          {/* Spoiler Mode */}
          <div className="flex items-center justify-between p-3 rounded bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Spoiler Mode</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Hide all live game scores and results until you choose to reveal them.
              </div>
            </div>
            <button
              onClick={() => onUpdateSettings({ spoilerMode: !settings.spoilerMode })}
              className={`px-3 py-1 font-bold rounded transition-colors ${
                settings.spoilerMode
                  ? "bg-[#0ac8b9] text-[#091428]"
                  : "bg-[#1e282d] text-[#7e8e9f]"
              }`}
            >
              {settings.spoilerMode ? "ON" : "OFF"}
            </button>
          </div>

          {/* Default Tab on Launch */}
          <div className="flex items-center justify-between p-3 rounded bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Default Tab on Launch</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Select which view opens automatically when starting RiftWatch.
              </div>
            </div>
            <div className="flex items-center gap-1 bg-[#091428] p-1 rounded border border-[#1e282d]">
              {(["live", "schedule", "stream", "watchlist"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => onUpdateSettings({ defaultTab: tab })}
                  className={`px-2.5 py-1 text-xs font-semibold rounded transition-all capitalize ${
                    settings.defaultTab === tab
                      ? "bg-[#c8aa6e] text-[#091428]"
                      : "text-[#7e8e9f] hover:text-[#f0e6d2]"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Notifications Section */}
      <section className="space-y-3">
        <h2 className="text-xs font-bold text-[#c8aa6e] uppercase tracking-wider flex items-center gap-1.5">
          <Bell className="w-3.5 h-3.5" />
          Desktop Notifications
        </h2>

        <div className="space-y-2">
          <div className="flex items-center justify-between p-3 rounded bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Live Kickoff Alerts</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Display desktop notifications when followed teams or players begin a match.
              </div>
            </div>
            <button
              onClick={() => onUpdateSettings({ notifyKickoff: !settings.notifyKickoff })}
              className={`px-3 py-1 font-bold rounded transition-colors ${
                settings.notifyKickoff ? "bg-[#0ac8b9] text-[#091428]" : "bg-[#1e282d] text-[#7e8e9f]"
              }`}
            >
              {settings.notifyKickoff ? "ON" : "OFF"}
            </button>
          </div>

          <div className="flex items-center justify-between p-3 rounded bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">Pre-match 15m Countdown</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Remind 15 minutes before your followed pro matches go live.
              </div>
            </div>
            <button
              onClick={() => onUpdateSettings({ notifyPregame: !settings.notifyPregame })}
              className={`px-3 py-1 font-bold rounded transition-colors ${
                settings.notifyPregame ? "bg-[#0ac8b9] text-[#091428]" : "bg-[#1e282d] text-[#7e8e9f]"
              }`}
            >
              {settings.notifyPregame ? "ON" : "OFF"}
            </button>
          </div>

          <div className="flex items-center justify-between p-3 rounded bg-[#0a1420] border border-[#1e282d]">
            <div>
              <div className="font-semibold text-[#f0e6d2]">24/7 Stream & S-Tier Banger Alerts</div>
              <div className="text-[11px] text-[#7e8e9f]">
                Notify when S-Tier legendary marathon games begin on Twitch and YouTube.
              </div>
            </div>
            <button
              onClick={() => onUpdateSettings({ notifyStream: !settings.notifyStream })}
              className={`px-3 py-1 font-bold rounded transition-colors ${
                settings.notifyStream ? "bg-[#0ac8b9] text-[#091428]" : "bg-[#1e282d] text-[#7e8e9f]"
              }`}
            >
              {settings.notifyStream ? "ON" : "OFF"}
            </button>
          </div>
        </div>
      </section>

      {/* Support Section */}
      <section className="p-4 rounded-lg bg-[#0a1420] border border-[#720e9e]/60 flex items-center justify-between">
        <div>
          <div className="font-bold text-[#f0e6d2] flex items-center gap-1.5 text-sm">
            <Heart className="w-4 h-4 text-[#ff4655] fill-current" />
            Support RiftWatch Development
          </div>
          <div className="text-[11px] text-[#7e8e9f] mt-0.5">
            RiftWatch is 100% free and open-source. Help fund 24/7 dedicated broadcast servers and continuous updates.
          </div>
        </div>
        <button
          onClick={() => onOpenUrl("https://ko-fi.com/monocleproductions")}
          className="flex items-center gap-1.5 px-4 py-2 rounded bg-[#720e9e] hover:bg-[#8c19bd] text-white font-bold transition-colors"
        >
          <span>Support on Ko-fi</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </button>
      </section>

      {/* About Section */}
      <footer className="pt-2 text-[11px] text-[#7e8e9f] space-y-1">
        <div>RiftWatch Tauri v0.3.0 · Powered by Rust, React & WebView2</div>
        <div>
          RiftWatch is an unofficial fan companion and is not endorsed by Riot Games. League of Legends is a trademark of Riot Games, Inc.
        </div>
      </footer>
    </div>
  );
};
