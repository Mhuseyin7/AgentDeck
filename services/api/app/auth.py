from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import OrganizationMember, Role, User

bearer = HTTPBearer(auto_error=False)
ALGORITHM = "HS256"


def create_access_token(user_id: UUID) -> str:
    claims = {"sub": str(user_id), "exp": datetime.now(UTC) + timedelta(hours=8), "typ": "access"}
    return jwt.encode(claims, settings.session_secret, algorithm=ALGORITHM)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing authentication"
        )
    try:
        claims = jwt.decode(
            credentials.credentials, settings.session_secret, algorithms=[ALGORITHM]
        )
        user_id = UUID(str(claims["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid authentication"
        ) from exc
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unknown user")
    return user


def organization_role(
    db: Session, organization_id: UUID, user_id: UUID, *roles: Role
) -> OrganizationMember:
    member = db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
    )
    if member is None or (roles and member.role not in roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="organization access denied"
        )
    return member
