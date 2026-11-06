import { CodeXml } from "lucide-react";

import { REPO_URL } from "@/constants";

export function SourceLink() {
  return (
    <a
      href={REPO_URL}
      target="_blank"
      rel="noreferrer"
      aria-label="Source code on GitHub"
      className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs text-ink-muted transition-colors hover:bg-surface-raised hover:text-ink"
    >
      <CodeXml className="size-4" aria-hidden />
      <span className="hidden sm:inline">Source</span>
    </a>
  );
}
