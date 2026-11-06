import { CircleAlert, Info } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/utils/cn";

const TONES = {
  error: { icon: CircleAlert, className: "border-rose-400/30 bg-rose-400/5 text-rose-200" },
  info: { icon: Info, className: "border-estimator/30 bg-estimator/5 text-amber-100" },
} as const;

interface AlertProps {
  tone?: keyof typeof TONES;
  title?: ReactNode;
  children?: ReactNode;
  className?: string;
}

export function Alert({ tone = "error", title, children, className }: AlertProps) {
  const { icon: Icon, className: toneClass } = TONES[tone];

  return (
    <div
      role={tone === "error" ? "alert" : "note"}
      className={cn("flex gap-3 rounded-xl border px-4 py-3 text-sm", toneClass, className)}
    >
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="min-w-0 space-y-1">
        {title && <p className="font-medium">{title}</p>}
        {children && <div className="whitespace-pre-line opacity-90">{children}</div>}
      </div>
    </div>
  );
}
