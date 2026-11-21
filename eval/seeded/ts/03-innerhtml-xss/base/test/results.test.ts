import { test } from "node:test";
import assert from "node:assert/strict";
import { renderResults } from "../src/results.ts";

test("renderResults writes titles as text", () => {
  const el = { textContent: "" } as unknown as HTMLElement;
  renderResults(el, [{ title: "A", url: "/a" }, { title: "B", url: "/b" }]);
  assert.equal(el.textContent, "A\nB");
});
