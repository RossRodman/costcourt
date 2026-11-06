import { useQuery } from "@tanstack/react-query";

import { api } from "@/api";
import { queryKeys } from "@/constants";

export function useRecentDebates() {
  return useQuery({ queryKey: queryKeys.debates, queryFn: api.debates, refetchInterval: 10_000 });
}
