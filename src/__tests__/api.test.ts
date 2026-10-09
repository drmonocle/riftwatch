import { describe, expect, it } from "vitest";
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
