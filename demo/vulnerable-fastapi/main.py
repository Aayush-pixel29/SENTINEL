from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="Demo App")

# Mock database
fake_users_db = {
    1: {"id": 1, "username": "alice", "profile": "Alice's profile data"},
    2: {"id": 2, "username": "bob", "profile": "Bob's profile data"}
}

def get_current_user_id() -> int:
    # Hardcoded to represent the authenticated user
    return 1

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.get("/users/{user_id}/profile")
def get_user_profile(user_id: int, current_user: int = Depends(get_current_user_id)):
    """
    Retrieve user profile.
    VULNERABILITY 1: SQL Injection
    VULNERABILITY 2: Insecure Direct Object Reference (Authorization)
    """
    
    # 🔴 CONFIRMED VULNERABILITY (SQLi - easily found by Semgrep)
    query = f"SELECT * FROM users WHERE id = {user_id}"
    
    # 🟡 UNCONFIRMED VULNERABILITY (Authorization - found by AI critic)
    # The endpoint retrieves the requested user_id but does not check 
    # if user_id == current_user
    
    profile = fake_users_db.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {"profile": profile, "executed_query": query}
