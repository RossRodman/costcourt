export const queryKeys = {
  health: ["health"] as const,
  samples: ["estimates", "samples"] as const,
  sample: (id: string) => ["estimates", "samples", id] as const,
  debates: ["debates"] as const,
  debate: (id: string) => ["debates", id] as const,
  demos: ["debates", "demos"] as const,
};
