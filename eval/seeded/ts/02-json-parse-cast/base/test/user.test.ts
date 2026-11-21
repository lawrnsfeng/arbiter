import { test } from "node:test";
import assert from "node:assert/strict";
import { displayName } from "../src/user.ts";

test("displayName joins name and email", () => {
  assert.equal(
    displayName({ id: 1, name: "Ada", email: "ada@example.com", role: "member" }),
    "Ada <ada@example.com>",
  );
});
