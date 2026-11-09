import type { LucideIcon } from "lucide-react";
import { NavLink as RouterNavLink } from "react-router";

import { cn } from "@/utils/cn";

interface NavLinkProps {
  to: string;
  label: string;
  icon: LucideIcon;
}

export function NavLink({ to, label, icon: Icon }: NavLinkProps) {
  return (
    <RouterNavLink
      to={to}
      className={({ isActive }) =>
        cn(
          "inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs transition-colors hover:bg-surface-raised hover:text-ink",
          isActive ? "text-ink" : "text-ink-muted",
        )
      }
    >
      <Icon className="size-4" aria-hidden />
      {label}
    </RouterNavLink>
  );
}
