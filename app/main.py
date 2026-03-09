from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.endpoints.init import auth_router, links_routers, get_router
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

app.include_router(auth_router, tags=["auth"])

for tag, router in links_routers:
    app.include_router(router, prefix="/links", tags=[tag])
app.include_router(get_router, tags=["redirect"])
