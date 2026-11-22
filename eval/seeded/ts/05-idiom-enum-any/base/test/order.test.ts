import { test } from "node:test";
import assert from "node:assert/strict";
import { orderTotal } from "../src/order.ts";

test("orderTotal multiplies price by qty", () => {
  assert.equal(orderTotal({ id: "o1", lines: [{ price: 2, qty: 3 }, { price: 1, qty: 1 }] }), 7);
});
