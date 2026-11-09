import { useQuery } from "@tanstack/react-query";

import { api } from "@/api";
import { queryKeys } from "@/constants";

export function useDebate(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.debate(id ?? ""),
    queryFn: () => api.debate(id ?? ""),
    enabled: Boolean(id),
    retry: false,
  });
}
