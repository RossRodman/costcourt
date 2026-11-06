import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/utils/cn";

const VARIANTS = {
  primary: "bg-judge text-canvas hover:bg-judge/90 focus-visible:outline-judge",
  secondary:
    "border border-line bg-surface-raised text-ink hover:bg-line/60 focus-visible:outline-ink-muted",
  ghost: "text-ink-muted hover:bg-surface-raised hover:text-ink focus-visible:outline-ink-muted",
} as const;

const SIZES = {
  sm: "h-8 gap-1.5 rounded-lg px-3 text-xs",
  md: "h-10 gap-2 rounded-xl px-4 text-sm",
  lg: "h-12 gap-2 rounded-xl px-6 text-base",
} as const;

export interface BaseButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof VARIANTS;
  size?: keyof typeof SIZES;
}

export function BaseButton({
  variant = "primary",
  size = "md",
  className,
  type = "button",
  ...props
}: BaseButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center font-medium whitespace-nowrap transition-colors",
        "focus-visible:outline-2 focus-visible:outline-offset-2",
        "disabled:pointer-events-none disabled:opacity-40",
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...props}
    />
  );
}
