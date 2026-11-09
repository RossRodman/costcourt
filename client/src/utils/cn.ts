import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Compose Tailwind classes, letting later utilities override earlier ones. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
