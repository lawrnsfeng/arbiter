import { test } from "node:test";
import assert from "node:assert/strict";
import { calc } from "../src/cart.ts";
import { formatTotal } from "../src/checkout.ts";

const lines = [
  { sku: "a", unitCents: 250, qty: 2 },
  { sku: "b", unitCents: 99, qty: 1 },
];

test("calc sums line totals in cents", () => {
  assert.equal(calc(lines), 599);
  assert.equal(calc([]), 0);
});

test("formatTotal renders dollars", () => {
  assert.equal(formatTotal(lines), "$5.99");
});
