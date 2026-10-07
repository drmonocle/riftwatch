import React, { useState } from "react";
import { AppSettings } from "../../types";
import { Search, Star, Check, Plus, Globe } from "lucide-react";

interface WatchlistViewProps {
  settings: AppSettings;
  onUpdateSettings: (s: Partial<AppSettings>) => void;
}

// Popular Pro Teams Directory
const POPULAR_TEAMS = [
  { code: "T1", name: "T1", league: "LCK" },
  { code: "GEN", name: "Gen.G", league: "LCK" },
  { code: "HLE", name: "Hanwha Life Esports", league: "LCK" },
  { code: "DK", name: "Dplus KIA", league: "LCK" },
  { code: "BLG", name: "Bilibili Gaming", league: "LPL" },
  { code: "TES", name: "Top Esports", league: "LPL" },
  { code: "WBG", name: "Weibo Gaming", league: "LPL" },
  { code: "JDG", name: "JD Gaming", league: "LPL" },
  { code: "G2", name: "G2 Esports", league: "LEC" },
  { code: "FNC", name: "Fnatic", league: "LEC" },
  { code: "KC", name: "Karmine Corp", league: "LEC" },
  { code: "FLY", name: "FlyQuest", league: "LCS" },
  { code: "TL", name: "Team Liquid", league: "LCS" },
  { code: "C9", name: "Cloud9", league: "LCS" },
];

const LEAGUES = [
  { slug: "worlds", name: "Worlds Championship", region: "International" },
  { slug: "msi", name: "Mid-Season Invitational", region: "International" },
  { slug: "first_stand", name: "First Stand", region: "International" },
  { slug: "lck", name: "LCK (Korea)", region: "Korea" },
  { slug: "lpl", name: "LPL (China)", region: "China" },
  { slug: "lec", name: "LEC (EMEA)", region: "EMEA" },
  { slug: "lcs", name: "LCS (North America)", region: "North America" },
];

export const WatchlistView: React.FC<WatchlistViewProps> = ({ settings, onUpdateSettings }) => {
  const [tab, setTab] = useState<"teams" | "leagues">("teams");
  const [search, setSearch] = useState("");

  const toggleTeam = (code: string) => {
    const next = settings.followedTeams.includes(code)
      ? settings.followedTeams.filter((t) => t !== code)
      : [...settings.followedTeams, code];
    onUpdateSettings({ followedTeams: next });
  };

  const toggleLeague = (slug: string) => {
    const next = settings.followedLeagues.includes(slug)
      ? settings.followedLeagues.filter((l) => l !== slug)
      : [...settings.followedLeagues, slug];
    onUpdateSettings({ followedLeagues: next });
  };

  const filteredTeams = POPULAR_TEAMS.filter((t) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return t.code.toLowerCase().includes(q) || t.name.toLowerCase().includes(q) || t.league.toLowerCase().includes(q);
  });

  const filteredLeagues = LEAGUES.filter((l) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return l.name.toLowerCase().includes(q) || l.region.toLowerCase().includes(q);
  });

  return (
    <div className="p-4 space-y-4 max-w-4xl mx-auto overflow-y-auto h-full select-none">
      {/* Category selector & search */}
      <div className="flex items-center justify-between gap-4 pb-3 border-b border-[#1e282d]">
        <div className="flex items-center gap-1 bg-[#0a0e17] p-1 rounded border border-[#1e282d]">
          <button
            onClick={() => setTab("teams")}
            className={`px-3 py-1 text-xs font-semibold rounded transition-all ${
              tab === "teams" ? "bg-[#c8aa6e] text-[#091428]" : "text-[#7e8e9f] hover:text-[#f0e6d2]"
            }`}
          >
            Teams ({settings.followedTeams.length} followed)
          </button>
          <button
            onClick={() => setTab("leagues")}
            className={`px-3 py-1 text-xs font-semibold rounded transition-all ${
              tab === "leagues" ? "bg-[#c8aa6e] text-[#091428]" : "text-[#7e8e9f] hover:text-[#f0e6d2]"
            }`}
          >
            Leagues ({settings.followedLeagues.length} followed)
          </button>
        </div>

        <div className="relative w-64">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-[#7e8e9f]" />
          <input
            type="text"
            placeholder={`Search ${tab}…`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#0a1420] border border-[#1e282d] rounded pl-8 pr-3 py-1 text-xs text-[#f0e6d2] focus:outline-none focus:border-[#c8aa6e]"
          />
        </div>
      </div>

      {/* Grid of items */}
      {tab === "teams" ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {filteredTeams.map((team) => {
            const isFollowed = settings.followedTeams.includes(team.code);
            return (
              <div
                key={team.code}
                onClick={() => toggleTeam(team.code)}
                className={`flex items-center justify-between p-3 rounded border cursor-pointer transition-all ${
                  isFollowed
                    ? "bg-[#0a1420] border-[#c8aa6e] text-[#f0e6d2]"
                    : "bg-[#091428] border-[#1e282d] text-[#7e8e9f] hover:border-[#7e8e9f]"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-[#0a0e17] flex items-center justify-center font-bold font-mono text-xs text-[#c8aa6e]">
                    {team.code}
                  </div>
                  <div>
                    <div className="font-semibold text-xs text-[#f0e6d2]">{team.name}</div>
                    <div className="text-[10px] text-[#7e8e9f]">{team.league}</div>
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleTeam(team.code);
                  }}
                  className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold transition-colors ${
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
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {filteredLeagues.map((league) => {
            const isFollowed = settings.followedLeagues.includes(league.slug);
            return (
              <div
                key={league.slug}
                onClick={() => toggleLeague(league.slug)}
                className={`flex items-center justify-between p-3 rounded border cursor-pointer transition-all ${
                  isFollowed
                    ? "bg-[#0a1420] border-[#c8aa6e] text-[#f0e6d2]"
                    : "bg-[#091428] border-[#1e282d] text-[#7e8e9f] hover:border-[#7e8e9f]"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-[#0a0e17] flex items-center justify-center text-[#0ac8b9]">
                    <Globe className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="font-semibold text-xs text-[#f0e6d2]">{league.name}</div>
                    <div className="text-[10px] text-[#7e8e9f]">{league.region}</div>
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleLeague(league.slug);
                  }}
                  className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold transition-colors ${
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
      )}
    </div>
  );
};
