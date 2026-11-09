import { cn } from "@/utils/cn";

export type EstimateSource = "samples" | "upload";

const TABS: { value: EstimateSource; label: string }[] = [
  { value: "samples", label: "Samples" },
  { value: "upload", label: "Upload JSON" },
];

interface SourceTabsProps {
  value: EstimateSource;
  onChange: (value: EstimateSource) => void;
}

export function SourceTabs({ value, onChange }: SourceTabsProps) {
  return (
    <div
      role="tablist"
      aria-label="Estimate source"
      className="flex rounded-xl border border-line bg-surface p-1"
    >
      {TABS.map((tab) => (
        <button
          key={tab.value}
          type="button"
          role="tab"
          aria-selected={value === tab.value}
          onClick={() => onChange(tab.value)}
          className={cn(
            "rounded-lg px-3 py-1.5 text-sm transition-colors",
            value === tab.value ? "bg-surface-raised text-ink" : "text-ink-muted hover:text-ink",
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
