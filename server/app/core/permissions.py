from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .errors import Forbidden, Unauthorized
from .security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class AuthSubject:
    user_id: int
    role: str


async def current_subject(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthSubject:
    if creds is None:
        raise Unauthorized("missing bearer token")
    payload = decode_access_token(creds.credentials)
    return AuthSubject(user_id=int(payload["sub"]), role=payload.get("role", "USER"))


ROLE_PERMS: dict[str, set[str]] = {
    "ADMIN": {
        "admin:ping",
        "task:create",
        "task:read",
        "draft:review",
        "job:publish",
        "dict:manage",
        "user:manage",
    },
    "USER": set(),
}


def require_perm(code: str):
    """FastAPI dependency factory: the Python equivalent of a permission annotation."""

    async def checker(
        subject: AuthSubject = Depends(current_subject),
    ) -> AuthSubject:
        if code not in ROLE_PERMS.get(subject.role, set()):
            raise Forbidden(f"missing permission: {code}")
        return subject

    return checker
