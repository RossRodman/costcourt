import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/api";
import { queryKeys } from "@/constants";
import type { DebateRequest } from "@/types";

export function useStartDebate() {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (body: DebateRequest) => api.startDebate(body),
    onSuccess: (debate) => {
      client.setQueryData(queryKeys.debate(debate.id), debate);
      void client.invalidateQueries({ queryKey: queryKeys.debates, exact: true });
    },
  });
}
