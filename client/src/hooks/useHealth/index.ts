import { useQuery } from "@tanstack/react-query";

import { api, type Health } from "@/api";

export type HealthState =
  { kind: "loading" } | { kind: "online"; health: Health } | { kind: "offline" };

export function useHealth(): HealthState {
  const query = useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => api.health(signal),
    refetchInterval: 30_000,
    retry: false,
  });

  if (query.data) return { kind: "online", health: query.data };
  if (query.isError) return { kind: "offline" };

  return { kind: "loading" };
}

export function useLlmConfigured(): boolean {
  const health = useHealth();
  return health.kind === "online" && health.health.llm_configured;
}
