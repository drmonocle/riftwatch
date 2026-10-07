import { Match, StreamEvent } from "./types";

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
