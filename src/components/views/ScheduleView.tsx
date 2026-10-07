import React, { useState } from "react";
import { Match, AppSettings } from "../../types";
import { Search, Calendar, Star } from "lucide-react";

interface ScheduleViewProps {
  schedule: Match[];
  settings: AppSettings;
  onOpenUrl: (url: string) => void;
  onUpdateSettings?: (s: Partial<AppSettings>) => void;
}

export const ScheduleView: React.FC<ScheduleViewProps> = ({
  schedule,
  settings,
  onOpenUrl,
  onUpdateSettings,
}) => {
  const [filterRange, setFilterRange] = useState<"today" | "upcoming" | "results">(() => {
    const today = new Date().toDateString();
    const hasTodayMatches = schedule.some((m) => {
      if (!m.startTimeUtc) return false;
      return new Date(m.startTimeUtc).toDateString() === today;
    });
    return hasTodayMatches ? "today" : "upcoming";
  });
  const [followedOnly, setFollowedOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [revealedMatchIds, setRevealedMatchIds] = useState<Record<string, boolean>>({});

  const toggleReveal = (matchId: string) => {
    setRevealedMatchIds((prev) => ({ ...prev, [matchId]: !prev[matchId] }));
  };

  const toggleTeamFollow = (code: string) => {
    if (!onUpdateSettings || !code) return;
    const isFollowed = settings.followedTeams.includes(code);
    const next = isFollowed
      ? settings.followedTeams.filter((t) => t !== code)
      : [...settings.followedTeams, code];
    onUpdateSettings({ followedTeams: next });
  };

  const now = new Date();
  const todayStr = now.toDateString();

  // Filter matches
  const filtered = schedule.filter((m) => {
    const matchDate = m.startTimeUtc ? new Date(m.startTimeUtc) : null;

    // Range filter
    if (filterRange === "today") {
      if (!matchDate || matchDate.toDateString() !== todayStr) return false;
    } else if (filterRange === "upcoming") {
      if (!matchDate || m.state === "completed" || matchDate < now) return false;
    } else if (filterRange === "results") {
      if (m.state !== "completed") return false;
    }

    // Followed only
    if (followedOnly) {
      const isFollowed =
        settings.followedTeams.includes(m.team1Code) ||
        settings.followedTeams.includes(m.team2Code) ||
        settings.followedLeagues.includes(m.leagueSlug);
      if (!isFollowed) return false;
    }

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const text = `${m.team1Code} ${m.team1Name} ${m.team2Code} ${m.team2Name} ${m.leagueName}`.toLowerCase();
      if (!text.includes(q)) return false;
    }

    return true;
  });

  return (
    <div className="p-4 space-y-4 max-w-4xl mx-auto overflow-y-auto h-full select-none">
      {/* Filters & Search Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#1e282d]">
        {/* Range Buttons */}
        <div className="flex items-center gap-1 bg-[#0a0e17] p-1 rounded border border-[#1e282d]">
          {(["today", "upcoming", "results"] as const).map((r) => (
            <button
              key={r}
              onClick={() => setFilterRange(r)}
              className={`px-3 py-1 text-xs font-semibold rounded transition-all capitalize ${
                filterRange === r
                  ? "bg-[#c8aa6e] text-[#091428]"
                  : "text-[#7e8e9f] hover:text-[#f0e6d2] hover:bg-[#121e2d]"
              }`}
            >
              {r}
            </button>
          ))}
        </div>

        {/* Search & Followed Toggle */}
        <div className="flex items-center gap-2 flex-1 max-w-xs justify-end">
          <button
            onClick={() => setFollowedOnly(!followedOnly)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs border transition-colors ${
              followedOnly
                ? "bg-[#c8aa6e]/20 border-[#c8aa6e] text-[#c8aa6e]"
                : "bg-[#0a1420] border-[#1e282d] text-[#7e8e9f] hover:text-[#f0e6d2]"
            }`}
            title="Filter by your followed teams and leagues"
          >
            <Star className={`w-3.5 h-3.5 ${followedOnly ? "fill-current" : ""}`} />
            <span>Followed only</span>
          </button>

          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-[#7e8e9f]" />
            <input
              type="text"
              placeholder="Search team or league…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#0a1420] border border-[#1e282d] rounded pl-8 pr-3 py-1 text-xs text-[#f0e6d2] focus:outline-none focus:border-[#c8aa6e]"
            />
          </div>
        </div>
      </div>

      {/* Match Rows */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 text-[#7e8e9f] text-xs">
          No scheduled matches match your active filters. Try switching tabs or turning off "Followed only".
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((m) => {
            const timeStr = m.startTimeUtc
              ? new Date(m.startTimeUtc).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
              : "--:--";

            const isT1Followed = settings.followedTeams.includes(m.team1Code);
            const isT2Followed = settings.followedTeams.includes(m.team2Code);
            const isRevealed = !!revealedMatchIds[m.matchId];
            const showScore = m.state === "completed" && (!settings.spoilerMode || isRevealed);

            return (
              <div
                key={m.matchId}
                className="flex items-center justify-between bg-[#0a1420] border border-[#1e282d] hover:border-[#c8aa6e] px-4 py-2.5 rounded transition-all"
              >
                {/* Time & League */}
                <div className="flex items-center gap-3 w-36">
                  <span className="font-mono text-xs text-[#0ac8b9] font-bold">{timeStr}</span>
                  <span className="text-[11px] text-[#7e8e9f] truncate">{m.leagueName}</span>
                </div>

                {/* Teams & Score */}
                <div className="flex items-center justify-center gap-4 flex-1">
                  {/* Team 1 */}
                  <div className="flex items-center gap-1.5 w-36 justify-end text-right">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleTeamFollow(m.team1Code);
                      }}
                      className={`p-0.5 rounded hover:bg-[#1e282d] transition-colors shrink-0 ${
                        isT1Followed ? "text-[#c8aa6e]" : "text-[#7e8e9f] hover:text-[#c8aa6e]"
                      }`}
                      title={isT1Followed ? `Unfollow ${m.team1Code}` : `Follow ${m.team1Code}`}
                    >
                      <Star className={`w-3.5 h-3.5 ${isT1Followed ? "fill-[#c8aa6e]" : ""}`} />
                    </button>
                    <span className="text-xs font-bold text-[#f0e6d2]">{m.team1Code}</span>
                    {m.team1Image && <img src={m.team1Image} alt="" className="w-5 h-5 object-contain" />}
                  </div>

                  {/* Score / VS Center with Per-Match Reveal */}
                  <div className="font-mono font-bold text-xs px-2 flex items-center justify-center min-w-[70px]">
                    {showScore ? (
                      <div
                        onClick={() => settings.spoilerMode && toggleReveal(m.matchId)}
                        className={`text-xs ${
                          settings.spoilerMode
                            ? "cursor-pointer hover:text-[#c8aa6e] bg-[#091428] px-2 py-0.5 rounded border border-[#1e282d]"
                            : ""
                        }`}
                        title={settings.spoilerMode ? "Click to re-hide score" : undefined}
                      >
                        <span className="text-[#f0e6d2]">
                          {m.team1Score} : {m.team2Score}
                        </span>
                      </div>
                    ) : m.state === "completed" && settings.spoilerMode ? (
                      <button
                        type="button"
                        onClick={() => toggleReveal(m.matchId)}
                        className="text-[11px] px-2 py-0.5 rounded bg-[#091428] border border-[#1e282d] text-[#7e8e9f] hover:text-[#c8aa6e] hover:border-[#c8aa6e]/60 transition-colors cursor-pointer"
                        title="Click to reveal final score"
                      >
                        Reveal
                      </button>
                    ) : (
                      <span className="text-[#7e8e9f]">VS</span>
                    )}
                  </div>

                  {/* Team 2 */}
                  <div className="flex items-center gap-1.5 w-36 justify-start text-left">
                    {m.team2Image && <img src={m.team2Image} alt="" className="w-5 h-5 object-contain" />}
                    <span className="text-xs font-bold text-[#f0e6d2]">{m.team2Code}</span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleTeamFollow(m.team2Code);
                      }}
                      className={`p-0.5 rounded hover:bg-[#1e282d] transition-colors shrink-0 ${
                        isT2Followed ? "text-[#c8aa6e]" : "text-[#7e8e9f] hover:text-[#c8aa6e]"
                      }`}
                      title={isT2Followed ? `Unfollow ${m.team2Code}` : `Follow ${m.team2Code}`}
                    >
                      <Star className={`w-3.5 h-3.5 ${isT2Followed ? "fill-[#c8aa6e]" : ""}`} />
                    </button>
                  </div>
                </div>

                {/* Status / Best Of */}
                <div className="flex items-center gap-2 w-28 justify-end">
                  <span className="text-[10px] text-[#7e8e9f] bg-[#091428] px-2 py-0.5 rounded border border-[#1e282d]">
                    Bo{m.bestOf}
                  </span>
                  {m.state === "completed" ? (
                    <span className="text-[10px] text-[#7e8e9f] font-semibold">FINAL</span>
                  ) : (
                    <span className="text-[10px] text-[#c8aa6e] font-semibold">UPCOMING</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
