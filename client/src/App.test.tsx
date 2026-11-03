import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "@/App";
import type { Health } from "@/lib/api";

function mockHealth(response: Partial<Health> | Error) {
  vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
    response instanceof Error
      ? Promise.reject(response)
      : Response.json({ status: "ok", version: "0.1.0", env: "test", ...response }),
  );
}

describe("App", () => {
  it("introduces all four debate roles", () => {
    mockHealth({ llm_configured: true });
    render(<App />);

    for (const role of ["Estimator", "Engineer", "Contractor's advocate", "Judge"]) {
      expect(screen.getByRole("heading", { name: role })).toBeInTheDocument();
    }
  });

  it("shows the backend as online", async () => {
    mockHealth({ llm_configured: true });
    render(<App />);
    expect(await screen.findByText("API online")).toBeInTheDocument();
  });

  it("warns when the Claude key is missing", async () => {
    mockHealth({ llm_configured: false });
    render(<App />);
    expect(await screen.findByText(/no Claude key/)).toBeInTheDocument();
  });

  it("shows the backend as offline when the request fails", async () => {
    mockHealth(new TypeError("Failed to fetch"));
    render(<App />);
    expect(await screen.findByText("API offline")).toBeInTheDocument();
  });
});
