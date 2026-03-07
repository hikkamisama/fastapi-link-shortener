from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.endpoints import auth, links
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

app.include_router(auth.router, tags=["Authentication"])
app.include_router(links.router, tags=["Links"])
