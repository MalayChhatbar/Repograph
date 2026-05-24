import { createUser } from "../src/services/userService";

test("create user", () => {
  expect(createUser().ok).toBe(true);
});
