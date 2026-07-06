import { describe, it, expect } from "vitest";
import { severityColor, formatDate, truncate } from "@/lib/utils";

describe("utils", () => {
  it("returns correct severity colors", () => {
    expect(severityColor("critical")).toBe("#ef4444");
    expect(severityColor("medium")).toBe("#eab308");
    expect(severityColor("unknown")).toBe("#8a93a6");
  });

  it("formats dates", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate(undefined)).toBe("—");
  });

  it("truncates long strings", () => {
    expect(truncate("a".repeat(300), 10)).toHaveLength(10);
  });
});
