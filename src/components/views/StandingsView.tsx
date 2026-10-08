import React, { useState, useMemo } from "react";
import { Match, CatalogData, AppSettings } from "../../types";
import { computeLeagueStandings, TeamStanding } from "../../helpers";
import { Trophy, TrendingUp, Star, Search, Shield } from "lucide-react";

interface StandingsViewProps {
  schedule: Match[];
  settings: AppSettings;
  catalog?: CatalogData;
  onSelectTeam: (teamCode: string, teamName?: string) => void;
  onToggleTeamFollow?: (teamCode: string) => void;
}

export const StandingsView: React.FC<StandingsViewProps> = ({
  schedule,
  settings,
  catalog,
  onSelectTeam,
  onToggleTeamFollow,
}) => {
  // Extract distinct leagues available in completed matches
  const availableLeagues = useMemo(() => {
    const map = new Map<string, { slug: string; name: string }>();
    for (const m of schedule) {
      if (m.state === "completed" && m.leagueSlug) {
        const slug = m.leagueSlug.toLowerCase();
        if (!map.has(slug)) {
          map.set(slug, { slug, name: m.leagueName });
        }
      }
    }
    return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name));
  }, [schedule]);

  const [selectedLeague, setSelectedLeague] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");

  // Automatically select first available league if none selected or previous no longer available
  const activeLeague = useMemo(() => {
    if (selectedLeague && availableLeagues.some((l) => l.slug === selectedLeague)) {
      return selectedLeague;
    }
    return availableLeagues.length > 0 ? availableLeagues[0].slug : "";
  }, [selectedLeague, availableLeagues]);

  const standings = useMemo(() => {
    return computeLeagueStandings(activeLeague, schedule);
  }, [activeLeague, schedule]);

  const filtered = useMemo(() => {
    if (!searchQuery.trim()) return standings;
    const q = searchQuery.toLowerCase();
    return standings.filter(
      (s) => s.teamCode.toLowerCase().includes(q) || s.teamName.toLowerCase().includes(q)
    );
  }, [standings, searchQuery]);

  return (
    <div className="space-y-4 select-none">
      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#1e282d]">
        {/* League Selector Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto max-w-full pb-1 sm:pb-0 scrollbar-thin">
          {availableLeagues.map((l) => (
            <button
              key={l.slug}
              type="button"
              onClick={() => setSelectedLeague(l.slug)}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all whitespace-nowrap ${
                activeLeague === l.slug
                  ? "bg-[#c8aa6e] text-[#091428] font-bold shadow-md shadow-[#c8aa6e]/10"
                  : "bg-[#0a1420] text-[#9bb3c9] hover:text-[#f0e6d2] hover:bg-[#121e2d] border border-[#1e282d]"
              }`}
            >
              {l.name}
            </button>
          ))}
          {availableLeagues.length === 0 && (
            <span className="text-xs text-[#9bb3c9]">
              {schedule.length === 0 ? "Loading tournament schedule…" : "No completed tournament matches in current window"}
            </span>
          )}
        </div>

        {/* Search Input */}
        <div className="relative min-w-[180px]">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[#7e8e9f]" />
          <input
            type="text"
            placeholder="Search teams…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#0a0e17] border border-[#1e282d] rounded-lg pl-8 pr-3 py-1 text-xs text-[#f0e6d2] focus:border-[#c8aa6e] focus:outline-none"
          />
        </div>
      </div>

      {/* Standings Table Card */}
      <div className="bg-[#0a1420] border border-[#1e282d] rounded-xl overflow-hidden shadow-lg">
        {filtered.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#091428] border-b border-[#1e282d] text-[#9bb3c9] font-bold uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="py-3 px-4 w-12 text-center">#</th>
                  <th className="py-3 px-4">Team</th>
                  <th className="py-3 px-4 text-center">Series</th>
                  <th className="py-3 px-4 text-center">Games</th>
                  <th className="py-3 px-4 text-center">Diff</th>
                  <th className="py-3 px-4 text-center">Win%</th>
                  <th className="py-3 px-4 text-center">Streak</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1e282d]/60">
                {filtered.map((team, idx) => {
                  const isFollowed = settings.followedTeams.includes(team.teamCode);
                  const isTop3 = idx < 3;

                  return (
                    <tr
                      key={team.teamCode}
                      className={`hover:bg-[#121e2d]/60 transition-colors group ${
                        isFollowed ? "bg-[#c8aa6e]/5" : ""
                      }`}
                    >
                      {/* Rank Column */}
                      <td className="py-3 px-4 text-center font-bold font-mono">
                        {idx === 0 && (
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs">
                            1
                          </span>
                        )}
                        {idx === 1 && (
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-300/20 text-slate-200 border border-slate-300/40 text-xs">
                            2
                          </span>
                        )}
                        {idx === 2 && (
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber-700/20 text-amber-500 border border-amber-700/40 text-xs">
                            3
                          </span>
                        )}
                        {idx > 2 && (
                          <span className="text-[#9bb3c9]">{idx + 1}</span>
                        )}
                      </td>

                      {/* Team Logo & Name (Clickable to Roster) */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          {team.teamImage ? (
                            <img
                              src={team.teamImage}
                              alt={team.teamCode}
                              className="w-7 h-7 object-contain rounded shrink-0 cursor-pointer"
                              onClick={() => onSelectTeam(team.teamCode, team.teamName)}
                            />
                          ) : (
                            <div
                              onClick={() => onSelectTeam(team.teamCode, team.teamName)}
                              className="w-7 h-7 rounded bg-[#091428] border border-[#1e282d] flex items-center justify-center font-bold text-[10px] text-[#c8aa6e] shrink-0 cursor-pointer font-mono"
                            >
                              {team.teamCode.slice(0, 3)}
                            </div>
                          )}

                          <div className="flex items-center gap-1.5 min-w-0">
                            <span
                              onClick={() => onSelectTeam(team.teamCode, team.teamName)}
                              className="font-bold text-[#f0e6d2] group-hover:text-[#c8aa6e] transition-colors cursor-pointer truncate"
                              title="Click to view team roster"
                            >
                              {team.teamName}
                            </span>

                            {onToggleTeamFollow && (
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onToggleTeamFollow(team.teamCode);
                                }}
                                className={`p-1 rounded hover:bg-[#1e282d] transition-colors shrink-0 ${
                                  isFollowed ? "text-[#c8aa6e]" : "text-[#7e8e9f] hover:text-[#c8aa6e]"
                                }`}
                                title={isFollowed ? `Unfollow ${team.teamCode}` : `Follow ${team.teamCode}`}
                              >
                                <Star className={`w-3.5 h-3.5 ${isFollowed ? "fill-[#c8aa6e]" : ""}`} />
                              </button>
                            )}

                            <span className="text-[11px] font-mono text-[#9bb3c9]">
                              {team.teamCode}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Series Record (W-L) */}
                      <td className="py-3 px-4 text-center font-mono font-bold text-sm text-[#f0e6d2]">
                        <span className="text-emerald-400">{team.seriesWon}</span>
                        <span className="text-[#7e8e9f] mx-1">-</span>
                        <span className="text-rose-400">{team.seriesLost}</span>
                      </td>

                      {/* Games Record (W-L) */}
                      <td className="py-3 px-4 text-center font-mono text-xs text-[#9bb3c9]">
                        {team.gamesWon} - {team.gamesLost}
                      </td>

                      {/* Game Diff */}
                      <td className="py-3 px-4 text-center font-mono font-bold text-xs">
                        <span
                          className={
                            team.gameDiff > 0
                              ? "text-emerald-400"
                              : team.gameDiff < 0
                              ? "text-rose-400"
                              : "text-[#9bb3c9]"
                          }
                        >
                          {team.gameDiff > 0 ? `+${team.gameDiff}` : team.gameDiff}
                        </span>
                      </td>

                      {/* Win % */}
                      <td className="py-3 px-4 text-center font-mono font-semibold text-xs text-[#0ac8b9]">
                        {team.winRatePct}%
                      </td>

                      {/* Streak */}
                      <td className="py-3 px-4 text-center font-mono text-xs">
                        <span
                          className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                            team.streak.endsWith("W")
                              ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                              : team.streak.endsWith("L")
                              ? "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                              : "text-[#7e8e9f]"
                          }`}
                        >
                          {team.streak}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-[#9bb3c9] space-y-2">
            <Trophy className="w-8 h-8 text-[#c8aa6e]/40 mx-auto" />
            <p className="font-semibold text-[#f0e6d2]">No Standings Data Available</p>
            <p>
              Completed match results are required to calculate league standings. Select another league above or browse the schedule.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
