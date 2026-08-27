import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCents(cents: number): string {
  if (cents === undefined || cents === null) return "$0.00";
  const dollars = cents / 100.0;
  return `$${dollars.toFixed(2)}`;
}
