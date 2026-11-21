export interface CartLine {
  sku: string;
  unitCents: number;
  qty: number;
}

/** Sum of all line totals, in cents. */
export function calc(lines: readonly CartLine[]): number {
  return lines.reduce((sum, line) => sum + line.unitCents * line.qty, 0);
}
