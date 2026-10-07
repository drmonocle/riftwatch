import React, { useState } from "react";
import { AppSettings, PlayerEntry } from "../../types";
import {
  MAJOR_REGIONS,
  DEFAULT_FOLLOWED_REGIONS,
  POPULAR_TEAMS,
  POPULAR_PLAYERS,
  GLOBAL_LEAGUES,
} from "../../api";
import { Search, Star, Check, Plus, X, Globe, User, Shield, Trophy } from "lucide-react";

interface WatchlistViewProps {
  settings: AppSettings;
  onUpdateSettings: (s: Partial<AppSettings>) => void;
}

type WatchlistSubTab = "teams" | "players" | "regions" | "leagues";

export const WatchlistView: React.FC<WatchlistViewProps> = ({ settings, onUpdateSettings }) => {
  const [tab, setTab] = useState<WatchlistSubTab>("teams");
  const [search, setSearch] = useState("");
  const [expandedTeam, setExpandedTeam] = useState<string | null>(null);

  // Toggle handlers (fast in-place updates)
  const toggleTeam = (code: string) => {
    const isFollowed = settings.followedTeams.includes(code);
    const next = isFollowed
      ? settings.followedTeams.filter((t) => t !== code)
      : [...settings.followedTeams, code];
    onUpdateSettings({ followedTeams: next });
  };

  const togglePlayer = (name: string) => {
    const isFollowed = settings.followedPlayers.includes(name);
    const next = isFollowed
      ? settings.followedPlayers.filter((p) => p !== name)
      : [...settings.followedPlayers, name];
    onUpdateSettings({ followedPlayers: next });
  };

  const toggleRegion = (code: string) => {
    const isFollowed = settings.followedRegions.includes(code);
    const next = isFollowed
      ? settings.followedRegions.filter((r) => r !== code)
      : [...settings.followedRegions, code];
    onUpdateSettings({ followedRegions: next });
  };

  const toggleLeague = (slug: string) => {
    const isFollowed = settings.followedLeagues.includes(slug);
    const next = isFollowed
      ? settings.followedLeagues.filter((l) => l !== slug)
      : [...settings.followedLeagues, slug];
    onUpdateSettings({ followedLeagues: next });
  };

  // Batch actions
  const followAllRegions = () => {
    onUpdateSettings({ followedRegions: [...DEFAULT_FOLLOWED_REGIONS] });
  };

  const unfollowAllRegions = () => {
    onUpdateSettings({ followedRegions: [] });
  };

  const followInternationalEvents = () => {
    const majors = ["worlds", "msi", "first_stand"];
    const merged = Array.from(new Set([...settings.followedLeagues, ...majors]));
    onUpdateSettings({ followedLeagues: merged });
  };

  // Filtered queries
  const q = search.trim().toLowerCase();

  const filteredTeams = POPULAR_TEAMS.filter((t) => {
    if (!q) return true;
    return t.code.toLowerCase().includes(q) || t.name.toLowerCase().includes(q) || t.league.toLowerCase().includes(q);
  });

  const filteredPlayers = POPULAR_PLAYERS.filter((p) => {
    if (!q) return true;
    return (
      p.name.toLowerCase().includes(q) ||
      p.teamCode.toLowerCase().includes(q) ||
      p.teamName.toLowerCase().includes(q) ||
      p.role.toLowerCase().includes(q) ||
      (p.realName && p.realName.toLowerCase().includes(q))
    );
  });

  const filteredRegions = MAJOR_REGIONS.filter((r) => {
    if (!q) return true;
    return (
      r.name.toLowerCase().includes(q) ||
      r.code.toLowerCase().includes(q) ||
      r.leagues.some((l) => l.toLowerCase().includes(q))
    );
  });

  const filteredLeagues = GLOBAL_LEAGUES.filter((l) => {
    if (!q) return true;
    return (
      l.name.toLowerCase().includes(q) ||
      l.slug.toLowerCase().includes(q) ||
      l.region.toLowerCase().includes(q)
    );
  });

  return (
    <div className="p-4 space-y-4 max-w-4xl mx-auto overflow-y-auto h-full select-none text-xs">
      {/* Following Summary Header */}
      <div className="p-3 rounded-lg bg-[#0a1420] border border-[#1e282d] space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-bold text-[#c8aa6e] uppercase tracking-wider text-[11px]">
              Active Watchlist
            </span>
            <span className="text-[#7e8e9f] text-[11px]">
              {settings.followedTeams.length} teams · {settings.followedPlayers.length} players ·{" "}
              {settings.followedRegions.length} regions · {settings.followedLeagues.length} leagues
            </span>
          </div>
        </div>

        {/* Quick-remove chips */}
        <div className="flex flex-wrap gap-1.5 pt-1">
          {settings.followedTeams.map((code) => (
            <span
              key={`chip-t-${code}`}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#091428] border border-[#c8aa6e]/40 text-[#c8aa6e] font-semibold text-[10px]"
            >
              <span>{code}</span>
              <button
                onClick={() => toggleTeam(code)}
                className="hover:text-white"
                title="Remove from watchlist"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}

          {settings.followedPlayers.map((name) => (
            <span
              key={`chip-p-${name}`}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#091428] border border-[#0ac8b9]/40 text-[#0ac8b9] font-semibold text-[10px]"
            >
              <span>{name}</span>
              <button
                onClick={() => togglePlayer(name)}
                className="hover:text-white"
                title="Remove from watchlist"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}

          {settings.followedRegions.length > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#091428] border border-[#7e8e9f]/40 text-[#f0e6d2] text-[10px]">
              <span>🌐 {settings.followedRegions.length} Regions</span>
            </span>
          )}
        </div>
      </div>

      {/* Sub-tab Navigation & Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#1e282d]">
        <div className="flex items-center gap-1 bg-[#0a0e17] p-1 rounded-lg border border-[#1e282d]">
          <button
            onClick={() => setTab("teams")}
            className={`flex items-center gap-1.5 px-3 py-1.5 font-semibold rounded transition-all ${
              tab === "teams" ? "bg-[#c8aa6e] text-[#091428]" : "text-[#7e8e9f] hover:text-[#f0e6d2]"
            }`}
          >
            <Shield className="w-3.5 h-3.5" />
            <span>Teams ({settings.followedTeams.length})</span>
          </button>

          <button
            onClick={() => setTab("players")}
            className={`flex items-center gap-1.5 px-3 py-1.5 font-semibold rounded transition-all ${
              tab === "players" ? "bg-[#c8aa6e] text-[#091428]" : "text-[#7e8e9f] hover:text-[#f0e6d2]"
            }`}
          >
            <User className="w-3.5 h-3.5" />
            <span>Players ({settings.followedPlayers.length})</span>
          </button>

          <button
            onClick={() => setTab("regions")}
            className={`flex items-center gap-1.5 px-3 py-1.5 font-semibold rounded transition-all ${
              tab === "regions" ? "bg-[#c8aa6e] text-[#091428]" : "text-[#7e8e9f] hover:text-[#f0e6d2]"
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Regions ({settings.followedRegions.length})</span>
          </button>

          <button
            onClick={() => setTab("leagues")}
            className={`flex items-center gap-1.5 px-3 py-1.5 font-semibold rounded transition-all ${
              tab === "leagues" ? "bg-[#c8aa6e] text-[#091428]" : "text-[#7e8e9f] hover:text-[#f0e6d2]"
            }`}
          >
            <Trophy className="w-3.5 h-3.5" />
            <span>Leagues ({settings.followedLeagues.length})</span>
          </button>
        </div>

        {/* Search input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-[#7e8e9f]" />
          <input
            type="text"
            placeholder={`Search ${tab}…`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#0a1420] border border-[#1e282d] rounded-lg pl-8 pr-3 py-1 text-xs text-[#f0e6d2] focus:outline-none focus:border-[#c8aa6e]"
          />
        </div>
      </div>

      {/* 1. TEAMS SUB-TAB */}
      {tab === "teams" && (
        <div className="space-y-3">
          <div className="text-[11px] text-[#7e8e9f]">
            Follow pro teams to prioritize their matches on the Live tab, get kickoff notifications, and surface in ticker alerts.
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {filteredTeams.map((team) => {
              const isFollowed = settings.followedTeams.includes(team.code);
              const isExpanded = expandedTeam === team.code;
              const roster = POPULAR_PLAYERS.filter((p) => p.teamCode === team.code);

              return (
                <div
                  key={team.code}
                  className={`rounded-lg border p-3 transition-all ${
                    isFollowed
                      ? "bg-[#0a1420] border-[#c8aa6e] text-[#f0e6d2]"
                      : "bg-[#091428] border-[#1e282d] text-[#7e8e9f] hover:border-[#7e8e9f]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-[#0a0e17] border border-[#1e282d] flex items-center justify-center font-bold font-mono text-xs text-[#c8aa6e]">
                        {team.code}
                      </div>
                      <div>
                        <div className="font-bold text-xs text-[#f0e6d2]">{team.name}</div>
                        <div className="text-[11px] text-[#7e8e9f]">{team.league}</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {roster.length > 0 && (
                        <button
                          onClick={() => setExpandedTeam(isExpanded ? null : team.code)}
                          className="px-2 py-1 rounded bg-[#091428] border border-[#1e282d] text-[10px] text-[#7e8e9f] hover:text-[#f0e6d2]"
                        >
                          {isExpanded ? "▲ Roster" : "▼ Roster"}
                        </button>
                      )}

                      <button
                        onClick={() => toggleTeam(team.code)}
                        className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
                          isFollowed
                            ? "bg-[#c8aa6e] text-[#091428]"
                            : "bg-[#0a0e17] border border-[#1e282d] text-[#7e8e9f] hover:text-[#f0e6d2]"
                        }`}
                      >
                        {isFollowed ? <Check className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                        <span>{isFollowed ? "Following" : "Follow"}</span>
                      </button>
                    </div>
                  </div>

                  {/* Expanded Roster Preview */}
                  {isExpanded && roster.length > 0 && (
                    <div className="mt-2.5 pt-2.5 border-t border-[#1e282d] space-y-1">
                      <div className="text-[10px] text-[#7e8e9f] uppercase tracking-wider mb-1">
                        Active Roster
                      </div>
                      {roster.map((p) => (
                        <div key={p.name} className="flex items-center justify-between text-[11px] py-0.5">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono px-1 rounded bg-[#0a0e17] text-[#0ac8b9] w-12 text-center">
                              {p.role}
                            </span>
                            <span className="text-[#f0e6d2] font-semibold">{p.name}</span>
                            {p.realName && <span className="text-[#7e8e9f]">({p.realName})</span>}
                          </div>
                          <button
                            onClick={() => togglePlayer(p.name)}
                            className="text-[10px] text-[#c8aa6e] hover:underline"
                          >
                            {settings.followedPlayers.includes(p.name) ? "★ Following" : "☆ Follow"}
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 2. PLAYERS SUB-TAB */}
      {tab === "players" && (
        <div className="space-y-3">
          <div className="text-[11px] text-[#7e8e9f]">
            Follow individual pro players (Faker, Chovy, Caps, etc.) to trigger alerts whenever they take the stage.
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {filteredPlayers.map((player) => {
              const isFollowed = settings.followedPlayers.includes(player.name);

              return (
                <div
                  key={player.name}
                  onClick={() => togglePlayer(player.name)}
                  className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all ${
                    isFollowed
                      ? "bg-[#0a1420] border-[#0ac8b9] text-[#f0e6d2]"
                      : "bg-[#091428] border-[#1e282d] text-[#7e8e9f] hover:border-[#7e8e9f]"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-[#0a0e17] border border-[#1e282d] text-[#0ac8b9] w-14 text-center">
                      {player.role}
                    </span>
                    <div>
                      <div className="font-bold text-xs text-[#f0e6d2] flex items-center gap-1.5">
                        <span>{player.name}</span>
                        {player.realName && (
                          <span className="text-[10px] font-normal text-[#7e8e9f]">
                            · {player.realName}
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-[#7e8e9f]">
                        {player.teamName} ({player.teamCode})
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      togglePlayer(player.name);
                    }}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
                      isFollowed
                        ? "bg-[#0ac8b9] text-[#091428]"
                        : "bg-[#0a0e17] border border-[#1e282d] text-[#7e8e9f] hover:text-[#f0e6d2]"
                    }`}
                  >
                    {isFollowed ? <Check className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                    <span>{isFollowed ? "Following" : "Follow"}</span>
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 3. REGIONS SUB-TAB */}
      {tab === "regions" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-[11px] text-[#7e8e9f]">
              Follow competitive ecosystems to track all tournaments and league games in those regions. All 7 regions default selected.
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={followAllRegions}
                className="px-2.5 py-1 rounded bg-[#0a1420] border border-[#c8aa6e] text-[#c8aa6e] hover:bg-[#c8aa6e] hover:text-[#091428] font-semibold text-[11px] transition-colors"
              >
                ★ Follow All
              </button>
              <button
                onClick={unfollowAllRegions}
                className="px-2.5 py-1 rounded bg-[#0a1420] border border-[#1e282d] text-[#7e8e9f] hover:text-[#e84057] font-semibold text-[11px] transition-colors"
              >
                Unfollow All
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {filteredRegions.map((region) => {
              const isFollowed = settings.followedRegions.includes(region.code);

              return (
                <div
                  key={region.code}
                  onClick={() => toggleRegion(region.code)}
                  className={`flex items-center justify-between p-3.5 rounded-lg border cursor-pointer transition-all ${
                    isFollowed
                      ? "bg-[#0a1420] border-[#c8aa6e] text-[#f0e6d2]"
                      : "bg-[#091428] border-[#1e282d] text-[#7e8e9f] hover:border-[#7e8e9f]"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{region.badge}</span>
                    <div>
                      <div className="font-bold text-xs text-[#f0e6d2]">{region.name}</div>
                      <div className="text-[10px] text-[#7e8e9f]">
                        {region.leagues.join(" · ")}
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleRegion(region.code);
                    }}
                    className={`flex items-center gap-1 px-3 py-1 rounded text-xs font-semibold transition-colors ${
                      isFollowed
                        ? "bg-[#c8aa6e] text-[#091428]"
                        : "bg-[#0a0e17] border border-[#1e282d] text-[#7e8e9f] hover:text-[#f0e6d2]"
                    }`}
                  >
                    {isFollowed ? <Check className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                    <span>{isFollowed ? "Following" : "Follow"}</span>
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. LEAGUES SUB-TAB */}
      {tab === "leagues" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-[11px] text-[#7e8e9f]">
              Matches from followed leagues appear in filtered schedule and live displays.
            </div>
            <button
              onClick={followInternationalEvents}
              className="px-2.5 py-1 rounded bg-[#0a1420] border border-[#0ac8b9] text-[#0ac8b9] hover:bg-[#0ac8b9] hover:text-[#091428] font-semibold text-[11px] transition-colors"
            >
              ★ Follow International Events
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {filteredLeagues.map((league) => {
              const isFollowed = settings.followedLeagues.includes(league.slug);

              return (
                <div
                  key={league.slug}
                  onClick={() => toggleLeague(league.slug)}
                  className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all ${
                    isFollowed
                      ? "bg-[#0a1420] border-[#c8aa6e] text-[#f0e6d2]"
                      : "bg-[#091428] border-[#1e282d] text-[#7e8e9f] hover:border-[#7e8e9f]"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-[#0a0e17] border border-[#1e282d] flex items-center justify-center font-bold text-xs text-[#0ac8b9]">
                      <Trophy className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-semibold text-xs text-[#f0e6d2]">{league.name}</div>
                      <div className="text-[10px] text-[#7e8e9f] uppercase">{league.region}</div>
                    </div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleLeague(league.slug);
                    }}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
                      isFollowed
                        ? "bg-[#c8aa6e] text-[#091428]"
                        : "bg-[#0a0e17] border border-[#1e282d] text-[#7e8e9f] hover:text-[#f0e6d2]"
                    }`}
                  >
                    {isFollowed ? <Check className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                    <span>{isFollowed ? "Following" : "Follow"}</span>
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
