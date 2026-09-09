from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Demo App - User Profiles")

# ---- Simulated database ----
fake_users_db = {
    1: {"id": 1, "username": "alice", "email": "alice@example.com", "profile": "Alice's profile data"},
    2: {"id": 2, "username": "bob", "email": "bob@example.com", "profile": "Bob's profile data"},
}


def get_current_user_id() -> int:
    """Simulates authentication -- always returns user 1 (Alice)."""
    return 1


@app.get("/")
def read_root():
    return {"status": "ok", "app": "demo-profiles"}


# ---- VULNERABLE ENDPOINT ----
# This endpoint contains TWO intentional problems:
#
# 1. SQL INJECTION (CONFIRMED by Semgrep)
#    - String interpolation into a SQL query.
#    - A real deterministic scanner will flag this.
#
# 2. MISSING AUTHORIZATION CHECK (UNCONFIRMED - AI should catch this)
#    - Any authenticated user can request ANY other user's profile.
#    - The task says "reject access to another user's profile."
#    - This is a specification mismatch the AI critic should identify.

@app.get("/users/{user_id}/profile")
def get_user_profile(user_id: int, current_user: int = Depends(get_current_user_id)):
    # BUG 1: SQL injection via string interpolation
    query = f"SELECT * FROM users WHERE id = {user_id}"

    # BUG 2: No authorization check -- should verify user_id == current_user
    profile = fake_users_db.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    return {"profile": profile, "debug_query": query}
