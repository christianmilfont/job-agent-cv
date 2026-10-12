"""Job Agent CV — API. Execute com: uvicorn app.main:app --reload"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import database
from app.routers import applications, profile

ROOT = Path(__file__).resolve().parents[2]


def _load_env() -> None:
    """Carrega .env (raiz do projeto ou backend/) sem dependências extras; variáveis já definidas prevalecem."""
    for path in (ROOT / ".env", ROOT / "backend" / ".env"):
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="Job Agent CV", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.exception_handler(RequestValidationError)
async def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    msgs = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err["loc"] if x != "body")
        msg = str(err["msg"]).removeprefix("Value error, ")
        msgs.append(f"{loc}: {msg}" if loc and "descrição" not in msg else msg)
    return JSONResponse(status_code=422, content={"detail": " ".join(msgs) or "Dados inválidos."})


app.include_router(profile.router)
app.include_router(applications.router)

# Em uso local, serve o frontend compilado (frontend/dist), se existir.
_dist = ROOT / "frontend" / "dist"
if _dist.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
