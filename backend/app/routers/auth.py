from datetime import timedelta
import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.core import models, schemas, database
from backend.app import auth

router = APIRouter(prefix="/auth", tags=["auth"])

from fastapi import Response

@router.post("/login")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.User).where(models.User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Set HttpOnly Cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=os.getenv("SECURE_COOKIES", "False").lower() == "true", # True in production
        expires=auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {"message": "Login successful"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}

@router.get("/me", response_model=schemas.TokenData)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return {"username": current_user.username}
