import { RoleAvatar } from "@/components/roleAvatar";
import { TypingDots } from "@/components/ui";
import { ROLES } from "@/constants";
import type { Role } from "@/types";
import { cn } from "@/utils/cn";

interface ThinkingCardProps {
  role: Role;
  label?: string;
}

export function ThinkingCard({ role, label }: ThinkingCardProps) {
  const meta = ROLES[role];
  return (
    <div
      role="status"
      className={cn(
        "flex animate-in items-center gap-3 rounded-2xl border border-l-2 border-dashed border-line bg-surface/60 p-5",
        meta.border,
      )}
    >
      <RoleAvatar role={role} />
      <div className="flex items-center gap-2 text-sm text-ink-muted">
        {label ?? `${meta.title} is reviewing the estimate`}
        <TypingDots className="text-ink-faint" />
      </div>
    </div>
  );
}
