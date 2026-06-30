from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import time
from collections import deque

EMAIL = "22f2001139@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-351zh2.example.com"
RATE_LIMIT = 12
WINDOW = 10

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        ALLOWED_ORIGIN,
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

rate_store = {}


# Request ID middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# Rate limiter
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):

    client = request.headers.get("X-Client-Id", "default")

    now = time.time()

    q = rate_store.setdefault(client, deque())

    while q and now - q[0] >= WINDOW:
        q.popleft()

    if len(q) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

    q.append(now)

    return await call_next(request)


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }