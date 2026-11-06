import { ArrowRight } from "lucide-react";
import { Link } from "react-router";

import { Badge } from "@/components/ui";
import { StatusBadge } from "@/components/statusBadge";
import { useRecentDebates } from "@/features/home/hooks";
import { formatRelative } from "@/utils/format";

export function RecentDebates() {
  const { data: debates } = useRecentDebates();

  if (!debates?.length) return null;

  return (
    <section aria-labelledby="recent" className="space-y-4">
      <h2 id="recent" className="text-xl font-semibold tracking-tight">
        Recent debates
      </h2>

      <ul className="divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface">
        {debates.slice(0, 8).map((debate) => (
          <li key={debate.id}>
            <Link
              to={`/debates/${debate.id}`}
              className="group flex items-center gap-3 px-5 py-3 transition-colors hover:bg-surface-raised"
            >
              <StatusBadge status={debate.status} />
              <span className="min-w-0 flex-1 truncate text-sm">{debate.estimate_title}</span>
              {debate.demo && <Badge>demo</Badge>}
              <span className="hidden text-xs text-ink-faint sm:inline">
                {debate.rounds} {debate.rounds === 1 ? "round" : "rounds"} ·{" "}
                {formatRelative(debate.created_at)}
              </span>
              <ArrowRight
                className="size-4 text-ink-faint transition-transform group-hover:translate-x-0.5"
                aria-hidden
              />
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
