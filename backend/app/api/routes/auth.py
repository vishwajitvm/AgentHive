from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any
import pyotp

from app.core.database import get_db
from app.core.models import User, UserSession
from app.core.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    get_current_user
)
from pydantic import BaseModel, EmailStr

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=TokenResponse)
async def register(user_in: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        name=user_in.name,
        role="super_admin" if user_in.email == "vishwajitmall50@gmail.com" else "user"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Create session
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    user_agent = request.headers.get("user-agent", "Unknown Device")
    client_ip = request.client.host if request.client else "Unknown IP"
    
    session = UserSession(
        user_id=user.id,
        session_token=refresh_token,
        device_info=user_agent[:250],
        ip_address=client_ip
    )
    db.add(session)
    await db.commit()
    
    return {"access_token": access_token, "refresh_token": refresh_token}

@router.post("/login", response_model=TokenResponse)
async def login(user_in: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()
    
    if not user or not user.password_hash or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    user_agent = request.headers.get("user-agent", "Unknown Device")
    client_ip = request.client.host if request.client else "Unknown IP"
    
    session = UserSession(
        user_id=user.id,
        session_token=refresh_token,
        device_info=user_agent[:250],
        ip_address=client_ip
    )
    db.add(session)
    await db.commit()
    
    return {"access_token": access_token, "refresh_token": refresh_token}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "2fa_enabled": current_user.two_factor_enabled
    }

@router.get("/sessions")
async def get_sessions(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserSession).where(UserSession.user_id == current_user.id, UserSession.is_revoked == False))
    sessions = result.scalars().all()
    return [{"id": s.id, "device_info": s.device_info, "ip_address": s.ip_address, "last_active": s.last_active} for s in sessions]

@router.post("/sessions/{session_id}/revoke")
async def revoke_session(session_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserSession).where(UserSession.id == session_id, UserSession.user_id == current_user.id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_revoked = True
    await db.commit()
    return {"status": "success"}

@router.post("/2fa/generate")
async def generate_2fa(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    secret = pyotp.random_base32()
    current_user.two_factor_secret = secret
    await db.commit()
    
    # Generate provisioning URI for Authenticator
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user.email, issuer_name="AgentHive")
    return {"secret": secret, "uri": uri}

class Verify2FA(BaseModel):
    code: str

@router.post("/2fa/verify")
async def verify_2fa(payload: Verify2FA, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user.two_factor_secret:
        raise HTTPException(status_code=400, detail="2FA not configured")
        
    totp = pyotp.TOTP(current_user.two_factor_secret)
    if totp.verify(payload.code):
        current_user.two_factor_enabled = True
        await db.commit()
        return {"status": "success"}
    else:
        raise HTTPException(status_code=400, detail="Invalid code")
