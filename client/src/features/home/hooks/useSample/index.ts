import { useQuery } from "@tanstack/react-query";

import { api } from "@/api";
import { queryKeys } from "@/constants";

export function useSample(id: string | null) {
  return useQuery({
    queryKey: queryKeys.sample(id ?? ""),
    queryFn: () => api.sample(id ?? ""),
    enabled: Boolean(id),
    staleTime: Infinity,
  });
}
