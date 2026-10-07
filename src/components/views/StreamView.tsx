import React, { useState, useEffect, useMemo } from "react";
import { StreamEvent, AppSettings, CatalogData } from "../../types";
import {
  Radio,
  Play,
  ExternalLink,
  Flame,
  Trophy,
  Clock,
  Calendar,
  Star,
  Tv,
} from "lucide-react";

interface StreamViewProps {
  events: StreamEvent[];
  settings: AppSettings;
  catalog?: CatalogData;
  onOpenUrl: (url: string) => void;
}

export const StreamView: React.FC<StreamViewProps> = ({
  events,
  settings,
  catalog,
  onOpenUrl,
}) => {
  const [, setTick] = useState(0);

  // Auto-refresh relative countdowns every 30s
  useEffect(() => {
    const timer = setInterval(() => setTick((t) => t + 1), 30000);
    return () => clearInterval(timer);
  }, []);

  // Quick lookup for team logos
  const teamLogos = useMemo(() => {
    const map: Record<string, string> = {};
    if (catalog?.teams) {
      for (const t of catalog.teams) {
        if (t.code && t.image) map[t.code.toUpperCase()] = t.image;
        if (t.name && t.image) map[t.name.toUpperCase()] = t.image;
      }
    }
    return map;
  }, [catalog]);

  const now = Date.now();
  const pastEvents = events.filter((e) => e.utcIso && new Date(e.utcIso).getTime() <= now);
  const currentEvent = pastEvents.length > 0 ? pastEvents[pastEvents.length - 1] : events[0];

  const upcomingEvents = events.filter((e) => e.utcIso && new Date(e.utcIso).getTime() > now);
  const displayUpcoming = upcomingEvents.length > 0 ? upcomingEvents.slice(0, 40) : events.slice(1, 41);
  const nextInRotation = displayUpcoming[0];

  // Only genuine bangers where isBanger is explicitly true
  const nextBanger = upcomingEvents.find((e) => e.isBanger);

  const formatRelativeTime = (utcIso?: string, rawTime?: string): string => {
    if (!utcIso) return rawTime || "Upcoming";
    const diffMs = new Date(utcIso).getTime() - Date.now();
    if (diffMs <= 0) return "Airing Now";
    const totalSec = Math.floor(diffMs / 1000);
    const hours = Math.floor(totalSec / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);
    const days = Math.floor(hours / 24);
    if (days > 0) return `in ${days}d ${hours % 24}h`;
    if (hours > 0) return `in ${hours}h ${mins}m`;
    return `in ${Math.max(1, mins)}m`;
  };

  const formatStartedTime = (utcIso?: string): string => {
    if (!utcIso) return "Airing Now";
    const started = new Date(utcIso).getTime();
    const diffMins = Math.floor((Date.now() - started) / 60000);
    if (diffMins < 0) return "Airing Now";
    if (diffMins < 60) return `Started ${diffMins}m ago`;
    const h = Math.floor(diffMins / 60);
    const m = diffMins % 60;
    return `Started ${h}h ${m}m ago`;
  };

  const getDayHeader = (utcIso?: string): string => {
    if (!utcIso) return "Upcoming Schedule";
    const date = new Date(utcIso);
    const nowDate = new Date();

    const dMidnight = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
    const nowMidnight = new Date(nowDate.getFullYear(), nowDate.getMonth(), nowDate.getDate()).getTime();
    const diffDays = Math.round((dMidnight - nowMidnight) / 86400000);

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Tomorrow";

    return date.toLocaleDateString([], {
      weekday: "long",
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  // Group upcoming events by calendar day
  const groupedUpcoming = useMemo(() => {
    const groups: { day: string; events: StreamEvent[] }[] = [];
    const map = new Map<string, StreamEvent[]>();

    for (const e of displayUpcoming) {
      const day = getDayHeader(e.utcIso);
      if (!map.has(day)) {
        const arr: StreamEvent[] = [];
        map.set(day, arr);
        groups.push({ day, events: arr });
      }
      map.get(day)!.push(e);
    }
    return groups;
  }, [displayUpcoming]);

  const t1Logo = currentEvent?.team1 ? teamLogos[currentEvent.team1.toUpperCase()] : undefined;
  const t2Logo = currentEvent?.team2 ? teamLogos[currentEvent.team2.toUpperCase()] : undefined;

  return (
    <div className="p-4 space-y-4 max-w-4xl mx-auto overflow-y-auto h-full select-none">
      {/* 24/7 Broadcast Hero Card */}
      <div className="bg-[#0a1420] border border-[#0ac8b9] rounded-lg p-5 shadow-xl relative overflow-hidden">
        {/* Top Badges */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="bg-[#0ac8b9] text-[#091428] font-bold text-xs px-2.5 py-0.5 rounded flex items-center gap-1.5 shadow-sm">
              <Radio className="w-3.5 h-3.5 animate-pulse" />
              24/7 BROADCAST STREAM
            </span>
            {currentEvent?.isBanger && (
              <span className="bg-[#ff4655] text-white font-bold text-[10px] px-2 py-0.5 rounded flex items-center gap-1 shadow-sm">
                <Flame className="w-3 h-3 fill-current" />
                S-TIER BANGER
              </span>
            )}
          </div>
          <span className="text-xs text-[#0ac8b9] font-mono">
            {formatStartedTime(currentEvent?.utcIso)}
          </span>
        </div>

        {/* Current Matchup Hero */}
        <div className="mb-4">
          <div className="flex flex-wrap items-center gap-3 my-1">
            {currentEvent?.team1 && (
              <div className="flex items-center gap-2">
                {t1Logo ? (
                  <img src={t1Logo} alt="" className="w-8 h-8 object-contain" />
                ) : (
                  <div className="w-8 h-8 rounded bg-[#091428] border border-[#1e282d] flex items-center justify-center font-bold text-xs text-[#c8aa6e]">
                    {currentEvent.team1.slice(0, 3)}
                  </div>
                )}
                <span className="text-xl font-bold text-[#f0e6d2] tracking-wide">
                  {currentEvent.team1}
                </span>
              </div>
            )}

            {currentEvent?.team1 && currentEvent?.team2 && (
              <span className="text-sm font-semibold text-[#7e8e9f] px-1">vs</span>
            )}

            {currentEvent?.team2 && (
              <div className="flex items-center gap-2">
                {t2Logo ? (
                  <img src={t2Logo} alt="" className="w-8 h-8 object-contain" />
                ) : (
                  <div className="w-8 h-8 rounded bg-[#091428] border border-[#1e282d] flex items-center justify-center font-bold text-xs text-[#c8aa6e]">
                    {currentEvent.team2.slice(0, 3)}
                  </div>
                )}
                <span className="text-xl font-bold text-[#f0e6d2] tracking-wide">
                  {currentEvent.team2}
                </span>
              </div>
            )}

            {!currentEvent?.team1 && !currentEvent?.team2 && (
              <h1 className="text-xl font-bold text-[#f0e6d2]">
                {currentEvent ? currentEvent.name || "Broadcast Intermission" : "Tournament Marathon"}
              </h1>
            )}
          </div>

          <div className="text-xs text-[#c8aa6e] font-semibold mt-1">
            {currentEvent
              ? `${currentEvent.event} ${currentEvent.season} ${
                  currentEvent.stage ? `· ${currentEvent.stage}` : ""
                }`
              : "Continuous Uninterrupted Tournament Archives"}
          </div>
        </div>

        {/* Up Next in Rotation Teaser */}
        {nextInRotation && (
          <div className="bg-[#091428]/80 border border-[#1e282d] rounded px-3 py-2 mb-4 flex items-center justify-between text-xs">
            <span className="text-[#7e8e9f]">
              <strong className="text-[#0ac8b9]">Up Next:</strong>{" "}
              {nextInRotation.team1 && nextInRotation.team2
                ? `${nextInRotation.team1} vs ${nextInRotation.team2}`
                : nextInRotation.name || "Next Match"}{" "}
              <span className="text-[#536675]">
                ({nextInRotation.event} {nextInRotation.season}
                {nextInRotation.stage ? ` · ${nextInRotation.stage}` : ""})
              </span>
            </span>
            <span className="font-mono text-[#0ac8b9] font-medium shrink-0 ml-2">
              {formatRelativeTime(nextInRotation.utcIso, nextInRotation.rawTime)}
            </span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => onOpenUrl("https://www.twitch.tv/LoLWorldChampionship")}
            className="flex items-center gap-2 px-4 py-2 rounded bg-[#9146ff] hover:bg-[#a970ff] text-white font-bold text-xs transition-colors shadow-md"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Watch on Twitch</span>
          </button>
          <button
            onClick={() => onOpenUrl("https://www.youtube.com/@LoLWorldChampionships/live")}
            className="flex items-center gap-2 px-4 py-2 rounded bg-[#cc0000] hover:bg-[#e60000] text-white font-bold text-xs transition-colors shadow-md"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Watch on YouTube</span>
          </button>
          <button
            onClick={() => onOpenUrl("https://lolworlds.com")}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded bg-[#091428] hover:bg-[#121e2d] border border-[#1e282d] hover:border-[#c8aa6e] text-[#f0e6d2] text-xs transition-colors"
          >
            <span>Full Schedule on lolworlds.com</span>
            <ExternalLink className="w-3.5 h-3.5 text-[#7e8e9f]" />
          </button>
        </div>
      </div>

      {/* Next S-Tier Banger Banner (Only rendered if genuine banger exists) */}
      {nextBanger && (
        <div className="bg-[#1e131d] border border-[#ff4655] rounded-lg p-3.5 flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded bg-[#ff4655]/20 flex items-center justify-center text-[#ff4655] shrink-0">
              <Trophy className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[10px] font-bold text-[#ff4655] tracking-wider uppercase flex items-center gap-1.5">
                <Flame className="w-3 h-3 fill-current" />
                Upcoming S-Tier Banger
              </div>
              <div className="text-xs font-bold text-[#f0e6d2] mt-0.5">
                {nextBanger.team1 && nextBanger.team2
                  ? `${nextBanger.team1} vs ${nextBanger.team2}`
                  : nextBanger.name}{" "}
                · {nextBanger.event} {nextBanger.season}
                {nextBanger.stage ? ` · ${nextBanger.stage}` : ""}
              </div>
            </div>
          </div>
          <div className="text-right shrink-0">
            <div className="text-xs font-mono font-bold text-[#ff4655]">
              {formatRelativeTime(nextBanger.utcIso, nextBanger.rawTime)}
            </div>
            <div className="text-[10px] text-[#7e8e9f] font-mono mt-0.5">
              {nextBanger.utcIso
                ? new Date(nextBanger.utcIso).toLocaleTimeString([], {
                    hour: "numeric",
                    minute: "2-digit",
                  })
                : ""}
            </div>
          </div>
        </div>
      )}

      {/* Grouped Upcoming Marathon Schedule */}
      <div>
        <div className="flex items-center justify-between pb-2 border-b border-[#1e282d] mb-3">
          <h3 className="text-xs font-bold text-[#c8aa6e] uppercase tracking-wider flex items-center gap-2">
            <Calendar className="w-3.5 h-3.5 text-[#0ac8b9]" />
            Upcoming Marathon Schedule ({upcomingEvents.length > 0 ? upcomingEvents.length : displayUpcoming.length})
          </h3>
          <span className="text-[11px] text-[#7e8e9f]">
            Continuous 24/7 Playout Rotation
          </span>
        </div>

        <div className="space-y-4">
          {groupedUpcoming.map((group) => (
            <div key={group.day} className="space-y-2">
              {/* Day Header Banner */}
              <div className="flex items-center gap-2 px-1 pt-1">
                <span className="text-xs font-bold text-[#0ac8b9] uppercase tracking-wider">
                  {group.day}
                </span>
                <div className="flex-1 h-px bg-[#1e282d]" />
                <span className="text-[10px] text-[#7e8e9f]">
                  {group.events.length} {group.events.length === 1 ? "match" : "matches"}
                </span>
              </div>

              {/* Day Match Rows */}
              <div className="space-y-1.5">
                {group.events.map((e, idx) => {
                  const isFollowed =
                    (e.team1 && settings.followedTeams.includes(e.team1)) ||
                    (e.team2 && settings.followedTeams.includes(e.team2));

                  const m1Logo = e.team1 ? teamLogos[e.team1.toUpperCase()] : undefined;
                  const m2Logo = e.team2 ? teamLogos[e.team2.toUpperCase()] : undefined;

                  const localTime = e.utcIso
                    ? new Date(e.utcIso).toLocaleTimeString([], {
                        hour: "numeric",
                        minute: "2-digit",
                      })
                    : "--:--";

                  return (
                    <div
                      key={idx}
                      className={`flex items-center justify-between px-3.5 py-2.5 rounded-lg border transition-all ${
                        isFollowed
                          ? "bg-[#101923] border-[#c8aa6e]/70 shadow-sm"
                          : "bg-[#0a1420] border-[#1e282d] hover:border-[#0ac8b9]/60"
                      }`}
                    >
                      {/* Left: Timing */}
                      <div className="w-28 shrink-0">
                        <div className="font-mono text-xs font-bold text-[#0ac8b9]">
                          {localTime}
                        </div>
                        <div className="text-[10px] text-[#7e8e9f] font-mono mt-0.5">
                          {formatRelativeTime(e.utcIso, e.rawTime)}
                        </div>
                      </div>

                      {/* Center: Matchup & Details */}
                      <div className="flex-1 min-w-0 px-3">
                        <div className="flex items-center gap-2 flex-wrap">
                          {e.team1 ? (
                            <div className="flex items-center gap-1.5">
                              {m1Logo ? (
                                <img src={m1Logo} alt="" className="w-4 h-4 object-contain" />
                              ) : (
                                <span className="w-4 h-4 rounded bg-[#091428] text-[9px] font-bold text-[#c8aa6e] flex items-center justify-center">
                                  {e.team1.slice(0, 2)}
                                </span>
                              )}
                              <span
                                className={`text-xs font-bold ${
                                  settings.followedTeams.includes(e.team1)
                                    ? "text-[#c8aa6e]"
                                    : "text-[#f0e6d2]"
                                }`}
                              >
                                {e.team1}
                              </span>
                            </div>
                          ) : (
                            <span className="text-xs font-semibold text-[#f0e6d2]">
                              {e.name || "Broadcast Segment"}
                            </span>
                          )}

                          {e.team1 && e.team2 && (
                            <span className="text-[11px] text-[#7e8e9f] font-medium">vs</span>
                          )}

                          {e.team2 && (
                            <div className="flex items-center gap-1.5">
                              {m2Logo ? (
                                <img src={m2Logo} alt="" className="w-4 h-4 object-contain" />
                              ) : (
                                <span className="w-4 h-4 rounded bg-[#091428] text-[9px] font-bold text-[#c8aa6e] flex items-center justify-center">
                                  {e.team2.slice(0, 2)}
                                </span>
                              )}
                              <span
                                className={`text-xs font-bold ${
                                  settings.followedTeams.includes(e.team2)
                                    ? "text-[#c8aa6e]"
                                    : "text-[#f0e6d2]"
                                }`}
                              >
                                {e.team2}
                              </span>
                            </div>
                          )}
                        </div>

                        {/* Tournament Stage Subtitle */}
                        <div className="text-[11px] text-[#7e8e9f] truncate mt-0.5">
                          {e.event} {e.season} {e.stage ? `· ${e.stage}` : ""}
                        </div>
                      </div>

                      {/* Right: Badges */}
                      <div className="flex items-center gap-1.5 shrink-0">
                        {isFollowed && (
                          <span className="text-[10px] font-bold text-[#c8aa6e] bg-[#c8aa6e]/10 border border-[#c8aa6e]/30 px-2 py-0.5 rounded flex items-center gap-1">
                            <Star className="w-3 h-3 fill-current" />
                            FOLLOWED
                          </span>
                        )}
                        {e.isBanger && (
                          <span className="text-[10px] font-bold text-white bg-[#ff4655] px-2 py-0.5 rounded flex items-center gap-1 shadow-sm">
                            <Flame className="w-3 h-3 fill-current" />
                            BANGER
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
