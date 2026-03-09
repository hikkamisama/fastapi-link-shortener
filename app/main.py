from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.endpoints.init import routers
from app.core.tasks import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Link Shortener API",
    lifespan=lifespan
)

for name, router in routers:
    app.include_router(router, tags=[name])
