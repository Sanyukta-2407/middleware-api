from collections import deque
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

EMAIL = "22f2001139@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://app-351zh2.example.com",
    "https://exam.sanand.workers.dev",
]

RATE_LIMIT = 12
WINDOW = 10

app = FastAPI(title="Middleware API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

rate_store = {}


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id", "default")

    now = time.time()

    q = rate_store.setdefault(client_id, deque())

    while q and now - q[0] >= WINDOW:
        q.popleft()

    if len(q) >= RATE_LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    q.append(now)

    return await call_next(request)


@app.options("/ping")
async def ping_options():
    return JSONResponse(content={})


@app.get("/")
async def root():
    return {"message": "Middleware API running"}


@app.get("/ping")
async def ping(request: Request):
    request_id = request.state.request_id

    response = JSONResponse(
        content={
            "email": EMAIL,
            "request_id": request_id,
        }
    )

    response.headers["X-Request-ID"] = request_id

    return response