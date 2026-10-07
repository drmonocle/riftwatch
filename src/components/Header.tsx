import React from "react";
import { AppSettings, Match, StreamEvent } from "../types";
import { Radio, RefreshCw, Eye, EyeOff, Heart, ExternalLink } from "lucide-react";

interface HeaderProps {
  settings: AppSettings;
  onUpdateSettings: (s: Partial<AppSettings>) => void;
  liveMatches: Match[];
  streamEvents: StreamEvent[];
  onRefresh: () => void;
  isRefreshing: boolean;
  onSelectTab: (tab: any) => void;
}

export const Header: React.FC<HeaderProps> = ({
  settings,
  onUpdateSettings,
  liveMatches,
  streamEvents,
  onRefresh,
  isRefreshing,
  onSelectTab,
}) => {
  const hasLive = liveMatches.length > 0;
  const firstLive = hasLive ? liveMatches[0] : null;

  return (
    <header className="bg-[#0a0e17] border-b border-[#c8aa6e] px-4 py-2 flex items-center justify-between select-none">
      {/* Brand & Live Status Pills */}
      <div className="flex items-center gap-4">
        <div className="flex items-baseline gap-1.5 cursor-pointer" onClick={() => onSelectTab("live")}>
          <span className="text-[#c8aa6e] font-bold text-lg tracking-wider">RIFTWATCH</span>
          <span className="text-[#a09b8c] text-[10px]">v0.3.0</span>
        </div>

        {/* Pro Matches Pill */}
        <div
          onClick={() => onSelectTab("live")}
          className={`flex items-center gap-2 px-2.5 py-1 rounded text-xs cursor-pointer border transition-colors ${
            hasLive
              ? "bg-[#1e131d] border-[#e84057] text-[#e84057]"
              : "bg-[#0a1420] border-[#1e282d] text-[#7e8e9f] hover:border-[#c8aa6e]"
          }`}
          title="Click to view Live Pro Matches"
        >
          <span className={`w-2 h-2 rounded-full ${hasLive ? "bg-[#e84057] animate-pulse" : "bg-[#7e8e9f]"}`} />
          <span className="font-semibold">
            {hasLive
              ? `LIVE: ${firstLive?.team1Code} vs ${firstLive?.team2Code} (${firstLive?.leagueName})`
              : "Pro Matches: Idle"}
          </span>
        </div>

        {/* 24/7 Twitch Stream Pill */}
        <div
          onClick={() => onSelectTab("stream")}
          className="flex items-center gap-2 px-2.5 py-1 rounded text-xs cursor-pointer border bg-[#0a1420] border-[#1e282d] text-[#0ac8b9] hover:border-[#0ac8b9] transition-colors"
          title="Click to view 24/7 Continuous Twitch Stream"
        >
          <Radio className="w-3.5 h-3.5 text-[#0ac8b9]" />
          <span className="font-medium">Twitch 24/7: Airing Now</span>
        </div>
      </div>

      {/* Quick Action Buttons */}
      <div className="flex items-center gap-2">
        {/* Spoiler Mode Toggle */}
        <button
          onClick={() => onUpdateSettings({ spoilerMode: !settings.spoilerMode })}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium border transition-colors ${
            settings.spoilerMode
              ? "bg-[#c8aa6e] border-[#c8aa6e] text-[#091428]"
              : "bg-[#0a1420] border-[#1e282d] text-[#f0e6d2] hover:bg-[#121e2d]"
          }`}
          title="Spoiler mode hides match scores and in-game gold"
        >
          {settings.spoilerMode ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
          <span>{settings.spoilerMode ? "Spoilers Hidden" : "Spoilers Shown"}</span>
        </button>

        {/* Support Ko-Fi */}
        <a
          href="https://ko-fi.com/monocleproductions"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium bg-[#720e9e] hover:bg-[#8c19bd] text-white transition-colors"
          title="Support RiftWatch development on Ko-fi"
        >
          <Heart className="w-3.5 h-3.5 fill-current" />
          <span>Support</span>
        </a>

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium bg-[#0a1420] hover:bg-[#121e2d] border border-[#1e282d] text-[#f0e6d2] transition-colors"
          title="Refresh match data"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-[#c8aa6e]" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>
    </header>
  );
};
