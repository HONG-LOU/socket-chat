from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router
from .db import init_db
from .ws import router as ws_router


def create_app() -> FastAPI:
    app = FastAPI(title="Socket Chat")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")
    app.include_router(ws_router)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.on_event("startup")
    def _on_startup() -> None:
        init_db()

    return app


def run() -> None:
    import uvicorn

    uvicorn.run(
        "server.main:create_app", factory=True, host="0.0.0.0", port=8000, reload=False
    )


if __name__ == "__main__":
    run()
