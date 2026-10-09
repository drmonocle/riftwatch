import { describe, expect, it } from "vitest";
import { pickCurrentTournament } from "../api";

describe("pickCurrentTournament", () => {
  const t = (id: string, start: string, end: string) => ({ id, slug: id, startDate: start, endDate: end });
  // newest first, as fetchLeagueTournaments returns them
  const list = [t("next", "2026-11-01", "2026-11-20"), t("now", "2026-10-01", "2026-10-15"), t("old", "2026-07-01", "2026-09-10")];
  it("prefers the tournament running today", () => {
    expect(pickCurrentTournament(list, "2026-10-09")?.id).toBe("now");
  });
  it("falls back to the most recently finished one between splits", () => {
    expect(pickCurrentTournament(list, "2026-10-20")?.id).toBe("now");
    expect(pickCurrentTournament(list.filter((x) => x.id !== "now"), "2026-10-20")?.id).toBe("old");
  });
  it("shows the next tournament when nothing has been played yet", () => {
    expect(pickCurrentTournament([t("only", "2026-12-01", "2026-12-10")], "2026-10-09")?.id).toBe("only");
    expect(pickCurrentTournament([], "2026-10-09")).toBeUndefined();
  });
});
import { buildStreamUrl, compareSemver } from "../api";

describe("compareSemver", () => {
  it("orders versions numerically, not lexically", () => {
    expect(compareSemver("0.3.10", "0.3.9")).toBe(1);
    expect(compareSemver("v1.0.0", "1.0.0")).toBe(0);
    expect(compareSemver("0.3.5", "0.3.6")).toBe(-1);
    expect(compareSemver("1.0", "1.0.0")).toBe(0);
  });
});

describe("buildStreamUrl", () => {
  it("returns empty for missing streams", () => {
    expect(buildStreamUrl(undefined)).toBe("");
    expect(buildStreamUrl([])).toBe("");
  });
  it("prefers English streams and encodes the channel", () => {
    const url = buildStreamUrl([
      { provider: "twitch", parameter: "lck_korea", locale: "ko-KR" },
      { provider: "twitch", parameter: "lck", locale: "en-US" },
    ]);
    expect(url).toBe("https://www.twitch.tv/lck");
    expect(buildStreamUrl([{ provider: "youtube", parameter: "a b" }])).toBe("https://www.youtube.com/watch?v=a%20b");
  });
  it("passes through explicit http(s) links and rejects unknown providers", () => {
    expect(buildStreamUrl([{ provider: "x", parameter: "https://example.com/s" }])).toBe("https://example.com/s");
    expect(buildStreamUrl([{ provider: "mystery", parameter: "abc" }])).toBe("");
  });
});
