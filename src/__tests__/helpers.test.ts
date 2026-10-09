import { describe, expect, it } from "vitest";
import { isMatchCompleted, normalizeTeamCode, reconcileLiveAndSchedule, computeLeagueStandings } from "../helpers";
import type { Match } from "../types";

const match = (over: Partial<Match> = {}): Match => ({
  matchId: "m1",
  leagueName: "LCK",
  leagueSlug: "lck",
  blockName: "Week 1",
  startTimeUtc: "2026-01-01T10:00:00Z",
  state: "unstarted",
  bestOf: 3,
  team1Code: "T1",
  team1Name: "T1",
  team1Score: 0,
  team2Code: "GEN",
  team2Name: "Gen.G",
  team2Score: 0,
  games: [],
  ...over,
});

describe("normalizeTeamCode", () => {
  it("uppercases, trims and applies aliases", () => {
    expect(normalizeTeamCode(" t1 ")).toBe("T1");
    expect(normalizeTeamCode("tlaw")).toBe("TL");
    expect(normalizeTeamCode("")).toBe("");
  });
});

describe("isMatchCompleted", () => {
  it("is true when state is completed", () => {
    expect(isMatchCompleted(match({ state: "completed" }))).toBe(true);
  });
  it("uses the series win threshold for Bo3 and Bo5", () => {
    expect(isMatchCompleted(match({ bestOf: 3, team1Score: 1 }))).toBe(false);
    expect(isMatchCompleted(match({ bestOf: 3, team1Score: 2 }))).toBe(true);
    expect(isMatchCompleted(match({ bestOf: 5, team2Score: 2 }))).toBe(false);
    expect(isMatchCompleted(match({ bestOf: 5, team2Score: 3 }))).toBe(true);
    expect(isMatchCompleted(match({ bestOf: 1, team1Score: 1 }))).toBe(true);
  });
});

describe("reconcileLiveAndSchedule", () => {
  it("never puts finished matches in the live list and syncs the schedule", () => {
    const live = [match({ state: "inProgress", team1Score: 2 })];
    const sched = [match({ state: "inProgress" })];
    const { finalLive, finalSchedule } = reconcileLiveAndSchedule(live, sched);
    expect(finalLive).toHaveLength(0);
    expect(finalSchedule[0].state).toBe("completed");
    expect(finalSchedule[0].winner).toBe("T1");
  });

  it("keeps genuine in-progress matches and drops placeholders", () => {
    const live = [
      match({ matchId: "a", state: "inProgress", team1Score: 1 }),
      match({ matchId: "b", state: "inProgress", team1Code: "LIVE" }),
    ];
    const { finalLive } = reconcileLiveAndSchedule(live, []);
    expect(finalLive.map((m) => m.matchId)).toEqual(["a"]);
  });

  it("surfaces in-progress schedule entries missing from getLive, without duplicates", () => {
    const sched = [match({ matchId: "x", state: "inProgress" })];
    const { finalLive } = reconcileLiveAndSchedule([match({ matchId: "x", state: "inProgress" })], sched);
    expect(finalLive).toHaveLength(1);
  });
});

describe("computeLeagueStandings", () => {
  it("counts series and games for completed matches in the league only", () => {
    const sched = [
      match({ matchId: "1", state: "completed", team1Score: 2, team2Score: 1, winner: "T1" }),
      match({ matchId: "2", state: "completed", leagueSlug: "lpl", team1Score: 2, team2Score: 0 }),
      match({ matchId: "3", state: "unstarted" }),
    ];
    const table = computeLeagueStandings("lck", sched);
    const t1 = table.find((t) => t.teamCode === "T1");
    const gen = table.find((t) => t.teamCode === "GEN");
    expect(table).toHaveLength(2);
    expect(t1).toMatchObject({ seriesWon: 1, seriesLost: 0, gamesWon: 2, gamesLost: 1 });
    expect(gen).toMatchObject({ seriesWon: 0, seriesLost: 1 });
  });
});
