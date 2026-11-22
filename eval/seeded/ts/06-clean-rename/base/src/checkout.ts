import { calc, type CartLine } from "./cart.ts";

export function formatTotal(lines: readonly CartLine[]): string {
  return `$${(calc(lines) / 100).toFixed(2)}`;
}
