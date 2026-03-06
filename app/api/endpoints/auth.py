from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.schema import LoginRequest, Token
from app.core.security import create_access_token, verify_password
from app.db.repository import get_user_by_username
from app.db.session import get_db

router = APIRouter()

@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username=request.username)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role} 
    )
    return Token(access_token=access_token, token_type="bearer")