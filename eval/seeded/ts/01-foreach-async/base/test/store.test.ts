import { test } from "node:test";
import assert from "node:assert/strict";
import { Store } from "../src/store.ts";

test("save stores an item by sku", async () => {
  const store = new Store();
  await store.save({ sku: "a1", qty: 3 });
  assert.deepEqual(store.get("a1"), { sku: "a1", qty: 3 });
  assert.equal(store.size(), 1);
});
