from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import app.core.security as security
import app.db.repository as repository
import app.schemas.schema as schema
from app.db.session import get_db

router = APIRouter()

@router.post("/signup", response_model=schema.UserResponse, status_code=status.HTTP_201_CREATED)
def signup(request: schema.UserCreate, db: Session = Depends(get_db)):
    existing_user = repository.get_user_by_username(db, username=request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already registered."
        )
    hashed_pw = security.get_password_hash(request.password)
    new_user = repository.create_user(
        db=db,
        username=request.username,
        hashed_password=hashed_pw
    )
    return new_user

@router.post("/login", response_model=schema.Token)
def login(request: schema.LoginRequest, db: Session = Depends(get_db)):
    user = repository.get_user_by_username(db, username=request.username)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not security.verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = security.create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return schema.Token(access_token=access_token, token_type="bearer")
