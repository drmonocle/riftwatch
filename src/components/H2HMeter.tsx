import React from "react";
import { Swords } from "lucide-react";
import { HeadToHeadStats } from "../helpers";

interface H2HMeterProps {
  team1Code: string;
  team2Code: string;
  h2h: HeadToHeadStats;
  /** "sm" fits under a schedule row score; "md" is the full banner with labels. */
  size?: "sm" | "md";
}

const T1_COLOR = "#0ac8b9";
const T2_COLOR = "#e84057";

/** Split bar of all-time game wins between two teams. */
export const H2HMeter: React.FC<H2HMeterProps> = ({ team1Code, team2Code, h2h, size = "sm" }) => {
  const total = h2h.team1Wins + h2h.team2Wins;
  const t1Pct = total > 0 ? Math.round((h2h.team1Wins / total) * 100) : 50;
  const title = `All-time head-to-head: ${team1Code} ${h2h.team1Wins}-${h2h.team2Wins} ${team2Code} (${h2h.totalGames} games, ${t1Pct}%-${100 - t1Pct}%)`;

  const bar = (
    <div className="flex w-full h-1.5 rounded-full overflow-hidden bg-[#1e282d]">
      <div style={{ width: `${t1Pct}%`, backgroundColor: T1_COLOR }} />
      <div style={{ width: `${100 - t1Pct}%`, backgroundColor: T2_COLOR }} />
    </div>
  );

  if (size === "sm") {
    return (
      <div className="flex flex-col items-center w-[84px] mt-1" title={title}>
        <div className="flex items-center justify-between w-full text-[9px] font-mono leading-none mb-0.5">
          <span style={{ color: T1_COLOR }}>{h2h.team1Wins}</span>
          <span className="text-[#7e8e9f] tracking-wide">H2H</span>
          <span style={{ color: T2_COLOR }}>{h2h.team2Wins}</span>
        </div>
        {bar}
      </div>
    );
  }

  return (
    <div className="w-full max-w-xs px-3 py-2 rounded-lg bg-[#091428] border border-[#c8aa6e]/40" title={title}>
      <div className="flex items-center justify-center gap-1.5 text-[10px] uppercase tracking-wider text-[#c8aa6e] font-semibold mb-1.5">
        <Swords className="w-3 h-3 text-[#0ac8b9]" />
        <span>All-Time H2H · {h2h.totalGames} games</span>
      </div>
      <div className="flex items-center gap-2 text-xs font-mono font-bold">
        <span className="whitespace-nowrap" style={{ color: T1_COLOR }}>
          {team1Code} {h2h.team1Wins}
        </span>
        <div className="flex-1">{bar}</div>
        <span className="whitespace-nowrap" style={{ color: T2_COLOR }}>
          {h2h.team2Wins} {team2Code}
        </span>
      </div>
    </div>
  );
};
