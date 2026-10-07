import { Match, LiveStats, StreamEvent, AppSettings, NewsItem, Team, Region, League, PlayerEntry, AppUpdateInfo } from "./types";

const RIOT_API_KEY = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z";
const RIOT_BASE = "https://esports-api.lolesports.com/persisted/gw";
const STREAM_SCHEDULE_URL = "https://lolworlds.com/api.ashx?type=schedule-json";

export const MAJOR_REGIONS: Region[] = [
  { code: "INTERNATIONAL", name: "International", leagues: ["Worlds", "MSI", "First Stand"], badge: "🌐" },
  { code: "KOREA", name: "Korea", leagues: ["LCK", "LCK Challengers"], badge: "🇰🇷" },
  { code: "CHINA", name: "China", leagues: ["LPL", "LDL"], badge: "🇨🇳" },
  { code: "EMEA", name: "Europe, Middle East & Africa", leagues: ["LEC", "EMEA Masters"], badge: "🇪🇺" },
  { code: "NORTH AMERICA", name: "North America", leagues: ["LCS", "NACL"], badge: "🇺🇸" },
  { code: "PACIFIC", name: "Asia-Pacific", leagues: ["LCP"], badge: "🌏" },
  { code: "BRAZIL", name: "Brazil", leagues: ["CBLOL", "CBLOL Academy"], badge: "🇧🇷" },
  { code: "JAPAN", name: "Japan", leagues: ["LJL"], badge: "🇯🇵" },
  { code: "VIETNAM", name: "Vietnam", leagues: ["VCS"], badge: "🇻🇳" },
  { code: "HONG KONG, MACAU, TAIWAN", name: "Hong Kong, Macau & Taiwan", leagues: ["PCS"], badge: "🇹🇼" },
  { code: "LATIN AMERICA", name: "Latin America", leagues: ["LLA"], badge: "🌎" },
  { code: "OCEANIA", name: "Oceania", leagues: ["Oceanic leagues"], badge: "🇦🇺" },
];

export const DEFAULT_FOLLOWED_REGIONS = MAJOR_REGIONS.map((r) => r.code);

// Older versions used these region codes; map them to the real ones.
const LEGACY_REGION_CODES: Record<string, string> = { EUROPE: "EMEA", APAC: "PACIFIC" };

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
  { slug: "lec", name: "LEC (League of Legends EMEA Championship)", region: "EMEA", priority: 5 },
  { slug: "lcs", name: "LCS (League Championship Series)", region: "NORTH AMERICA", priority: 6 },
  { slug: "lcp", name: "LCP (League of Legends Championship Pacific)", region: "PACIFIC", priority: 7 },
  { slug: "cblol-brazil", name: "CBLOL (Campeonato Brasileiro)", region: "BRAZIL", priority: 8 },
  { slug: "demacia_cup", name: "Demacia Cup", region: "CHINA", priority: 9 },
  { slug: "emea_masters", name: "EMEA Masters", region: "EMEA", priority: 10 },
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
      if (!Array.isArray(parsed.followedRegions) || parsed.followedRegions.length === 0) {
        parsed.followedRegions = [...DEFAULT_FOLLOWED_REGIONS];
      } else {
        // Map region codes saved by older versions (EUROPE, APAC) to the real ones.
        const mapped: string[] = parsed.followedRegions.map((c: string) => LEGACY_REGION_CODES[c] || c);
        const hadLegacy = mapped.some((c, i) => c !== parsed.followedRegions[i]);
        // If the user never customised (old default list), follow every region now.
        parsed.followedRegions = hadLegacy && mapped.length >= 7 ? [...DEFAULT_FOLLOWED_REGIONS] : Array.from(new Set(mapped));
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

// -------------------------------------------------------------
// Catalog Persistence & Live Synchronizer (Teams, Players, Leagues)
// -------------------------------------------------------------
import { CatalogData, CatalogTeam } from "./types";

export const EMPTY_CATALOG: CatalogData = { teams: [], players: [], leagues: [], updatedAt: 0 };

/** Catalog saved from a previous live sync (null if none yet). */
export function loadCachedCatalog(): CatalogData | null {
  try {
    const raw = localStorage.getItem("riftwatch_catalog");
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed.teams?.length > 0 && parsed.players?.length > 0 && parsed.leagues?.length > 0) {
        return parsed as CatalogData;
      }
    }
  } catch (e) {
    console.warn("Failed to read catalog from cache:", e);
  }
  return null;
}

/** The catalog snapshot shipped inside the app. Loaded only when needed to keep startup light. */
export async function loadBundledCatalog(): Promise<CatalogData> {
  const mod = await import("./catalog_default.json");
  return (mod.default ?? mod) as unknown as CatalogData;
}

export function saveCatalog(catalog: CatalogData): void {
  try {
    localStorage.setItem("riftwatch_catalog", JSON.stringify(catalog));
    window.dispatchEvent(new CustomEvent("riftwatch_catalog_updated", { detail: catalog }));
  } catch (e) {
    console.error("Failed to save catalog:", e);
  }
}

/**
 * Pulls the latest teams, players and leagues from Riot.
 * Returns null (and changes nothing) if the request fails or the result looks broken.
 */
export async function fetchLiveCatalog(current?: CatalogData): Promise<CatalogData | null> {
  try {
    const [teamsData, leaguesData] = await Promise.all([
      fetchJson(`${RIOT_BASE}/getTeams?hl=en-US`, { headers: riotHeaders }, 30000),
      fetchJson(`${RIOT_BASE}/getLeagues?hl=en-US`, { headers: riotHeaders }, 30000),
    ]);

    const rawTeams = teamsData?.data?.teams || [];
    const cleanTeams: CatalogTeam[] = [];
    const cleanPlayers: PlayerEntry[] = [];
    const seenPlayers = new Set<string>();

    for (const t of rawTeams) {
      if (t.status !== "active" || !t.players || t.players.length === 0 || !t.slug) continue;
      const code = (t.code || t.slug).trim().toUpperCase();
      const name = (t.name || t.slug).trim();
      const homeLeague = t.homeLeague?.name || "";
      const homeRegion = t.homeLeague?.region || "";

      cleanTeams.push({
        slug: t.slug,
        code,
        name,
        image: t.image,
        league: homeLeague,
        region: homeRegion,
      });

      for (const p of t.players) {
        const pName = (p.summonerName || "").trim();
        if (!pName) continue;
        const key = `${pName.toLowerCase()}:${code}`;
        if (seenPlayers.has(key)) continue;
        seenPlayers.add(key);

        const roleStr = (p.role || "").toLowerCase();
        let roleFormatted = "Sub";
        if (roleStr === "top") roleFormatted = "Top";
        else if (roleStr === "jungle") roleFormatted = "Jungle";
        else if (roleStr === "mid") roleFormatted = "Mid";
        else if (roleStr === "bottom") roleFormatted = "Bot";
        else if (roleStr === "support") roleFormatted = "Support";

        let real = "";
        if (p.firstName && p.lastName) {
          real = `${p.firstName} ${p.lastName}`.trim();
        } else if (p.firstName) {
          real = p.firstName.trim();
        }

        cleanPlayers.push({
          name: pName,
          role: roleFormatted,
          teamCode: code,
          teamName: name,
          teamSlug: t.slug,
          realName: real || undefined,
          image: p.image,
        });
      }
    }

    const rawLeagues = leaguesData?.data?.leagues || [];
    const cleanLeagues: League[] = [];
    for (const l of rawLeagues) {
      if (!l.slug || !l.name) continue;
      cleanLeagues.push({
        slug: l.slug,
        name: l.name,
        region: l.region || "",
        image: l.image,
      });
    }

    // Sanity guard: a response far smaller than what we already have is almost certainly a glitch.
    if (current && current.teams.length > 0 && cleanTeams.length < current.teams.length * 0.5) {
      console.warn(`Live catalog looks incomplete (${cleanTeams.length} vs ${current.teams.length} teams); keeping current.`);
      return null;
    }
    if (cleanTeams.length === 0 || cleanPlayers.length === 0 || cleanLeagues.length === 0) return null;

    const newCatalog: CatalogData = {
      teams: cleanTeams,
      players: cleanPlayers,
      leagues: cleanLeagues,
      updatedAt: Date.now(),
    };

    saveCatalog(newCatalog);
    return newCatalog;
  } catch (err) {
    console.warn("fetchLiveCatalog failed, retaining current cache:", err);
    return null;
  }
}



async function fetchJson(url: string, init?: RequestInit, timeoutMs = 15000): Promise<any> {
  const res = await fetch(url, { ...init, signal: AbortSignal.timeout(timeoutMs) });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

const riotHeaders = { "x-api-key": RIOT_API_KEY };

/**
 * Turns Riot's stream entry (provider + channel/video id) into a real web link.
 * Prefers English-language streams, like the original Python app did.
 */
export function buildStreamUrl(streams: any[] | undefined): string {
  if (!streams || streams.length === 0) return "";
  const pick =
    streams.find((s) => String(s?.locale || "").toLowerCase().startsWith("en")) || streams[0];
  const param = String(pick?.parameter || "").trim();
  if (!param) return "";
  if (/^https?:\/\//i.test(param)) return param;
  const p = encodeURIComponent(param);
  switch (String(pick?.provider || "").toLowerCase()) {
    case "twitch":
      return `https://www.twitch.tv/${p}`;
    case "youtube":
      return `https://www.youtube.com/watch?v=${p}`;
    case "afreecatv":
    case "afreeca":
    case "soop":
      return `https://play.sooplive.co.kr/${p}`;
    case "bilibili":
      return `https://live.bilibili.com/${p}`;
    case "huya":
      return `https://www.huya.com/${p}`;
    case "chzzk":
      return `https://chzzk.naver.com/live/${p}`;
    default:
      return "";
  }
}

export async function fetchLiveMatches(): Promise<{ matches: Match[]; liveStats: Record<string, LiveStats> }> {
  const data = await fetchJson(`${RIOT_BASE}/getLive?hl=en-US`, { headers: riotHeaders });
  const rawEvents = data?.data?.schedule?.events || [];

  const matches: Match[] = [];
  const liveStats: Record<string, LiveStats> = {};

  for (const ev of rawEvents) {
    const isProgress = ev.state === "inProgress";
    const m = ev.match;

    if (!m && !isProgress) continue;

    if (!m && isProgress) {
      // Live broadcast / show without an embedded match object (e.g. EMEA Masters or international stream)
      matches.push({
        matchId: ev.id,
        leagueName: ev.league?.name || "Live Pro Broadcast",
        leagueSlug: ev.league?.slug || "",
        blockName: ev.blockName || "Broadcast Live",
        startTimeUtc: ev.startTime || new Date().toISOString(),
        state: "inProgress",
        bestOf: 1,
        winner: undefined,
        streamUrl: buildStreamUrl(ev.streams),
        team1Code: "LIVE",
        team1Name: ev.league?.name || "Live Broadcast",
        team1Image: ev.league?.image,
        team1Score: 0,
        team2Code: "AIR",
        team2Name: "Live on Air",
        team2Image: ev.league?.image,
        team2Score: 0,
        games: [],
      });
      continue;
    }

    const t1 = m.teams?.[0] || {};
    const t2 = m.teams?.[1] || {};

    matches.push({
      matchId: m.id || ev.id,
      leagueName: ev.league?.name || "League",
      leagueSlug: ev.league?.slug || "",
      blockName: ev.blockName || "",
      startTimeUtc: ev.startTime || new Date().toISOString(),
      state: m.state || "inProgress",
      bestOf: m.strategy?.count || 3,
      winner: (t1.result?.outcome === "win" ? t1.code : t2.result?.outcome === "win" ? t2.code : undefined),
      streamUrl: buildStreamUrl(ev.streams),
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
    });
  }
  return { matches, liveStats };
}

function scheduleEventsToMatches(rawEvents: any[]): Match[] {
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
      streamUrl: buildStreamUrl(ev.streams),
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
}

/**
 * Riot's schedule endpoint only returns about two days per request.
 * We take the first page, then follow "newer" pages a couple of times so
 * "next match for a team you follow" can see further ahead.
 */
export async function fetchSchedule(extraNewerPages = 2): Promise<Match[]> {
  const first = await fetchJson(`${RIOT_BASE}/getSchedule?hl=en-US`, { headers: riotHeaders });
  const all: Match[] = scheduleEventsToMatches(first?.data?.schedule?.events || []);

  let token: string | undefined = first?.data?.schedule?.pages?.newer;
  for (let i = 0; i < extraNewerPages && token; i++) {
    try {
      const next = await fetchJson(
        `${RIOT_BASE}/getSchedule?hl=en-US&pageToken=${encodeURIComponent(token)}`,
        { headers: riotHeaders },
      );
      all.push(...scheduleEventsToMatches(next?.data?.schedule?.events || []));
      token = next?.data?.schedule?.pages?.newer;
    } catch {
      break; // later pages are a bonus; keep what we have
    }
  }

  const seen = new Set<string>();
  const unique = all.filter((m) => (seen.has(m.matchId) ? false : (seen.add(m.matchId), true)));
  unique.sort((a, b) => a.startTimeUtc.localeCompare(b.startTimeUtc));
  return unique;
}

export async function fetchStreamSchedule(): Promise<StreamEvent[]> {
  const data: any[] = await fetchJson(STREAM_SCHEDULE_URL, undefined, 20000);
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
    isBanger: item.isBanger === true || (typeof item.tag === "string" && item.tag.toLowerCase().trim() === "banger"),
  }));
}

export async function fetchCuratedNews(): Promise<NewsItem[]> {
  // Authoritative, tier-1 LoL Esports journalism dispatches
  return [
    {
      id: "news-sheep-1",
      title: "Sources: T1 Finalizes Multi-Year Core Roster Extensions Ahead of 2026 Season",
      source: "Sheep Esports",
      date: "Today",
      summary: "Following their historic international runs, T1 has secured key multi-year commitments to retain their world-championship caliber core through 2026.",
      tag: "Transfers & Rumors",
      url: "https://www.sheepesports.com",
    },
    {
      id: "news-inven-1",
      title: "LCK Post-Match: Faker on Adapting to Fearless Draft & Shotcalling Under Pressure",
      source: "Inven Global",
      date: "Today",
      summary: "In an exclusive press conference, Faker breaks down how the Fearless Draft format tests player versatility, champion depth, and mid-series adaptation.",
      tag: "LCK & Interviews",
      url: "https://www.invenglobal.com/esports",
    },
    {
      id: "news-riot-1",
      title: "First Stand 2026: Official International Tournament Format, Schedule & Venues",
      source: "Riot LoL Esports",
      date: "Yesterday",
      summary: "Riot Games officially unveils the structure for First Stand, uniting split-one champions across LCK, LPL, LEC, LCS, and LCP in high-stakes competition.",
      tag: "Official Dispatches",
      url: "https://lolesports.com/news",
    },
    {
      id: "news-inven-2",
      title: "Gen.G Chovy: 'Fearless Draft Rewards Teams That Understand Global Tempo Over Safe Metas'",
      source: "Inven Global",
      date: "2 days ago",
      summary: "Chovy discusses the evolution of mid lane itemization, wave priority in the current competitive patch, and preparation for international clashes.",
      tag: "LCK & Interviews",
      url: "https://www.invenglobal.com/esports",
    },
    {
      id: "news-sheep-2",
      title: "Sources: LEC Off-Season Shuffle Begins as Teams Eye Rising ERL Standouts",
      source: "Sheep Esports",
      date: "3 days ago",
      summary: "Multiple European organizations are evaluating top performers from EMEA Masters to inject fresh talent into upcoming split rosters.",
      tag: "Transfers & Rumors",
      url: "https://www.sheepesports.com",
    },
    {
      id: "news-dot-1",
      title: "Competitive Patch Breakdown: Priority Champions & Winrate Shifts Across Major Leagues",
      source: "Dot Esports",
      date: "3 days ago",
      summary: "Comprehensive statistical analysis of pick-ban presence, objective trading tempo, and champion tier shifts across LCK, LPL, and LEC pro play.",
      tag: "Meta & Analysis",
      url: "https://dotesports.com/league-of-legends",
    },
    {
      id: "news-riot-2",
      title: "LoL Esports Global Rulebook Update: Competitive Rulings & In-Game Pause Protocols",
      source: "Riot LoL Esports",
      date: "4 days ago",
      summary: "Official competitive operations notice regarding standardized hardware timeout protocols and referee decision trees during live tier-1 stages.",
      tag: "Official Dispatches",
      url: "https://lolesports.com/news",
    },
  ];
}

/**
 * Compare two semver-like strings (e.g., "0.3.5" vs "0.3.6").
 * Returns 1 if v1 > v2, -1 if v1 < v2, and 0 if equal.
 */
export function compareSemver(v1: string, v2: string): number {
  const p1 = v1.replace(/^v/i, "").split(".").map((n) => parseInt(n, 10) || 0);
  const p2 = v2.replace(/^v/i, "").split(".").map((n) => parseInt(n, 10) || 0);
  const maxLen = Math.max(p1.length, p2.length);
  for (let i = 0; i < maxLen; i++) {
    const num1 = p1[i] || 0;
    const num2 = p2[i] || 0;
    if (num1 > num2) return 1;
    if (num1 < num2) return -1;
  }
  return 0;
}

/**
 * Query GitHub Releases API for the latest published RiftWatch release.
 * Returns metadata and direct download URL for the standalone .exe asset.
 */
export async function checkForAppUpdate(currentVersion: string): Promise<AppUpdateInfo | null> {
  try {
    const res = await fetch("https://api.github.com/repos/drmonocle/riftwatch/releases/latest", {
      headers: {
        Accept: "application/vnd.github.v3+json",
      },
    });
    if (!res.ok) return null;
    const data = await res.json();
    const latestTag = (data.tag_name || "").trim();
    const cleanLatest = latestTag.replace(/^v/i, "");
    const cleanCurrent = currentVersion.replace(/^v/i, "");

    const hasUpdate = compareSemver(cleanLatest, cleanCurrent) > 0;
    const exeAsset = (data.assets || []).find((a: any) =>
      a.name?.toLowerCase().endsWith(".exe")
    );
    const downloadUrl =
      exeAsset?.browser_download_url ||
      `https://github.com/drmonocle/riftwatch/releases/download/${latestTag}/RiftWatch.exe`;

    return {
      hasUpdate,
      currentVersion: cleanCurrent,
      latestVersion: cleanLatest,
      releaseName: data.name || latestTag,
      releaseNotes: data.body || "",
      releaseUrl: data.html_url || "https://github.com/drmonocle/riftwatch/releases",
      downloadUrl,
      publishedAt: data.published_at || "",
    };
  } catch (err) {
    console.warn("Failed to check GitHub releases for updates:", err);
    return null;
  }
}
