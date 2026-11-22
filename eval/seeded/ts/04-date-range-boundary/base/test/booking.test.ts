import { test } from "node:test";
import assert from "node:assert/strict";
import { totalGuests } from "../src/booking.ts";

test("totalGuests sums guests", () => {
  assert.equal(
    totalGuests([
      { id: "1", day: "2026-03-01", guests: 2 },
      { id: "2", day: "2026-03-02", guests: 3 },
    ]),
    5,
  );
});
