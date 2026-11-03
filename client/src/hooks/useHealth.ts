import { useEffect, useState } from "react";

import { api, type Health } from "@/lib/api";

export type HealthState =
  { kind: "loading" } | { kind: "online"; health: Health } | { kind: "offline" };

export function useHealth(): HealthState {
  const [state, setState] = useState<HealthState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();

    api
      .health(controller.signal)
      .then((health) => setState({ kind: "online", health }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "offline" });
      });

    return () => controller.abort();
  }, []);

  return state;
}
