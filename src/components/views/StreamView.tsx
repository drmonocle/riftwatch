import React from "react";
import { StreamEvent, AppSettings } from "../../types";
import { Radio, Play, ExternalLink, Flame, Trophy } from "lucide-react";

interface StreamViewProps {
  events: StreamEvent[];
  settings: AppSettings;
  onOpenUrl: (url: string) => void;
}

export const StreamView: React.FC<StreamViewProps> = ({ events, settings, onOpenUrl }) => {
  const currentEvent = events[0];
  const upcomingEvents = events.slice(1, 20);
  const nextBanger = events.find((e) => e.isBanger);

  return (
    <div className="p-4 space-y-4 max-w-4xl mx-auto overflow-y-auto h-full select-none">
      {/* 24/7 Broadcast Hero Card */}
      <div className="bg-[#0a1420] border border-[#0ac8b9] rounded-lg p-5 shadow-lg relative overflow-hidden">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="bg-[#0ac8b9] text-[#091428] font-bold text-xs px-2.5 py-0.5 rounded flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 animate-pulse" />
              24/7 BROADCAST REPLAY
            </span>
            {currentEvent?.isBanger && (
              <span className="bg-[#ff4655] text-white font-bold text-[10px] px-2 py-0.5 rounded flex items-center gap-1">
                <Flame className="w-3 h-3 fill-current" />
                S-TIER BANGER
              </span>
            )}
          </div>
          <span className="text-xs text-[#7e8e9f]">Continuous Stream</span>
        </div>

        {/* Title */}
        <h1 className="text-xl font-bold text-[#f0e6d2] mt-1 mb-1">
          {currentEvent ? `${currentEvent.event} ${currentEvent.season}: ${currentEvent.stage || "Replay"}` : "League Rebroadcast"}
        </h1>
        <p className="text-xs text-[#7e8e9f] mb-4">
          {currentEvent?.team1 && currentEvent?.team2
            ? `${currentEvent.team1} vs. ${currentEvent.team2} · High-bitrate remastered broadcast`
            : "Continuous uninterrupted tournament archives playing 24/7 without commercial breaks."}
        </p>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => onOpenUrl("https://twitch.tv/lolcontinuous")}
            className="flex items-center gap-2 px-4 py-2 rounded bg-[#9146ff] hover:bg-[#a970ff] text-white font-bold text-xs transition-colors shadow"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Watch on Twitch</span>
          </button>
          <button
            onClick={() => onOpenUrl("https://youtube.com/@LoLWorldChampionships/live")}
            className="flex items-center gap-2 px-4 py-2 rounded bg-[#cc0000] hover:bg-[#e60000] text-white font-bold text-xs transition-colors shadow"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Watch on YouTube</span>
          </button>
          <button
            onClick={() => onOpenUrl("https://lolworlds.com")}
            className="flex items-center gap-1.5 px-3 py-2 rounded bg-[#091428] hover:bg-[#121e2d] border border-[#1e282d] text-[#f0e6d2] text-xs transition-colors"
          >
            <span>Full Schedule on lolworlds.com</span>
            <ExternalLink className="w-3.5 h-3.5 text-[#7e8e9f]" />
          </button>
        </div>
      </div>

      {/* Next S-Tier Banger Banner */}
      {nextBanger && (
        <div className="bg-[#1e131d] border border-[#ff4655]/50 rounded-lg p-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-[#ff4655]/20 flex items-center justify-center text-[#ff4655]">
              <Trophy className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[10px] font-bold text-[#ff4655] tracking-wider uppercase">Upcoming S-Tier Banger</div>
              <div className="text-xs font-semibold text-[#f0e6d2]">
                {nextBanger.event} {nextBanger.season} · {nextBanger.team1} vs {nextBanger.team2}
              </div>
            </div>
          </div>
          <span className="text-xs text-[#7e8e9f] font-mono">{nextBanger.rawTime || "In rotation"}</span>
        </div>
      )}

      {/* Upcoming Rebroadcasts List */}
      <div>
        <h3 className="text-xs font-bold text-[#c8aa6e] uppercase tracking-wider mb-2">
          Upcoming Marathon Schedule ({upcomingEvents.length})
        </h3>
        <div className="space-y-1.5">
          {upcomingEvents.map((e, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between bg-[#0a1420] border border-[#1e282d] hover:border-[#0ac8b9] px-4 py-2 rounded text-xs transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="font-mono text-[#0ac8b9] text-[11px] w-20">{e.rawTime || "Upcoming"}</span>
                <span className="font-semibold text-[#f0e6d2]">
                  {e.event} {e.season} {e.stage ? `· ${e.stage}` : ""}
                </span>
                {e.team1 && e.team2 && (
                  <span className="text-[#7e8e9f]">
                    ({e.team1} vs {e.team2})
                  </span>
                )}
              </div>
              {e.isBanger && (
                <span className="text-[10px] font-bold text-[#ff4655] bg-[#ff4655]/10 px-1.5 py-0.5 rounded">
                  BANGER
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
