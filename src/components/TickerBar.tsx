import React, { useState, useEffect } from "react";
import { AppSettings, Match, StreamEvent } from "../types";
import { ChevronLeft, ChevronRight, Pin, PinOff, Minimize2, Maximize2, X } from "lucide-react";

interface TickerBarProps {
  settings: AppSettings;
  liveMatches: Match[];
  upcomingMatches: Match[];
  streamEvents: StreamEvent[];
  onSelectTab: (tab: any) => void;
  onUpdateSettings: (s: Partial<AppSettings>) => void;
  isDetached?: boolean;
}

interface TickerItem {
  id: string;
  badge: string;
  badgeBg: string;
  badgeFg: string;
  headline: string;
  details: string;
  targetTab: string;
}

export const TickerBar: React.FC<TickerBarProps> = ({
  settings,
  liveMatches,
  upcomingMatches,
  streamEvents,
  onSelectTab,
  onUpdateSettings,
  isDetached = false,
}) => {
  const [index, setIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);

  const handleStartDrag = (e: React.MouseEvent) => {
    if (e.button === 0) {
      import("@tauri-apps/api/core")
        .then(({ invoke }) => invoke("start_window_drag"))
        .catch(() => {});
    }
  };

  const handleDock = () => {
    onUpdateSettings({ tickerMode: "docked" });
    import("@tauri-apps/api/core")
      .then(({ invoke }) => {
        invoke("hide_ticker").catch(() => {});
        invoke("show_main").catch(() => {});
      })
      .catch(() => {});
  };

  const handleDetach = () => {
    onUpdateSettings({ tickerMode: "detached" });
    import("@tauri-apps/api/core")
      .then(({ invoke }) => invoke("show_ticker").catch(() => {}))
      .catch(() => {});
  };

  const handleClose = () => {
    onUpdateSettings({ tickerMode: "hidden" });
    if (isDetached) {
      import("@tauri-apps/api/core")
        .then(({ invoke }) => invoke("hide_ticker").catch(() => {}))
        .catch(() => {});
    }
  };

  // Compile items
  const items: TickerItem[] = [];

  // 1. Live pro matches
  for (const m of liveMatches) {
    const scores = settings.spoilerMode ? "Scores Hidden" : `${m.team1Score} : ${m.team2Score}`;
    items.push({
      id: `live-${m.matchId}`,
      badge: "● LIVE",
      badgeBg: "bg-[#e84057]",
      badgeFg: "text-white",
      headline: `${m.leagueName} · ${m.team1Code} ${scores} ${m.team2Code}`,
      details: settings.spoilerMode ? "Spoiler mode active" : `Bo${m.bestOf}`,
      targetTab: "live",
    });
  }

  // 2. 24/7 continuous stream
  if (streamEvents.length > 0) {
    const now = Date.now();
    const past = streamEvents.filter((e) => e.utcIso && new Date(e.utcIso).getTime() <= now);
    const cur = past.length > 0 ? past[past.length - 1] : streamEvents[0];
    if (cur) {
      items.push({
        id: `stream-${cur.id}`,
        badge: "📺 24/7 STREAM",
        badgeBg: "bg-[#0ac8b9]",
        badgeFg: "text-[#091428]",
        headline: `24/7 Marathon: ${cur.event} ${cur.season}`,
        details: cur.stage ? `${cur.stage} · Airing on Twitch & YouTube` : "Airing on Twitch & YouTube",
        targetTab: "stream",
      });
    }
  }

  // 3. Upcoming matches
  for (const m of upcomingMatches.slice(0, 3)) {
    const relTime = m.startTimeUtc
      ? new Date(m.startTimeUtc).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })
      : "Soon";
    items.push({
      id: `up-${m.matchId}`,
      badge: "⏰ UPCOMING",
      badgeBg: "bg-[#c8aa6e]",
      badgeFg: "text-[#091428]",
      headline: `${m.leagueName} · ${m.team1Code} vs ${m.team2Code}`,
      details: `Starts at ${relTime}`,
      targetTab: "schedule",
    });
  }

  // Auto rotation
  useEffect(() => {
    if (items.length <= 1 || isHovered) return;
    const cycleMs = (settings.tickerCycleSec || 5) * 1000;
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % items.length);
    }, cycleMs);
    return () => clearInterval(timer);
  }, [items.length, isHovered, settings.tickerCycleSec]);

  if (settings.tickerMode === "hidden" && !isDetached) {
    return null;
  }

  const currentItem = items[index % Math.max(1, items.length)];

  return (
    <div
      data-tauri-drag-region
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`select-none flex items-center justify-between text-xs px-3 py-1 transition-colors ${
        isDetached
          ? "bg-[#080c14] border border-[#c8aa6e]/60 shadow-2xl h-[38px] w-full"
          : "bg-[#080c14] border-b border-[#1e282d] h-8"
      }`}
    >
      {/* Detached Drag Grip */}
      {isDetached && (
        <div
          data-tauri-drag-region
          onMouseDown={handleStartDrag}
          className="cursor-move flex items-center justify-center text-[#c8aa6e] hover:text-white mr-2 text-sm select-none px-1.5 py-0.5 rounded hover:bg-[#1e282d] transition-colors"
          title="Click and drag to reposition floating HUD"
        >
          ⠿
        </div>
      )}

      {/* Main Clickable Content */}
      <div
        onClick={() => {
          if (isDetached) {
            import("@tauri-apps/api/core")
              .then(({ invoke }) => invoke("show_main").catch(() => {}))
              .catch(() => {});
          }
          if (currentItem) onSelectTab(currentItem.targetTab);
        }}
        className="flex items-center gap-2.5 overflow-hidden flex-1 cursor-pointer"
        title="Click to jump to match"
      >
        {currentItem ? (
          <>
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${currentItem.badgeBg} ${currentItem.badgeFg}`}
            >
              {currentItem.badge}
            </span>
            <span className="font-semibold text-[#f0e6d2] truncate">{currentItem.headline}</span>
            <span className="text-[#7e8e9f] hidden sm:inline truncate">· {currentItem.details}</span>
          </>
        ) : (
          <span className="text-[#7e8e9f] italic">Checking live pro games & 24/7 marathon…</span>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-1.5 ml-2 text-[#7e8e9f]">
        {items.length > 1 && (
          <>
            <span className="text-[10px] text-[#7e8e9f] mr-1">
              {index + 1}/{items.length}
            </span>
            <button
              onClick={() => setIndex((prev) => (prev - 1 + items.length) % items.length)}
              className="p-0.5 hover:text-[#c8aa6e] rounded hover:bg-[#1e282d]"
              title="Previous item"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setIndex((prev) => (prev + 1) % items.length)}
              className="p-0.5 hover:text-[#c8aa6e] rounded hover:bg-[#1e282d]"
              title="Next item"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </>
        )}

        {/* Detach / Dock Mode Button */}
        {!isDetached ? (
          <button
            onClick={handleDetach}
            className="flex items-center gap-1 px-1.5 py-0.5 rounded hover:text-[#0ac8b9] hover:bg-[#1e282d] text-[10px]"
            title="Detach to floating desktop HUD overlay"
          >
            <Maximize2 className="w-3 h-3" />
            <span>Detach</span>
          </button>
        ) : (
          <>
            {/* Pin Always on Top Toggle */}
            <button
              onClick={() => {
                const nextTop = !settings.tickerTopmost;
                onUpdateSettings({ tickerTopmost: nextTop });
                import("@tauri-apps/api/core")
                  .then(({ invoke }) => invoke("set_ticker_topmost", { topmost: nextTop }))
                  .catch(() => {});
              }}
              className={`p-1 rounded hover:bg-[#1e282d] ${
                settings.tickerTopmost ? "text-[#c8aa6e]" : "text-[#7e8e9f]"
              }`}
              title={settings.tickerTopmost ? "Pinned Always on Top" : "Unpinned"}
            >
              {settings.tickerTopmost ? <Pin className="w-3 h-3" /> : <PinOff className="w-3 h-3" />}
            </button>

            <button
              onClick={handleDock}
              className="flex items-center gap-1 px-1.5 py-0.5 rounded hover:text-[#c8aa6e] hover:bg-[#1e282d] text-[10px]"
              title="Dock back to main RiftWatch window"
            >
              <Minimize2 className="w-3 h-3" />
              <span>Dock</span>
            </button>
          </>
        )}

        {/* Close/Hide Button */}
        <button
          onClick={handleClose}
          className="p-1 hover:text-[#e84057] rounded hover:bg-[#1e282d]"
          title="Hide ticker bar (can be restored in Settings)"
        >
          <X className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
};
