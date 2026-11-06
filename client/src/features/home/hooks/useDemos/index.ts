import { useQuery } from "@tanstack/react-query";

import { api } from "@/api";
import { queryKeys } from "@/constants";

export function useDemos() {
  return useQuery({ queryKey: queryKeys.demos, queryFn: api.demos, staleTime: Infinity });
}
