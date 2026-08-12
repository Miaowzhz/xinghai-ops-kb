from fastapi import FastAPI

from app.core.config import settings
from app.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
