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

export interface HeadToHeadStats {
  team1Wins: number;
  team2Wins: number;
  totalMeetings: number;
  totalMatches: number;
  team1GameWins: number;
  team2GameWins: number;
  lastWinner?: string;
  lastDate?: string;
}

export function computeHeadToHead(
  team1Code: string,
  team2Code: string,
  schedule: Match[]
): HeadToHeadStats | null {
  const c1 = (team1Code || "").trim().toUpperCase();
  const c2 = (team2Code || "").trim().toUpperCase();
  if (!c1 || !c2 || c1 === c2 || c1 === "TBD" || c2 === "TBD") return null;

  const pastMatches = schedule
    .filter((m) => {
      if (m.state !== "completed") return false;
      const m1 = (m.team1Code || "").trim().toUpperCase();
      const m2 = (m.team2Code || "").trim().toUpperCase();
      return (m1 === c1 && m2 === c2) || (m1 === c2 && m2 === c1);
    })
    .sort((a, b) => new Date(b.startTimeUtc).getTime() - new Date(a.startTimeUtc).getTime());

  if (pastMatches.length === 0) return null;

  let team1Wins = 0;
  let team2Wins = 0;
  let team1GameWins = 0;
  let team2GameWins = 0;

  for (const m of pastMatches) {
    const isC1Team1 = (m.team1Code || "").trim().toUpperCase() === c1;
    const c1Score = isC1Team1 ? m.team1Score : m.team2Score;
    const c2Score = isC1Team1 ? m.team2Score : m.team1Score;

    team1GameWins += c1Score;
    team2GameWins += c2Score;

    if (c1Score > c2Score) team1Wins++;
    else if (c2Score > c1Score) team2Wins++;
  }

  const last = pastMatches[0];
  const isLastC1Team1 = (last.team1Code || "").trim().toUpperCase() === c1;
  const lastC1Score = isLastC1Team1 ? last.team1Score : last.team2Score;
  const lastC2Score = isLastC1Team1 ? last.team2Score : last.team1Score;
  const lastWinner = lastC1Score > lastC2Score ? c1 : c2;

  return {
    team1Wins,
    team2Wins,
    totalMeetings: pastMatches.length,
    totalMatches: pastMatches.length,
    team1GameWins,
    team2GameWins,
    lastWinner,
    lastDate: last.startTimeUtc,
  };
}

export interface TeamStanding {
  teamCode: string;
  teamName: string;
  teamImage?: string;
  seriesWon: number;
  seriesLost: number;
  seriesPlayed: number;
  gamesWon: number;
  gamesLost: number;
  gameDiff: number;
  winRatePct: number;
  streak: string;
}

export function computeLeagueStandings(
  leagueSlug: string,
  schedule: Match[]
): TeamStanding[] {
  const slug = (leagueSlug || "").toLowerCase();
  const completed = schedule.filter(
    (m) => m.state === "completed" && (!slug || m.leagueSlug?.toLowerCase() === slug)
  );

  const statsMap = new Map<
    string,
    {
      code: string;
      name: string;
      image?: string;
      sWon: number;
      sLost: number;
      gWon: number;
      gLost: number;
      results: boolean[];
    }
  >();

  const getOrCreate = (code: string, name: string, image?: string) => {
    const upper = code.toUpperCase();
    if (!statsMap.has(upper)) {
      statsMap.set(upper, {
        code: upper,
        name: name || upper,
        image,
        sWon: 0,
        sLost: 0,
        gWon: 0,
        gLost: 0,
        results: [],
      });
    }
    const item = statsMap.get(upper)!;
    if (!item.image && image) item.image = image;
    return item;
  };

  const sorted = [...completed].sort(
    (a, b) => new Date(a.startTimeUtc).getTime() - new Date(b.startTimeUtc).getTime()
  );

  for (const m of sorted) {
    if (!m.team1Code || !m.team2Code || m.team1Code === "TBD" || m.team2Code === "TBD") continue;
    const t1 = getOrCreate(m.team1Code, m.team1Name, m.team1Image);
    const t2 = getOrCreate(m.team2Code, m.team2Name, m.team2Image);

    t1.gWon += m.team1Score;
    t1.gLost += m.team2Score;
    t2.gWon += m.team2Score;
    t2.gLost += m.team1Score;

    if (m.team1Score > m.team2Score) {
      t1.sWon++;
      t2.sLost++;
      t1.results.push(true);
      t2.results.push(false);
    } else if (m.team2Score > m.team1Score) {
      t2.sWon++;
      t1.sLost++;
      t2.results.push(true);
      t1.results.push(false);
    }
  }

  const standings: TeamStanding[] = Array.from(statsMap.values()).map((s) => {
    const sPlayed = s.sWon + s.sLost;
    const winRate = sPlayed > 0 ? Math.round((s.sWon / sPlayed) * 100) : 0;

    let streak = "-";
    if (s.results.length > 0) {
      const last = s.results[s.results.length - 1];
      let count = 0;
      for (let i = s.results.length - 1; i >= 0; i--) {
        if (s.results[i] === last) count++;
        else break;
      }
      streak = `${count}${last ? "W" : "L"}`;
    }

    return {
      teamCode: s.code,
      teamName: s.name,
      teamImage: s.image,
      seriesWon: s.sWon,
      seriesLost: s.sLost,
      seriesPlayed: sPlayed,
      gamesWon: s.gWon,
      gamesLost: s.gLost,
      gameDiff: s.gWon - s.gLost,
      winRatePct: winRate,
      streak,
    };
  });

  return standings.sort((a, b) => {
    if (b.seriesWon !== a.seriesWon) return b.seriesWon - a.seriesWon;
    if (b.gameDiff !== a.gameDiff) return b.gameDiff - a.gameDiff;
    return b.gamesWon - a.gamesWon;
  });
}

/**
 * Procedurally synthesizes a crisp, elegant LoL-style hextech kickoff chime
 * using the browser Web Audio API (0 KB disk asset overhead).
 */
export function playKickoffChime(): void {
  try {
    const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const notes = [523.25, 659.25, 783.99, 1046.5]; // C5, E5, G5, C6 (Hextech ascending fanfare)
    const now = ctx.currentTime;

    notes.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, now + idx * 0.08);

      gain.gain.setValueAtTime(0.001, now + idx * 0.08);
      gain.gain.exponentialRampToValueAtTime(0.08, now + idx * 0.08 + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.08 + 0.35);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now + idx * 0.08);
      osc.stop(now + idx * 0.08 + 0.4);
    });
  } catch (e) {
    // Audio context unavailable or user blocked autoplay
  }
}


