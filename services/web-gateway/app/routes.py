from fastapi import APIRouter, Request, HTTPException

from .auth_proxy import introspect

router = APIRouter()


@router.get("/whoami")
async def whoami(request: Request):
    auth = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="missing authorization header")
    token = auth.split(" ", 1)[1] if " " in auth else auth
    payload = await introspect(token)
    return payload
