import { cn } from "@/utils/cn";

interface TypingDotsProps {
  className?: string;
}

export function TypingDots({ className }: TypingDotsProps) {
  return (
    <span aria-hidden className={cn("inline-flex items-center gap-1", className)}>
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="size-1.5 animate-bounce rounded-full bg-current"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </span>
  );
}
