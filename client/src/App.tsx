import { Gavel, HardHat, type LucideIcon, Ruler, Scale } from "lucide-react";

import { StatusPill } from "@/components/StatusPill";
import { useHealth } from "@/hooks/useHealth";
import { cn } from "@/lib/utils";

interface Role {
  name: string;
  blurb: string;
  icon: LucideIcon;
  accent: string;
}

const ROLES: Role[] = [
  {
    name: "Estimator",
    blurb: "Defends the quantities, unit rates and totals.",
    icon: Ruler,
    accent: "text-estimator bg-estimator/10 ring-estimator/25",
  },
  {
    name: "Engineer",
    blurb: "Hunts for scope gaps, wrong specs and quantity errors.",
    icon: HardHat,
    accent: "text-engineer bg-engineer/10 ring-engineer/25",
  },
  {
    name: "Contractor's advocate",
    blurb: "Argues for realistic labour, logistics, risk and margin.",
    icon: Scale,
    accent: "text-advocate bg-advocate/10 ring-advocate/25",
  },
  {
    name: "Judge",
    blurb: "Rules on every disputed line and explains why.",
    icon: Gavel,
    accent: "text-judge bg-judge/10 ring-judge/25",
  },
];

export function App() {
  const health = useHealth();

  return (
    <div className="relative min-h-dvh overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-radial-[at_50%_0%] from-judge/15 to-transparent to-70%"
      />

      <nav className="relative mx-auto flex max-w-5xl items-center justify-between px-6 pt-6">
        <a href="/" className="flex items-center gap-2.5 font-semibold tracking-tight">
          <img src="/favicon.svg" alt="" className="size-7" />
          CostCourt
        </a>
        <StatusPill state={health} />
      </nav>

      <main className="relative mx-auto flex max-w-5xl flex-col gap-14 px-6 pt-16 pb-20">
        <header className="flex flex-col items-start gap-6">
          <p className="text-sm font-medium tracking-wide text-judge uppercase">
            Put your estimate on trial
          </p>
          <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
            Construction estimates, <span className="text-judge">argued out</span> before you sign.
          </h1>
          <p className="max-w-2xl text-lg text-pretty text-ink-muted">
            Three AI agents debate every line of your estimate. A judge weighs the arguments and
            issues a ruling, and the full reasoning lands in an auditable report.
          </p>
        </header>

        <section aria-label="Debate roles" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {ROLES.map(({ name, blurb, icon: Icon, accent }) => (
            <article
              key={name}
              className="rounded-2xl border border-line bg-surface p-5 transition-colors hover:bg-surface-raised"
            >
              <span
                className={cn(
                  "inline-flex size-10 items-center justify-center rounded-xl ring-1",
                  accent,
                )}
              >
                <Icon className="size-5" aria-hidden />
              </span>
              <h2 className="mt-4 font-medium">{name}</h2>
              <p className="mt-1 text-sm text-ink-muted">{blurb}</p>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}
