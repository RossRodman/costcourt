import type { HTMLAttributes } from "react";

import { cn } from "@/utils/cn";

export function Badge({
  tone = "text-ink-muted bg-surface-raised ring-line",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap ring-1 ring-inset",
        tone,
        className,
      )}
      {...props}
    />
  );
}
