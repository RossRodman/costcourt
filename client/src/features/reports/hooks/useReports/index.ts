import { useQuery } from "@tanstack/react-query";

import { api } from "@/api";
import { queryKeys } from "@/constants";

export function useReports() {
  return useQuery({ queryKey: queryKeys.reports, queryFn: api.reports });
}
