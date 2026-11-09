import { cn } from "@/utils/cn";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div aria-hidden className={cn("animate-pulse rounded-lg bg-surface-raised", className)} />
  );
}
