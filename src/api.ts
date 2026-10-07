import { Match, LiveStats, StreamEvent, AppSettings, NewsItem, Team } from "./types";

const RIOT_API_KEY = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z";
const RIOT_BASE = "https://esports-api.lolesports.com/persisted/gw";
const STREAM_SCHEDULE_URL = "https://lolworlds.com/api.ashx?type=schedule-json";

const DEFAULT_SETTINGS: AppSettings = {
  spoilerMode: false,
  tickerMode: "docked",
  tickerTopmost: true,
  defaultTab: "live",
  notifyKickoff: true,
  notifyPregame: true,
  notifyStream: true,
  followedTeams: ["T1", "GEN", "G2", "FLY", "BLG"],
  followedPlayers: ["Faker", "Chovy", "Ruler", "Caps"],
  followedLeagues: ["worlds", "msi", "lck", "lpl", "lec", "lcs"],
};

export function loadSettings(): AppSettings {
  try {
    const raw = localStorage.getItem("riftwatch_settings");
    if (raw) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
    }
  } catch (e) {
    console.error("Failed to load settings:", e);
  }
  return DEFAULT_SETTINGS;
}

export function saveSettings(settings: AppSettings): void {
  try {
    localStorage.setItem("riftwatch_settings", JSON.stringify(settings));
  } catch (e) {
    console.error("Failed to save settings:", e);
  }
}

export async function fetchLiveMatches(): Promise<{ matches: Match[]; liveStats: Record<string, LiveStats> }> {
  try {
    const res = await fetch(`${RIOT_BASE}/getLive?hl=en-US`, {
      headers: { "x-api-key": RIOT_API_KEY },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const rawEvents = data?.data?.schedule?.events || [];

    const matches: Match[] = [];
    const liveStats: Record<string, LiveStats> = {};

    for (const ev of rawEvents) {
      if (ev.type !== "match") continue;
      const m = ev.match;
      if (!m) continue;

      const t1 = m.teams?.[0] || {};
      const t2 = m.teams?.[1] || {};

      const matchObj: Match = {
        matchId: m.id || ev.id,
        leagueName: ev.league?.name || "League",
        leagueSlug: ev.league?.slug || "",
        blockName: ev.blockName || "",
        startTimeUtc: ev.startTime || new Date().toISOString(),
        state: m.state || "inProgress",
        bestOf: m.strategy?.count || 3,
        winner: (t1.result?.outcome === "win" ? t1.code : t2.result?.outcome === "win" ? t2.code : undefined),
        streamUrl: ev.streams?.[0]?.parameter || "",
        team1Code: t1.code || t1.name || "TBD",
        team1Name: t1.name || "TBD",
        team1Image: t1.image,
        team1Score: t1.result?.gameWins ?? 0,
        team2Code: t2.code || t2.name || "TBD",
        team2Name: t2.name || "TBD",
        team2Image: t2.image,
        team2Score: t2.result?.gameWins ?? 0,
        games: (m.games || []).map((g: any) => ({
          id: g.id,
          number: g.number,
          state: g.state,
        })),
      };
      matches.push(matchObj);
    }
    return { matches, liveStats };
  } catch (err) {
    console.warn("fetchLiveMatches fallback:", err);
    return { matches: [], liveStats: {} };
  }
}

export async function fetchSchedule(): Promise<Match[]> {
  try {
    const res = await fetch(`${RIOT_BASE}/getSchedule?hl=en-US`, {
      headers: { "x-api-key": RIOT_API_KEY },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const rawEvents = data?.data?.schedule?.events || [];

    const matches: Match[] = [];
    for (const ev of rawEvents) {
      if (ev.type !== "match") continue;
      const m = ev.match;
      if (!m) continue;

      const t1 = m.teams?.[0] || {};
      const t2 = m.teams?.[1] || {};

      matches.push({
        matchId: m.id || ev.id,
        leagueName: ev.league?.name || "League",
        leagueSlug: ev.league?.slug || "",
        blockName: ev.blockName || "",
        startTimeUtc: ev.startTime || "",
        state: m.state || (ev.state === "completed" ? "completed" : "unstarted"),
        bestOf: m.strategy?.count || 3,
        team1Code: t1.code || t1.name || "TBD",
        team1Name: t1.name || "TBD",
        team1Image: t1.image,
        team1Score: t1.result?.gameWins ?? 0,
        team2Code: t2.code || t2.name || "TBD",
        team2Name: t2.name || "TBD",
        team2Image: t2.image,
        team2Score: t2.result?.gameWins ?? 0,
        games: [],
      });
    }
    return matches;
  } catch (err) {
    console.warn("fetchSchedule fallback:", err);
    return [];
  }
}

export async function fetchStreamSchedule(): Promise<StreamEvent[]> {
  try {
    const res = await fetch(STREAM_SCHEDULE_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data: any[] = await res.json();
    return data.map((item) => ({
      id: item.id,
      type: item.type,
      name: item.name,
      event: item.event,
      season: item.season,
      stage: item.stage,
      team1: item.team1,
      team2: item.team2,
      rawTime: item.rawTime,
      utcIso: item.utcIso,
      isBanger: item.isBanger || item.event?.toLowerCase().includes("worlds") || item.stage?.toLowerCase().includes("finals"),
    }));
  } catch (err) {
    console.warn("fetchStreamSchedule fallback:", err);
    return [];
  }
}

export async function fetchCuratedNews(): Promise<NewsItem[]> {
  // Curated, ultra-clean LoL Esports dispatch items without clickbait
  return [
    {
      id: "news-1",
      title: "First Stand 2026 Tournament Format & Bracket Explained",
      source: "Riot LoL Esports",
      date: "Today",
      summary: "First Stand debuts as the first international tournament of the 2026 season featuring the Fearless Draft format.",
      tag: "Tournament",
      url: "https://lolesports.com",
    },
    {
      id: "news-2",
      title: "Patch 14.20 Meta Breakdown: Pro Play Priority Picks",
      source: "LoL Esports Analytics",
      date: "1 day ago",
      summary: "Key adjustments to jungle tempo and marksman itemization affecting upcoming LCK and LPL playoff drafting.",
      tag: "Meta",
      url: "https://lolesports.com",
    },
    {
      id: "news-3",
      title: "Global Power Rankings: Top 10 Teams Entering Split 2",
      source: "Esports Global",
      date: "2 days ago",
      summary: "T1, Gen.G, Bilibili Gaming, and G2 Esports continue to set the international benchmark ahead of MSI 2026.",
      tag: "Rankings",
      url: "https://lolesports.com",
    },
  ];
}
