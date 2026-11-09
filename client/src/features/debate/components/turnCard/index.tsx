import { RoleAvatar } from "@/components/roleAvatar";
import { ROLES } from "@/constants";
import { ArgumentItem } from "@/features/debate/components/argumentItem";
import type { Estimate, Turn } from "@/types";
import { cn } from "@/utils/cn";

interface TurnCardProps {
  turn: Turn;
  estimate: Estimate | null;
}

export function TurnCard({ turn, estimate }: TurnCardProps) {
  const meta = ROLES[turn.role];
  return (
    <article
      aria-label={`${meta.title}, round ${turn.round}`}
      className={cn(
        "animate-in rounded-2xl border border-l-2 border-line bg-surface p-5",
        meta.border,
      )}
    >
      <header className="flex items-start gap-3">
        <RoleAvatar role={turn.role} />
        <div className="min-w-0">
          <h3 className="font-medium">{meta.title}</h3>
          <p className="mt-0.5 text-sm text-pretty text-ink-muted">{turn.summary}</p>
        </div>
      </header>

      {turn.arguments.length > 0 && (
        <ul className="mt-4 space-y-4 border-t border-line pt-4">
          {turn.arguments.map((argument, i) => (
            <ArgumentItem key={i} argument={argument} estimate={estimate} />
          ))}
        </ul>
      )}
    </article>
  );
}
