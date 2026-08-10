import jwt
from jwt import PyJWKClient
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.models import User, UserSession
from app.core.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Keycloak JWKS endpoint
jwks_client = PyJWKClient('http://keycloak:8080/realms/agenthive/protocol/openid-connect/certs')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    pass

def create_refresh_token(data: dict) -> str:
    pass

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        email = payload.get("email") or payload.get("preferred_username")
        
        if not email:
            raise credentials_exception
            
    except jwt.PyJWTError as e:
        print(f"JWT Validation Error: {e}")
        raise credentials_exception
        
    roles = payload.get("resource_access", {}).get("agenthive-frontend", {}).get("roles", [])
    is_super_admin = "super_admin" in roles
    role_str = "super_admin" if is_super_admin else ("admin" if "admin" in roles else "user")

    # Check if user exists in our DB, if not create them
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user is None:
        user = User(
            email=email,
            name=payload.get("preferred_username", email),
            role=role_str,
            password_hash="keycloak_managed",
            status="active"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif user.role != role_str:
        user.role = role_str
        await db.commit()
        await db.refresh(user)
        
    return user

async def get_current_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.email != "vishwajitmall50@gmail.com":
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges. Super Admin required.")
    return current_user
