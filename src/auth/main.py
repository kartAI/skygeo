from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()

# Static token for demo purposes
API_TOKEN = "mysecrettoken123"
STORAGE_HOST = "http://localhost:8080"
# The auth api server manages the credentials to storage.
# this is comparable to having the server issue pre-signed urls.
STORAGE_TOKEN = "demo123"

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme"
        )
    if credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token"
        )
    return credentials.credentials

app = FastAPI(dependencies=[Depends(verify_token)])

def get_presigned_url(obj: str):
    # Dummy function to simulate creating a presinged url
    return f"{STORAGE_HOST}/{obj}?token={STORAGE_TOKEN}"

@app.get("/{obj}")
def read_item(obj: str):
    return RedirectResponse(
        url=get_presigned_url(obj)
    )
