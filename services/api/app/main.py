"""FastAPI entrypoint."""

import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.routers import library as library_router
from app.api.routers import study as study_router
from app.config import get_settings

logger = logging.getLogger(__name__)

app = FastAPI(title="StudyGraph API")
app.include_router(library_router.router)
app.include_router(study_router.router)


@app.get("/api/health")
def health() -> JSONResponse:
    settings = get_settings()
    return JSONResponse(
        {
            "status": "ok",
            "app_env": settings.app_env,
            "llm_provider": settings.llm_provider,
            "asr_backend": settings.asr_backend,
            "embed_backend": settings.embed_backend,
        }
    )
