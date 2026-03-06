from fastapi import FastAPI

from app.api.endpoints import auth, links

app = FastAPI()

app.include_router(links.router)
app.include_router(auth.router)
