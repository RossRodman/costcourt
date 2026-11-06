import { Gavel, Lightbulb } from "lucide-react";

import { Badge, Card } from "@/components/ui";
import { lineChanges } from "@/features/debate/utils/lineChanges";
import { FigureChanges } from "@/features/debate/components/figureChanges";
import { RoleAvatar } from "@/components/roleAvatar";
import { DECISIONS, ROLES } from "@/constants";
import type { CostImpact, Ruling, Verdict, Estimate } from "@/types";
import { formatMoney, formatMoneyDelta, formatPercent } from "@/utils/format";
import { cn } from "@/utils/cn";

interface VerdictPanelProps {
  verdict: Verdict;
  estimate: Estimate | null;
  impact: CostImpact | null;
}

export function VerdictPanel({ verdict, estimate, impact }: VerdictPanelProps) {
  return (
    <section aria-labelledby="verdict" className="animate-in space-y-6">
      <Card className="overflow-hidden border-judge/30">
        <div className="bg-radial-[at_0%_0%] from-judge/15 to-transparent to-60% p-6">
          <div className="flex items-center gap-3">
            <RoleAvatar role="judge" size="lg" />
            <div>
              <p className="text-xs font-medium tracking-wide text-judge uppercase">Verdict</p>
              <h2 id="verdict" className="text-xl font-semibold tracking-tight">
                The judge has ruled
              </h2>
            </div>
          </div>
          <p className="mt-4 text-pretty text-ink-muted">{verdict.summary}</p>

          <div className="mt-6 grid gap-3 sm:grid-cols-4">
            {impact && estimate && <ImpactStats impact={impact} currency={estimate.currency} />}
            <Confidence value={verdict.confidence} />
          </div>
        </div>
      </Card>

      {verdict.rulings.length > 0 && (
        <div className="space-y-3">
          <h3 className="flex items-center gap-2 text-sm font-medium">
            <Gavel className="size-4 text-judge" aria-hidden />
            Rulings
            <span className="text-ink-faint">({verdict.rulings.length})</span>
          </h3>
          <ul className="space-y-3">
            {verdict.rulings.map((ruling) => (
              <RulingItem key={ruling.line_item_id} ruling={ruling} estimate={estimate} />
            ))}
          </ul>
        </div>
      )}

      {verdict.recommendations.length > 0 && (
        <Card className="p-5">
          <h3 className="flex items-center gap-2 text-sm font-medium">
            <Lightbulb className="size-4 text-estimator" aria-hidden />
            Recommendations
          </h3>
          <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-ink-muted marker:text-ink-faint">
            {verdict.recommendations.map((text) => (
              <li key={text} className="pl-1 text-pretty">
                {text}
              </li>
            ))}
          </ol>
        </Card>
      )}
    </section>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="rounded-xl border border-line bg-canvas/40 px-4 py-3">
      <p className="text-xs text-ink-faint">{label}</p>
      <p className={cn("mt-1 font-mono text-lg tabular-nums", tone)}>{value}</p>
    </div>
  );
}

function ImpactStats({ impact, currency }: { impact: CostImpact; currency: string }) {
  const tone = impact.delta > 0 ? "text-amber-300" : impact.delta < 0 ? "text-sky-300" : "text-ink";

  return (
    <>
      <Stat
        label="Original total"
        value={formatMoney(impact.original_total, currency, { whole: true })}
      />
      <Stat
        label="Revised total"
        value={formatMoney(impact.revised_total, currency, { whole: true })}
      />
      <Stat
        label={`Change (${formatPercent(impact.delta_pct, { signed: true })})`}
        value={formatMoneyDelta(impact.delta, currency, { whole: true })}
        tone={tone}
      />
    </>
  );
}

function Confidence({ value }: { value: number }) {
  const pct = Math.round(value * 100);

  return (
    <div className="rounded-xl border border-line bg-canvas/40 px-4 py-3">
      <p className="text-xs text-ink-faint">Judge's confidence</p>
      <p className="mt-1 font-mono text-lg tabular-nums">{pct}%</p>
      <div
        role="meter"
        aria-label="Judge's confidence"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        className="mt-2 h-1 overflow-hidden rounded-full bg-line"
      >
        <div className="h-full rounded-full bg-judge" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function RulingItem({ ruling, estimate }: { ruling: Ruling; estimate: Estimate | null }) {
  const item = estimate?.items.find((i) => i.id === ruling.line_item_id);
  const decision = DECISIONS[ruling.decision];
  const currency = estimate?.currency ?? "USD";

  const changes = item
    ? lineChanges(item, currency, ruling.approved_quantity, ruling.approved_unit_rate)
    : [];

  return (
    <li className="rounded-2xl border border-line bg-surface p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={decision.tone}>{decision.label}</Badge>
        <span className="font-mono text-xs text-ink-faint">{ruling.line_item_id}</span>
        {item && <span className="text-sm">{item.description}</span>}
        {ruling.sided_with.length > 0 && (
          <span className="ml-auto flex items-center gap-1" aria-label="Sided with">
            {ruling.sided_with.map((role) => (
              <RoleAvatar key={role} role={role} size="sm" />
            ))}
            <span className="sr-only">
              {ruling.sided_with.map((role) => ROLES[role].title).join(", ")}
            </span>
          </span>
        )}
      </div>

      {changes.length > 0 && (
        <div className="mt-3">
          <FigureChanges changes={changes} />
        </div>
      )}

      <p className="mt-3 text-sm text-pretty text-ink-muted">{ruling.reasoning}</p>
    </li>
  );
}
