import { describe, expect, it } from "vitest";

import { api, describeDetail } from "@/api";

describe("describeDetail", () => {
  it("passes plain messages through", () => {
    expect(describeDetail("ANTHROPIC_API_KEY is not set")).toBe("ANTHROPIC_API_KEY is not set");
  });

  it("summarises validation errors", () => {
    const detail = [
      { loc: ["body", "items", 0, "quantity"], msg: "Input should be greater than 0" },
      { loc: ["body"], msg: "duplicate line item ids: 01.010" },
    ];
    expect(describeDetail(detail)).toBe(
      "items.0.quantity: Input should be greater than 0\nduplicate line item ids: 01.010",
    );
    expect(describeDetail({})).toBeNull();
  });
});

describe("reportExportUrl", () => {
  it("opens the report inline by default", () => {
    expect(api.reportExportUrl("abc", "html")).toBe("/api/reports/abc/export?format=html");
  });

  it("asks for a download when requested", () => {
    expect(api.reportExportUrl("abc", "markdown", { download: true })).toBe(
      "/api/reports/abc/export?format=markdown&download=true",
    );
  });

  it("escapes the id", () => {
    expect(api.reportExportUrl("a/b", "json")).toBe("/api/reports/a%2Fb/export?format=json");
  });
});
