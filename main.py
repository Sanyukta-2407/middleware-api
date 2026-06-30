from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from collections import deque
import uuid
import time

EMAIL = "22f2001139@ds.study.iitm.ac.in"

RATE_LIMIT = 12
WINDOW = 10

app = FastAPI(title="Middleware API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-351zh2.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

rate_store = {}


# Declare the rate limiter first.
# The request-context middleware below runs before it.
@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id", "default")

    now = time.time()

    q = rate_store.setdefault(client_id, deque())

    while q and now - q[0] >= WINDOW:
        q.popleft()

    if len(q) >= RATE_LIMIT:
        request_id = getattr(
            request.state,
            "request_id",
            request.headers.get("X-Request-ID", str(uuid.uuid4()))
        )

        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
        response.headers["X-Request-ID"] = request_id
        return response

    q.append(now)

    return await call_next(request)


# Declare this after the rate limiter so it executes first.
@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/")
async def root():
    return {"message": "Middleware API running"}


@app.options("/ping")
async def options_ping():
    return JSONResponse(content={})


@app.get("/ping")
async def ping(request: Request):
    return JSONResponse(
        content={
            "email": EMAIL,
            "request_id": request.state.request_id,
        },
        headers={
            "X-Request-ID": request.state.request_id,
        },
    )