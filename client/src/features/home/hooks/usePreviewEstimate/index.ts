import { useMutation } from "@tanstack/react-query";

import { api } from "@/api";

export function usePreviewEstimate() {
  return useMutation({ mutationFn: (estimate: unknown) => api.preview(estimate) });
}
