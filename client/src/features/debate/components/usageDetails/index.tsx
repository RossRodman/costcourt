import { ChevronDown } from "lucide-react";

import { ROLES } from "@/constants";
import type { LLMUsage } from "@/types";
import { formatTokens } from "@/utils/format";

interface UsageDetailsProps {
  usage: LLMUsage[];
}

export function UsageDetails({ usage }: UsageDetailsProps) {
  if (usage.length === 0) return null;

  const total = usage.reduce((sum, u) => sum + u.input_tokens + u.output_tokens, 0);
  const cached = usage.reduce((sum, u) => sum + u.cache_read_tokens, 0);

  return (
    <details className="group rounded-2xl border border-line bg-surface">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 text-sm">
        <span>
          <span className="font-medium">Model calls</span>
          <span className="ml-2 text-ink-faint">
            {usage.length} calls · {formatTokens(total)} tokens
            {cached > 0 && ` · ${formatTokens(cached)} from cache`}
          </span>
        </span>

        <ChevronDown
          className="size-4 text-ink-faint transition-transform group-open:rotate-180"
          aria-hidden
        />
      </summary>

      <div className="overflow-x-auto px-5 pb-4">
        <table className="w-full text-xs tabular-nums">
          <thead>
            <tr className="border-b border-line text-left text-ink-faint">
              <th className="py-2 pr-3 font-medium">Agent</th>
              <th className="py-2 pr-3 font-medium">Round</th>
              <th className="py-2 pr-3 font-medium">Model</th>
              <th className="py-2 pr-3 text-right font-medium">Input</th>
              <th className="py-2 pr-3 text-right font-medium">Cached</th>
              <th className="py-2 text-right font-medium">Output</th>
            </tr>
          </thead>

          <tbody className="text-ink-muted">
            {usage.map((u, i) => (
              <tr key={i} className="border-b border-line/60 last:border-0">
                <td className="py-1.5 pr-3 text-ink">{ROLES[u.role].title}</td>
                <td className="py-1.5 pr-3">{u.round ?? "—"}</td>
                <td className="py-1.5 pr-3 font-mono">{u.model}</td>
                <td className="py-1.5 pr-3 text-right">{formatTokens(u.input_tokens)}</td>
                <td className="py-1.5 pr-3 text-right">{formatTokens(u.cache_read_tokens)}</td>
                <td className="py-1.5 text-right">{formatTokens(u.output_tokens)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
