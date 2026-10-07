import { Match, LiveStats, StreamEvent, AppSettings, NewsItem, Team, Region, League, PlayerEntry } from "./types";

const RIOT_API_KEY = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z";
const RIOT_BASE = "https://esports-api.lolesports.com/persisted/gw";
const STREAM_SCHEDULE_URL = "https://lolworlds.com/api.ashx?type=schedule-json";

export const MAJOR_REGIONS: Region[] = [
  { code: "INTERNATIONAL", name: "International", leagues: ["Worlds", "MSI", "First Stand"], badge: "🌐" },
  { code: "KOREA", name: "Korea", leagues: ["LCK", "LCK Challengers"], badge: "🇰🇷" },
  { code: "CHINA", name: "China", leagues: ["LPL", "LDL"], badge: "🇨🇳" },
  { code: "EUROPE", name: "Europe", leagues: ["LEC", "EMEA Masters"], badge: "🇪🇺" },
  { code: "NORTH AMERICA", name: "North America", leagues: ["LCS", "NACL"], badge: "🇺🇸" },
  { code: "APAC", name: "Asia-Pacific", leagues: ["LCP", "PCS", "VCS"], badge: "🌏" },
  { code: "BRAZIL", name: "Brazil", leagues: ["CBLOL", "CBLOL Academy"], badge: "🇧🇷" },
];

export const DEFAULT_FOLLOWED_REGIONS = [
  "INTERNATIONAL",
  "KOREA",
  "CHINA",
  "EUROPE",
  "NORTH AMERICA",
  "APAC",
  "BRAZIL",
];

export const DEFAULT_FOLLOWED_LEAGUES = [
  "worlds",
  "msi",
  "first_stand",
  "lck",
  "lpl",
  "lec",
  "lcs",
  "lcp",
  "cblol-brazil",
];

export const POPULAR_TEAMS: Array<{ code: string; name: string; league: string; image?: string }> = [
  { code: "T1", name: "T1", league: "LCK" },
  { code: "GEN", name: "Gen.G Esports", league: "LCK" },
  { code: "HLE", name: "Hanwha Life Esports", league: "LCK" },
  { code: "DK", name: "Dplus KIA", league: "LCK" },
  { code: "KT", name: "KT Rolster", league: "LCK" },
  { code: "BLG", name: "Bilibili Gaming", league: "LPL" },
  { code: "TES", name: "Top Esports", league: "LPL" },
  { code: "WBG", name: "Weibo Gaming", league: "LPL" },
  { code: "JDG", name: "JD Gaming", league: "LPL" },
  { code: "LNG", name: "LNG Esports", league: "LPL" },
  { code: "G2", name: "G2 Esports", league: "LEC" },
  { code: "FNC", name: "Fnatic", league: "LEC" },
  { code: "KC", name: "Karmine Corp", league: "LEC" },
  { code: "MDK", name: "MAD Lions KOI", league: "LEC" },
  { code: "FLY", name: "FlyQuest", league: "LCS" },
  { code: "TL", name: "Team Liquid", league: "LCS" },
  { code: "C9", name: "Cloud9", league: "LCS" },
  { code: "100", name: "100 Thieves", league: "LCS" },
  { code: "PNG", name: "paiN Gaming", league: "CBLOL" },
  { code: "FUR", name: "FURIA", league: "CBLOL" },
];

export const POPULAR_PLAYERS: PlayerEntry[] = [
  { name: "Faker", role: "Mid", teamCode: "T1", teamName: "T1", realName: "Lee Sang-hyeok" },
  { name: "Chovy", role: "Mid", teamCode: "GEN", teamName: "Gen.G Esports", realName: "Jeong Ji-hoon" },
  { name: "Ruler", role: "Bot", teamCode: "GEN", teamName: "Gen.G Esports", realName: "Park Jae-hyuk" },
  { name: "Caps", role: "Mid", teamCode: "G2", teamName: "G2 Esports", realName: "Rasmus Winther" },
  { name: "Bwipo", role: "Top", teamCode: "FLY", teamName: "FlyQuest", realName: "Gabriël Rau" },
  { name: "Gumayusi", role: "Bot", teamCode: "T1", teamName: "T1", realName: "Lee Min-hyeong" },
  { name: "Keria", role: "Support", teamCode: "T1", teamName: "T1", realName: "Ryu Min-seok" },
  { name: "Oner", role: "Jungle", teamCode: "T1", teamName: "T1", realName: "Mun Hyeon-jun" },
  { name: "Zeus", role: "Top", teamCode: "HLE", teamName: "Hanwha Life Esports", realName: "Choi Woo-je" },
  { name: "Viper", role: "Bot", teamCode: "HLE", teamName: "Hanwha Life Esports", realName: "Park Do-hyeon" },
  { name: "Knight", role: "Mid", teamCode: "BLG", teamName: "Bilibili Gaming", realName: "Zhuo Ding" },
  { name: "Bin", role: "Top", teamCode: "BLG", teamName: "Bilibili Gaming", realName: "Chen Ze-Bin" },
  { name: "JackeyLove", role: "Bot", teamCode: "TES", teamName: "Top Esports", realName: "Yu Wen-Bo" },
  { name: "Scout", role: "Mid", teamCode: "LNG", teamName: "LNG Esports", realName: "Lee Ye-chan" },
  { name: "Inspired", role: "Jungle", teamCode: "FLY", teamName: "FlyQuest", realName: "Kacper Słoma" },
  { name: "Humanoid", role: "Mid", teamCode: "FNC", teamName: "Fnatic", realName: "Marek Brázda" },
  { name: "Mikyx", role: "Support", teamCode: "G2", teamName: "G2 Esports", realName: "Mihael Mehle" },
  { name: "ShowMaker", role: "Mid", teamCode: "DK", teamName: "Dplus KIA", realName: "Heo Su" },
  { name: "Canyon", role: "Jungle", teamCode: "GEN", teamName: "Gen.G Esports", realName: "Kim Geon-bu" },
  { name: "Peyz", role: "Bot", teamCode: "JDG", teamName: "JD Gaming", realName: "Kim Su-hwan" },
];

export const GLOBAL_LEAGUES: League[] = [
  { slug: "worlds", name: "World Championship", region: "INTERNATIONAL", priority: 0 },
  { slug: "msi", name: "Mid-Season Invitational", region: "INTERNATIONAL", priority: 1 },
  { slug: "first_stand", name: "First Stand", region: "INTERNATIONAL", priority: 2 },
  { slug: "lck", name: "LCK (League of Legends Champions Korea)", region: "KOREA", priority: 3 },
  { slug: "lpl", name: "LPL (League of Legends Pro League)", region: "CHINA", priority: 4 },
  { slug: "lec", name: "LEC (League of Legends EMEA Championship)", region: "EUROPE", priority: 5 },
  { slug: "lcs", name: "LCS (League Championship Series)", region: "NORTH AMERICA", priority: 6 },
  { slug: "lcp", name: "LCP (League of Legends Championship Pacific)", region: "APAC", priority: 7 },
  { slug: "cblol-brazil", name: "CBLOL (Campeonato Brasileiro)", region: "BRAZIL", priority: 8 },
  { slug: "demacia_cup", name: "Demacia Cup", region: "CHINA", priority: 9 },
  { slug: "emea_masters", name: "EMEA Masters", region: "EUROPE", priority: 10 },
  { slug: "nacl", name: "NACL (North American Challengers)", region: "NORTH AMERICA", priority: 11 },
];

export const DEFAULT_SETTINGS: AppSettings = {
  spoilerMode: false,
  tickerMode: "docked",
  tickerTopmost: true,
  tickerCycleSec: 5,
  defaultTab: "live",
  notifyKickoff: true,
  notifyPregame: true,
  notifyStream: true,
  minimizeToTrayOnClose: true,
  startWithWindows: false,
  followedTeams: ["T1", "GEN", "G2", "FLY", "BLG"],
  followedPlayers: ["Faker", "Chovy", "Ruler", "Caps"],
  followedLeagues: [...DEFAULT_FOLLOWED_LEAGUES],
  followedRegions: [...DEFAULT_FOLLOWED_REGIONS],
};

export function loadSettings(): AppSettings {
  try {
    const raw = localStorage.getItem("riftwatch_settings");
    if (raw) {
      const parsed = JSON.parse(raw);
      // Ensure all major regions are followed if not already configured
      if (!parsed.followedRegions || parsed.followedRegions.length === 0) {
        parsed.followedRegions = [...DEFAULT_FOLLOWED_REGIONS];
      }
      return { ...DEFAULT_SETTINGS, ...parsed };
    }
  } catch (e) {
    console.error("Failed to load settings:", e);
  }
  return DEFAULT_SETTINGS;
}

export function saveSettings(settings: AppSettings): void {
  try {
    localStorage.setItem("riftwatch_settings", JSON.stringify(settings));
    window.dispatchEvent(new Event("riftwatch_settings_updated"));
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
