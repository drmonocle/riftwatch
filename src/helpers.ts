import { Match, StreamEvent, AppSettings, League } from "./types";

/** If the schedule's latest started entry is older than this, the stream is treated as offline. */
const MAX_AIRING_GAP_MS = 10 * 60 * 60 * 1000;

const ts = (iso?: string): number => {
  if (!iso) return NaN;
  return new Date(iso).getTime();
};

/** The match airing on the 24/7 stream right now, or null if it is off air. */
export function currentStreamEvent(events: StreamEvent[], now = Date.now()): StreamEvent | null {
  let last: StreamEvent | null = null;
  let lastT = -Infinity;
  let lastMatch: StreamEvent | null = null;
  let lastMatchT = -Infinity;

  for (const e of events) {
    const t = ts(e.utcIso);
    if (isNaN(t) || t > now) continue;
    if (t >= lastT) {
      last = e;
      lastT = t;
    }
    if (e.type !== "special" && t >= lastMatchT) {
      lastMatch = e;
      lastMatchT = t;
    }
  }

  if (!last) return null;
  // The playlist ended (an "End" marker is the most recent entry)
  if (last.type === "special" && /^\s*end/i.test(last.name || "")) return null;
  if (now - lastT > MAX_AIRING_GAP_MS) return null;
  // Start / pre-show markers: show the last real match if it is recent, otherwise the marker itself
  if (last.type === "special" && lastMatch && now - lastMatchT <= MAX_AIRING_GAP_MS) return lastMatch;
  return last;
}

/** Upcoming real matches on the 24/7 stream (skips Start/End/Preshow markers), soonest first. */
export function upcomingStreamMatches(events: StreamEvent[], now = Date.now()): StreamEvent[] {
  return events
    .filter((e) => e.type !== "special" && ts(e.utcIso) > now)
    .sort((a, b) => ts(a.utcIso) - ts(b.utcIso));
}

/**
 * The next few matches that haven't started yet.
 * Matches involving teams you follow come first, then the soonest remaining ones.
 */
export function nextUpcomingMatches(
  schedule: Match[],
  followedTeams: string[],
  limit = 3,
  now = Date.now(),
): Match[] {
  // Allow matches a little past their start time (delayed kickoffs) that haven't gone live yet
  const cutoff = now - 30 * 60 * 1000;
  const future = schedule
    .filter((m) => m.state === "unstarted" && ts(m.startTimeUtc) >= cutoff)
    .sort((a, b) => ts(a.startTimeUtc) - ts(b.startTimeUtc));

  const followed = new Set(followedTeams.map((c) => c.toUpperCase()));
  const isFollowed = (m: Match) =>
    followed.has(m.team1Code.toUpperCase()) || followed.has(m.team2Code.toUpperCase());

  const mine = future.filter(isFollowed).slice(0, limit);
  if (mine.length >= limit) return mine;
  const mineIds = new Set(mine.map((m) => m.matchId));
  const rest = future.filter((m) => !mineIds.has(m.matchId)).slice(0, limit - mine.length);
  return [...mine, ...rest].sort((a, b) => ts(a.startTimeUtc) - ts(b.startTimeUtc));
}

export interface BroadcastStream {
  name: string;
  url: string;
  icon: "twitch" | "youtube" | "riot" | "soop" | "bilibili" | "generic";
  badge?: string;
}

/**
 * Returns the official broadcast destinations for a given league slug,
 * including Riot's direct live stream URL if available.
 */
export function getLeagueBroadcastStreams(
  leagueSlug?: string,
  riotStreamUrl?: string
): BroadcastStream[] {
  const streams: BroadcastStream[] = [];

  // If Riot's live API provided a direct active stream link, prioritize it
  if (riotStreamUrl && riotStreamUrl.trim()) {
    streams.push({
      name: "Watch Live",
      url: riotStreamUrl.trim(),
      icon: "riot",
      badge: "LIVE FEED",
    });
  }

  const slug = (leagueSlug || "").toLowerCase();
  if (slug.includes("lck")) {
    streams.push(
      { name: "LCK Twitch", url: "https://www.twitch.tv/lck", icon: "twitch" },
      { name: "LCK YouTube", url: "https://www.youtube.com/@LCKglobal/live", icon: "youtube" },
      { name: "LoLEsports", url: "https://lolesports.com", icon: "riot" }
    );
  } else if (slug.includes("lpl")) {
    streams.push(
      { name: "LPL Twitch", url: "https://www.twitch.tv/lpl", icon: "twitch" },
      { name: "LPL YouTube", url: "https://www.youtube.com/@LPL/live", icon: "youtube" },
      { name: "LoLEsports", url: "https://lolesports.com", icon: "riot" }
    );
  } else if (slug.includes("lec")) {
    streams.push(
      { name: "LEC Twitch", url: "https://www.twitch.tv/lec", icon: "twitch" },
      { name: "LEC YouTube", url: "https://www.youtube.com/@LEC/live", icon: "youtube" },
      { name: "LoLEsports", url: "https://lolesports.com", icon: "riot" }
    );
  } else if (slug.includes("lcs")) {
    streams.push(
      { name: "LCS Twitch", url: "https://www.twitch.tv/lcs", icon: "twitch" },
      { name: "LCS YouTube", url: "https://www.youtube.com/@LCS/live", icon: "youtube" },
      { name: "LoLEsports", url: "https://lolesports.com", icon: "riot" }
    );
  } else if (slug.includes("lcp") || slug.includes("pacific") || slug.includes("pcs")) {
    streams.push(
      { name: "LCP Twitch", url: "https://www.twitch.tv/lolesportspacific", icon: "twitch" },
      { name: "LCP YouTube", url: "https://www.youtube.com/@lolesportspacific/live", icon: "youtube" },
      { name: "LoLEsports", url: "https://lolesports.com", icon: "riot" }
    );
  } else if (slug.includes("cblol") || slug.includes("brazil")) {
    streams.push(
      { name: "CBLOL Twitch", url: "https://www.twitch.tv/cblol", icon: "twitch" },
      { name: "CBLOL YouTube", url: "https://www.youtube.com/@CBLOLoficial/live", icon: "youtube" },
      { name: "LoLEsports", url: "https://lolesports.com", icon: "riot" }
    );
  } else if (slug.includes("emea") || slug.includes("masters")) {
    streams.push(
      { name: "EMEA Twitch", url: "https://www.twitch.tv/emeamasters", icon: "twitch" },
      { name: "OTP LoL (FR)", url: "https://www.twitch.tv/otplol_", icon: "twitch" },
      { name: "Prime League (DE)", url: "https://www.twitch.tv/primeleague", icon: "twitch" },
      { name: "LoLEsports", url: "https://lolesports.com", icon: "riot" }
    );
  } else {
    // International tournaments (Worlds, MSI, First Stand) & general default
    streams.push(
      { name: "Riot Twitch", url: "https://www.twitch.tv/riotgames", icon: "twitch" },
      { name: "LoL YouTube", url: "https://www.youtube.com/@lolesports/live", icon: "youtube" },
      { name: "LoLEsports", url: "https://lolesports.com", icon: "riot" }
    );
  }

  return streams;
}

/**
 * Formats the header 24/7 Twitch stream title pill showing what stage, year, and match.
 * If stream is offline or outside airing window, returns offline status.
 */
export function formatStreamHeaderTitle(e: StreamEvent | null): { title: string; isLive: boolean } {
  if (!e) {
    return { title: "Twitch 24/7: Offline", isLive: false };
  }

  // Extract 4-digit year from season (e.g. "S13 (2023)" -> "2023", "2024" -> "2024")
  let year = "";
  if (e.season) {
    const m = e.season.match(/\b(20\d\d)\b/);
    year = m ? m[1] : e.season;
  }

  const stage = e.stage || e.event || "";
  const match = e.team1 && e.team2 ? `${e.team1} vs ${e.team2}` : e.name || "";

  // Combine: "Twitch 24/7: [Year] [Stage] · [Match]" (e.g. "Twitch 24/7: 2023 Finals · WBG vs T1")
  const details: string[] = [];
  if (year && stage) {
    details.push(`${year} ${stage}`);
  } else if (year || stage) {
    details.push(year || stage);
  }

  if (match) {
    details.push(match);
  }

  if (details.length > 0) {
    return { title: `Twitch 24/7: ${details.join(" · ")}`, isLive: true };
  }

  return { title: "Twitch 24/7: Airing Now", isLive: true };
}

/**
 * Determines whether a match matches the user's watchlist:
 * 1. Followed team (team1Code or team2Code in settings.followedTeams)
 * 2. Followed league (leagueSlug or lowercase leagueName in settings.followedLeagues)
 * 3. Followed region (if user follows the region associated with this league)
 */
export function isMatchFollowed(
  m: Match,
  settings: AppSettings,
  leaguesCatalog?: League[]
): boolean {
  if (
    settings.followedTeams.includes(m.team1Code) ||
    settings.followedTeams.includes(m.team2Code)
  ) {
    return true;
  }

  const slug = (m.leagueSlug || "").toLowerCase();
  const name = (m.leagueName || "").toLowerCase();

  if (
    settings.followedLeagues.some(
      (l) => l.toLowerCase() === slug || l.toLowerCase() === name
    )
  ) {
    return true;
  }

  // Region check against catalog
  if (settings.followedRegions && settings.followedRegions.length > 0 && leaguesCatalog) {
    const l = leaguesCatalog.find(
      (item) => item.slug.toLowerCase() === slug || item.name.toLowerCase() === name
    );
    if (l?.region && settings.followedRegions.includes(l.region.toUpperCase())) {
      return true;
    }
  }

  return false;
}

/**
 * Reconciles Riot's live matches (/getLive) with scheduled matches (/getSchedule).
 * Ensures legitimate inProgress matches from either source are captured,
 * while preventing fake/synthetic placeholders from ever appearing in liveMatches.
 */
export function reconcileLiveAndSchedule(
  liveMatches: Match[],
  scheduleMatches: Match[]
): { finalLive: Match[]; finalSchedule: Match[] } {
  const finalLive: Match[] = [];
  const liveById = new Set<string>();

  // Add all legitimate live matches from getLive
  for (const lm of liveMatches) {
    if (lm.team1Code === "LIVE" || lm.team2Code === "AIR") continue;
    if (!liveById.has(lm.matchId)) {
      liveById.add(lm.matchId);
      finalLive.push(lm);
    }
  }

  // Also check if schedule has any matches legitimately marked inProgress by Riot
  const updatedSchedule = scheduleMatches.map((sm) => {
    if (sm.state === "inProgress" && !liveById.has(sm.matchId)) {
      liveById.add(sm.matchId);
      finalLive.push(sm);
    }
    return sm;
  });

  return { finalLive, finalSchedule: updatedSchedule };
}
