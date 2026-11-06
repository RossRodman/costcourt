import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { vi } from "vitest";

import { routes } from "@/app/router";
import type { DebateEvent } from "@/types";
import demoEvents from "@/test/fixtures/demo-events.json";

export const DEMO_EVENTS = demoEvents as DebateEvent[];

export function renderRoute(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter(routes, { initialEntries: [path] });

  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return { router, client };
}

type Handler = (body: unknown) => unknown;

export function mockApi(handlers: Record<string, Handler | unknown>) {
  const calls: { key: string; body: unknown }[] = [];

  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = new URL(String(input), "http://localhost");
    const key = `${init?.method ?? "GET"} ${url.pathname.replace(/^\/api/, "")}`;
    const body: unknown = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ key, body });

    if (!(key in handlers)) {
      return Response.json({ detail: `unmocked ${key}` }, { status: 404 });
    }

    const handler = handlers[key];
    const result = typeof handler === "function" ? (handler as Handler)(body) : handler;

    return result instanceof Response ? result : Response.json(result);
  });

  return calls;
}

export class FakeEventSource {
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSED = 2;
  static instances: FakeEventSource[] = [];

  readonly url: string;
  readyState = FakeEventSource.OPEN;
  onerror: ((event: Event) => void) | null = null;
  private listeners = new Map<string, ((event: MessageEvent<string>) => void)[]>();

  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: (event: MessageEvent<string>) => void) {
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), listener]);
  }

  close() {
    this.readyState = FakeEventSource.CLOSED;
  }

  emit(id: number, event: DebateEvent) {
    const message = new MessageEvent(event.type, {
      data: JSON.stringify(event),
      lastEventId: String(id),
    });
    for (const listener of this.listeners.get(event.type) ?? []) listener(message);
  }

  fail() {
    this.readyState = FakeEventSource.CLOSED;
    this.onerror?.(new Event("error"));
  }

  static install() {
    FakeEventSource.instances = [];
    vi.stubGlobal("EventSource", FakeEventSource);
  }

  static get latest(): FakeEventSource {
    const source = FakeEventSource.instances.at(-1);
    if (!source) throw new Error("no EventSource was opened");
    return source;
  }
}
