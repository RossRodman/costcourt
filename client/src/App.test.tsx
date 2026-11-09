import { render, screen } from "@testing-library/react";
import { createMemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";

import { App } from "@/App";
import { routes } from "@/app/router";
import { mockApi } from "@/test/utils";

function renderApp(health: object | Response) {
  mockApi({
    "GET /health": health,
    "GET /estimates/samples": [],
    "GET /debates/demos": [],
    "GET /debates": [],
  });
  render(<App router={createMemoryRouter(routes, { initialEntries: ["/"] })} />);
}

const ONLINE = { status: "ok", version: "0.1.0", env: "test" };

describe("App", () => {
  it("introduces all four debate roles", () => {
    renderApp({ ...ONLINE, llm_configured: true });
    for (const role of ["Estimator", "Engineer", "Contractor's advocate", "Judge"]) {
      expect(screen.getByText(role)).toBeInTheDocument();
    }
  });

  it("shows the backend as online", async () => {
    renderApp({ ...ONLINE, llm_configured: true });
    expect(await screen.findByText("API online")).toBeInTheDocument();
    expect(screen.getByText("v0.1.0")).toBeInTheDocument();
  });

  it("warns when the Claude key is missing", async () => {
    renderApp({ ...ONLINE, llm_configured: false });
    expect(await screen.findByText(/no Claude key/)).toBeInTheDocument();
  });

  it("shows the backend as offline when the request fails", async () => {
    renderApp(Response.json({ detail: "down" }, { status: 503 }));
    expect(await screen.findByText("API offline")).toBeInTheDocument();
  });
});
