import { createUser } from "../services/userService";

export function listUsers() {
  return [];
}

router.get("/api/users", listUsers);
router.post("/api/users", createUser);
