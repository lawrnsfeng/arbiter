import { test } from "node:test";
import assert from "node:assert/strict";
import { slugify } from "../src/text.ts";

test("slugify joins words with hyphens", () => {
  assert.equal(slugify("  Hello, World! "), "hello-world");
});
