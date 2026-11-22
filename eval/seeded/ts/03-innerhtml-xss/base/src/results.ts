export interface Result {
  title: string;
  url: string;
}

/** Renders result titles as plain text, one per line. */
export function renderResults(el: HTMLElement, results: Result[]): void {
  el.textContent = results.map((r) => r.title).join("\n");
}
