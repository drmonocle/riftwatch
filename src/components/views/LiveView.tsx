import React from "react";
import { Match, AppSettings } from "../../types";
import { Tv, ExternalLink, ShieldAlert } from "lucide-react";

interface LiveViewProps {
  matches: Match[];
  settings: AppSettings;
  onOpenUrl: (url: string) => void;
}

export const LiveView: React.FC<LiveViewProps> = ({ matches, settings, onOpenUrl }) => {
  if (matches.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-4 py-16">
        <div className="w-12 h-12 rounded-full bg-[#0a1420] border border-[#1e282d] flex items-center justify-center text-[#7e8e9f] mb-3">
          <Tv className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-bold text-[#f0e6d2] uppercase tracking-wider mb-1">
          No Pro Matches In Progress
        </h3>
        <p className="text-xs text-[#7e8e9f] max-w-sm mb-4">
          All regional leagues (LCK, LPL, LEC, LCS) and international events are currently idle. Check the Schedule tab for upcoming kickoffs today.
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4 max-w-4xl mx-auto overflow-y-auto h-full">
      <div className="flex items-center justify-between pb-1 border-b border-[#1e282d]">
        <h2 className="text-xs font-bold text-[#c8aa6e] uppercase tracking-wider">
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
                isT1Followed || isT2Followed ? "border-[#c8aa6e] shadow-lg shadow-[#c8aa6e]/5" : "border-[#1e282d]"
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
};
