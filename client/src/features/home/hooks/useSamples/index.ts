import { useQuery } from "@tanstack/react-query";

import { api } from "@/api";
import { queryKeys } from "@/constants";

export function useSamples() {
  return useQuery({ queryKey: queryKeys.samples, queryFn: api.samples, staleTime: Infinity });
}
