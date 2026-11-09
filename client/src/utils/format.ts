import type { Unit } from "@/types";

const currencyFormatters = new Map<string, Intl.NumberFormat>();

function currencyFormatter(currency: string, whole: boolean): Intl.NumberFormat {
  const key = `${currency}:${whole}`;
  const formatter = currencyFormatters.get(key);

  if (!formatter) {
    const newFormatter = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      maximumFractionDigits: whole ? 0 : 2,
      minimumFractionDigits: whole ? 0 : 2,
    });

    currencyFormatters.set(key, newFormatter);

    return newFormatter;
  }

  return formatter;
}

export function formatMoney(value: number, currency: string, opts: { whole?: boolean } = {}) {
  return currencyFormatter(currency, opts.whole ?? false).format(value);
}

export function formatMoneyDelta(value: number, currency: string, opts: { whole?: boolean } = {}) {
  const abs = formatMoney(Math.abs(value), currency, opts);
  if (value > 0) return `+${abs}`;
  if (value < 0) return `−${abs}`;

  return abs;
}

const numberFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 3 });

export function formatNumber(value: number): string {
  return numberFormatter.format(value);
}

export function formatPercent(value: number, opts: { signed?: boolean } = {}): string {
  const text = `${Math.abs(value).toFixed(Math.abs(value) < 10 ? 2 : 1)}%`;

  if (!opts.signed || value === 0) return value < 0 ? `−${text}` : text;

  return value > 0 ? `+${text}` : `−${text}`;
}

const UNIT_LABELS: Record<Unit, string> = {
  m: "m",
  m2: "m²",
  m3: "m³",
  kg: "kg",
  t: "t",
  pcs: "pcs",
  hr: "hr",
  day: "day",
  ls: "LS",
};

export function formatUnit(unit: Unit): string {
  return UNIT_LABELS[unit];
}

export function formatQuantity(value: number, unit: Unit): string {
  return `${formatNumber(value)} ${formatUnit(unit)}`;
}

const compactFormatter = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

export function formatTokens(value: number): string {
  return compactFormatter.format(value);
}

const relativeFormatter = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

export function formatRelative(iso: string, now: number = Date.now()): string {
  const seconds = Math.round((new Date(iso).getTime() - now) / 1000);
  const abs = Math.abs(seconds);

  if (abs < 60) return relativeFormatter.format(seconds, "second");
  if (abs < 3600) return relativeFormatter.format(Math.round(seconds / 60), "minute");
  if (abs < 86400) return relativeFormatter.format(Math.round(seconds / 3600), "hour");

  return relativeFormatter.format(Math.round(seconds / 86400), "day");
}
