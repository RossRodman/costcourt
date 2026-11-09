import { Gavel, HardHat, type LucideIcon, Ruler, Scale } from "lucide-react";

import type { Decision, Role, Stance } from "@/types";

export interface RoleMeta {
  title: string;
  blurb: string;
  icon: LucideIcon;
  accent: string;
  solid: string;
  border: string;
}

export const ROLES: Record<Role, RoleMeta> = {
  estimator: {
    title: "Estimator",
    blurb: "Defends the quantities, unit rates and totals.",
    icon: Ruler,
    accent: "text-estimator bg-estimator/10 ring-estimator/25",
    solid: "bg-estimator",
    border: "border-l-estimator",
  },
  engineer: {
    title: "Engineer",
    blurb: "Hunts for scope gaps, wrong specs and quantity errors.",
    icon: HardHat,
    accent: "text-engineer bg-engineer/10 ring-engineer/25",
    solid: "bg-engineer",
    border: "border-l-engineer",
  },
  advocate: {
    title: "Contractor's advocate",
    blurb: "Argues for realistic labour, logistics, risk and margin.",
    icon: Scale,
    accent: "text-advocate bg-advocate/10 ring-advocate/25",
    solid: "bg-advocate",
    border: "border-l-advocate",
  },
  judge: {
    title: "Judge",
    blurb: "Rules on every disputed line and explains why.",
    icon: Gavel,
    accent: "text-judge bg-judge/10 ring-judge/25",
    solid: "bg-judge",
    border: "border-l-judge",
  },
};

export const ROLE_ORDER: readonly Role[] = ["estimator", "engineer", "advocate", "judge"];

export const STANCES: Record<Stance, { label: string; tone: string }> = {
  support: { label: "Support", tone: "text-emerald-300 bg-emerald-400/10 ring-emerald-400/25" },
  increase: { label: "Increase", tone: "text-amber-300 bg-amber-400/10 ring-amber-400/25" },
  decrease: { label: "Decrease", tone: "text-sky-300 bg-sky-400/10 ring-sky-400/25" },
  missing: { label: "Missing scope", tone: "text-rose-300 bg-rose-400/10 ring-rose-400/25" },
};

export const DECISIONS: Record<Decision, { label: string; tone: string }> = {
  accepted: { label: "Accepted", tone: "text-emerald-300 bg-emerald-400/10 ring-emerald-400/25" },
  adjusted: { label: "Adjusted", tone: "text-amber-300 bg-amber-400/10 ring-amber-400/25" },
  rejected: { label: "Rejected", tone: "text-rose-300 bg-rose-400/10 ring-rose-400/25" },
};
