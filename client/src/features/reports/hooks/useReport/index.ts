import { useQuery } from "@tanstack/react-query";

import { api } from "@/api";
import { queryKeys } from "@/constants";

export function useReport(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.report(id ?? ""),
    queryFn: () => api.report(id ?? ""),
    enabled: Boolean(id),
    // Saved reports never change.
    staleTime: Infinity,
  });
}
