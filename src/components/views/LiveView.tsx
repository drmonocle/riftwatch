import React, { useState, useEffect } from "react";
import { Match, AppSettings } from "../../types";
import { Tv, ExternalLink, Calendar, Clock, ChevronRight } from "lucide-react";

interface LiveViewProps {
  matches: Match[];
  schedule: Match[];
  settings: AppSettings;
  onOpenUrl: (url: string) => void;
  onSelectTab: (tab: any) => void;
}

// Live ticking countdown hook
function useCountdown(utcDateStr?: string) {
  const [timeLeft, setTimeLeft] = useState<{
    hours: number;
    minutes: number;
    seconds: number;
    isPast: boolean;
    formatted: string;
  }>({ hours: 0, minutes: 0, seconds: 0, isPast: false, formatted: "" });

  useEffect(() => {
    if (!utcDateStr) return;

    const calc = () => {
      const target = new Date(utcDateStr).getTime();
      const now = Date.now();
      const diff = target - now;

      if (isNaN(target)) {
        setTimeLeft({ hours: 0, minutes: 0, seconds: 0, isPast: false, formatted: "Scheduled" });
        return;
      }

      if (diff <= 0) {
        setTimeLeft({ hours: 0, minutes: 0, seconds: 0, isPast: true, formatted: "Starting momentarily" });
        return;
      }

      const totalSec = Math.floor(diff / 1000);
      const hours = Math.floor(totalSec / 3600);
      const minutes = Math.floor((totalSec % 3600) / 60);
      const seconds = totalSec % 60;

      let str = "";
      if (hours > 24) {
        const days = Math.floor(hours / 24);
        const remHours = hours % 24;
        str = `Starts in ${days}d ${remHours}h ${minutes}m`;
      } else if (hours > 0) {
        str = `Starts in ${hours}h ${minutes}m ${seconds}s`;
      } else {
        str = `Starts in ${minutes}m ${seconds}s`;
      }

      setTimeLeft({ hours, minutes, seconds, isPast: false, formatted: str });
    };

    calc();
    const interval = setInterval(calc, 1000);
    return () => clearInterval(interval);
  }, [utcDateStr]);

  return timeLeft;
}

function formatMatchTime(iso: string): string {
  try {
    const d = new Date(iso);
    const today = new Date();
    const isToday =
      d.getDate() === today.getDate() &&
      d.getMonth() === today.getMonth() &&
      d.getFullYear() === today.getFullYear();

    const timeStr = d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    if (isToday) return `Today at ${timeStr}`;

    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);
    const isTomorrow =
      d.getDate() === tomorrow.getDate() &&
      d.getMonth() === tomorrow.getMonth() &&
      d.getFullYear() === tomorrow.getFullYear();

    if (isTomorrow) return `Tomorrow at ${timeStr}`;

    return `${d.toLocaleDateString([], { month: "short", day: "numeric" })} at ${timeStr}`;
  } catch {
    return iso;
  }
}

export const LiveView: React.FC<LiveViewProps> = ({
  matches,
  schedule,
  settings,
  onOpenUrl,
  onSelectTab,
}) => {
  // If no live matches, find next upcoming match based on watchlist priority
  const unstarted = schedule.filter((m) => m.state === "unstarted" || !m.state);

  // 1. Followed team priority
  let nextMatch: Match | undefined = unstarted.find(
    (m) =>
      settings.followedTeams.includes(m.team1Code) ||
      settings.followedTeams.includes(m.team2Code)
  );
  let nextTag = "Next match you follow";

  // 2. Followed league priority
  if (!nextMatch) {
    nextMatch = unstarted.find(
      (m) =>
        settings.followedLeagues.includes(m.leagueSlug) ||
        settings.followedLeagues.includes(m.leagueName.toLowerCase())
    );
    nextTag = "Next match in your leagues";
  }

  // 3. Earliest match overall
  if (!nextMatch && unstarted.length > 0) {
    nextMatch = unstarted[0];
    nextTag = "Next pro match";
  }

  const countdown = useCountdown(nextMatch?.startTimeUtc);

  // Subsequent upcoming matches (next 4)
  const comingUp = unstarted
    .filter((m) => m.matchId !== nextMatch?.matchId)
    .filter(
      (m) =>
        settings.followedTeams.includes(m.team1Code) ||
        settings.followedTeams.includes(m.team2Code) ||
        settings.followedLeagues.includes(m.leagueSlug)
    )
    .slice(0, 4);

  // If pro matches are live right now
  if (matches.length > 0) {
    return (
      <div className="p-4 space-y-4 max-w-4xl mx-auto overflow-y-auto h-full">
        <div className="flex items-center justify-between pb-1 border-b border-[#1e282d]">
          <h2 className="text-xs font-bold text-[#e84057] uppercase tracking-wider flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#e84057] animate-ping" />
            Live Pro Matches ({matches.length})
          </h2>
          {settings.spoilerMode && (
            <span className="text-[10px] text-[#c8aa6e] bg-[#c8aa6e]/10 border border-[#c8aa6e]/30 px-2 py-0.5 rounded">
              SPOILER MODE ACTIVE
            </span>
          )}
        </div>

        <div className="grid gap-4">
          {matches.map((m) => {
            const isT1Followed = settings.followedTeams.includes(m.team1Code);
            const isT2Followed = settings.followedTeams.includes(m.team2Code);

            return (
              <div
                key={m.matchId}
                className={`bg-[#0a1420] border rounded-lg p-4 transition-all hover:border-[#c8aa6e] ${
                  isT1Followed || isT2Followed
                    ? "border-[#c8aa6e] shadow-lg shadow-[#c8aa6e]/5"
                    : "border-[#1e282d]"
                }`}
              >
                {/* Card Header: League & Best-of */}
                <div className="flex items-center justify-between text-xs text-[#7e8e9f] mb-3">
                  <span className="font-bold text-[#0ac8b9]">{m.leagueName}</span>
                  <span className="font-medium bg-[#091428] px-2 py-0.5 rounded border border-[#1e282d]">
                    Best of {m.bestOf}
                  </span>
                </div>

                {/* Match Scoreboard */}
                <div className="grid grid-cols-5 items-center gap-2 my-2">
                  {/* Team 1 */}
                  <div className="col-span-2 flex items-center justify-end gap-3 text-right">
                    <div>
                      <div className="font-bold text-base text-[#f0e6d2]">{m.team1Name}</div>
                      <div className="text-[11px] text-[#7e8e9f] font-mono">{m.team1Code}</div>
                    </div>
                    {m.team1Image ? (
                      <img src={m.team1Image} alt={m.team1Code} className="w-10 h-10 object-contain rounded" />
                    ) : (
                      <div className="w-10 h-10 bg-[#091428] rounded flex items-center justify-center font-bold text-xs text-[#c8aa6e]">
                        {m.team1Code.slice(0, 3)}
                      </div>
                    )}
                  </div>

                  {/* Score Center */}
                  <div className="col-span-1 text-center font-bold font-mono">
                    {settings.spoilerMode ? (
                      <div className="text-xs text-[#7e8e9f] bg-[#091428] py-1 px-2 rounded border border-[#1e282d]">
                        VS
                      </div>
                    ) : (
                      <div className="text-2xl text-[#f0e6d2]">
                        <span className="text-[#0ac8b9]">{m.team1Score}</span>
                        <span className="text-[#7e8e9f] mx-2">:</span>
                        <span className="text-[#e84057]">{m.team2Score}</span>
                      </div>
                    )}
                  </div>

                  {/* Team 2 */}
                  <div className="col-span-2 flex items-center gap-3 text-left">
                    {m.team2Image ? (
                      <img src={m.team2Image} alt={m.team2Code} className="w-10 h-10 object-contain rounded" />
                    ) : (
                      <div className="w-10 h-10 bg-[#091428] rounded flex items-center justify-center font-bold text-xs text-[#c8aa6e]">
                        {m.team2Code.slice(0, 3)}
                      </div>
                    )}
                    <div>
                      <div className="font-bold text-base text-[#f0e6d2]">{m.team2Name}</div>
                      <div className="text-[11px] text-[#7e8e9f] font-mono">{m.team2Code}</div>
                    </div>
                  </div>
                </div>

                {/* Action Footer */}
                <div className="flex items-center justify-between pt-3 mt-2 border-t border-[#1e282d]/60 text-xs">
                  <span className="flex items-center gap-1.5 text-[#e84057] font-semibold text-[11px]">
                    <span className="w-2 h-2 rounded-full bg-[#e84057] animate-ping" />
                    Match In Progress
                  </span>

                  <button
                    onClick={() => onOpenUrl(m.streamUrl || "https://lolesports.com")}
                    className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#0ac8b9] hover:bg-[#0ac8b9]/80 text-[#091428] font-bold text-xs transition-colors"
                  >
                    <Tv className="w-3.5 h-3.5" />
                    <span>Watch Stream</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // IDLE STATE: No matches live right now -> Show Next Match Hero with Live Countdown
  return (
    <div className="p-4 space-y-6 max-w-4xl mx-auto overflow-y-auto h-full">
      {/* Idle Notice Header */}
      <div className="text-center py-4 border-b border-[#1e282d]">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#0a1420] border border-[#1e282d] text-[#7e8e9f] text-xs mb-1">
          <Clock className="w-3.5 h-3.5 text-[#0ac8b9]" />
          <span>No pro matches are live right now</span>
        </div>
      </div>

      {/* Hero Next Match Card */}
      {nextMatch ? (
        <section className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-[#c8aa6e] uppercase tracking-wider">
              {nextTag}
            </span>
            <span className="text-[#7e8e9f]">
              {nextMatch.leagueName} {nextMatch.blockName ? `· ${nextMatch.blockName}` : ""}
            </span>
          </div>

          <div className="bg-[#0a1420] border border-[#c8aa6e] rounded-xl p-6 shadow-xl shadow-[#c8aa6e]/5 relative overflow-hidden">
            {/* Ambient Background Glow */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-[#c8aa6e]/5 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

            <div className="relative z-10 flex flex-col items-center text-center">
              {/* League & Format Badge */}
              <div className="flex items-center gap-2 text-xs text-[#7e8e9f] mb-4">
                <span className="font-semibold text-[#0ac8b9]">{nextMatch.leagueName}</span>
                <span>·</span>
                <span className="font-mono bg-[#091428] px-2 py-0.5 rounded border border-[#1e282d]">
                  Best of {nextMatch.bestOf}
                </span>
              </div>

              {/* Matchup Banner */}
              <div className="flex items-center justify-center gap-6 sm:gap-12 w-full my-2">
                {/* Team 1 */}
                <div className="flex flex-col items-center flex-1 max-w-[180px]">
                  {nextMatch.team1Image ? (
                    <img
                      src={nextMatch.team1Image}
                      alt={nextMatch.team1Code}
                      className="w-14 h-14 sm:w-16 sm:h-16 object-contain mb-2 drop-shadow-md"
                    />
                  ) : (
                    <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-xl bg-[#091428] border border-[#1e282d] flex items-center justify-center font-bold text-lg text-[#c8aa6e] mb-2 font-mono">
                      {nextMatch.team1Code.slice(0, 3)}
                    </div>
                  )}
                  <div className="font-bold text-base sm:text-lg text-[#f0e6d2] truncate w-full">
                    {nextMatch.team1Name}
                  </div>
                  <div className="text-xs text-[#7e8e9f] font-mono">{nextMatch.team1Code}</div>
                </div>

                {/* VS Center */}
                <div className="flex flex-col items-center">
                  <span className="text-xs font-bold text-[#7e8e9f] bg-[#091428] border border-[#1e282d] px-2.5 py-1 rounded-full uppercase tracking-widest font-mono">
                    VS
                  </span>
                </div>

                {/* Team 2 */}
                <div className="flex flex-col items-center flex-1 max-w-[180px]">
                  {nextMatch.team2Image ? (
                    <img
                      src={nextMatch.team2Image}
                      alt={nextMatch.team2Code}
                      className="w-14 h-14 sm:w-16 sm:h-16 object-contain mb-2 drop-shadow-md"
                    />
                  ) : (
                    <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-xl bg-[#091428] border border-[#1e282d] flex items-center justify-center font-bold text-lg text-[#c8aa6e] mb-2 font-mono">
                      {nextMatch.team2Code.slice(0, 3)}
                    </div>
                  )}
                  <div className="font-bold text-base sm:text-lg text-[#f0e6d2] truncate w-full">
                    {nextMatch.team2Name}
                  </div>
                  <div className="text-xs text-[#7e8e9f] font-mono">{nextMatch.team2Code}</div>
                </div>
              </div>

              {/* Live Ticking Countdown */}
              <div className="mt-5 pt-4 border-t border-[#1e282d]/80 w-full flex flex-col items-center">
                <div className="text-xl sm:text-2xl font-extrabold text-[#0ac8b9] font-mono tracking-tight animate-pulse">
                  {countdown.formatted || "Calculating…"}
                </div>
                <div className="text-xs text-[#7e8e9f] mt-1 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-[#c8aa6e]" />
                  <span>{formatMatchTime(nextMatch.startTimeUtc)}</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      ) : (
        <div className="text-center py-8 text-[#7e8e9f] text-xs">
          No upcoming matches found in current schedule window.
        </div>
      )}

      {/* Coming Up Next (followed upcoming matches) */}
      {comingUp.length > 0 && (
        <section className="space-y-2">
          <h3 className="text-xs font-bold text-[#7e8e9f] uppercase tracking-wider">
            Coming Up Next
          </h3>
          <div className="grid gap-2">
            {comingUp.map((m) => (
              <div
                key={m.matchId}
                className="flex items-center justify-between p-3 rounded-lg bg-[#0a1420] border border-[#1e282d] hover:border-[#7e8e9f] transition-all text-xs"
              >
                <div className="flex items-center gap-3">
                  <span className="font-bold text-[#0ac8b9] text-[11px] w-20 truncate">
                    {m.leagueName}
                  </span>
                  <span className="text-[#f0e6d2] font-semibold">
                    {m.team1Name} vs {m.team2Name}
                  </span>
                  <span className="text-[#7e8e9f] text-[11px]">Bo{m.bestOf}</span>
                </div>
                <div className="text-[#7e8e9f] font-mono text-[11px]">
                  {formatMatchTime(m.startTimeUtc)}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Full Schedule Link */}
      <div className="flex justify-center pt-2 pb-6">
        <button
          onClick={() => onSelectTab("schedule")}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#c8aa6e] hover:bg-[#f0e6d2] text-[#091428] font-bold text-xs transition-colors shadow"
        >
          <span>View Full Schedule</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
