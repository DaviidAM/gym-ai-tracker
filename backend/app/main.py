from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, workouts, exercises, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(exercises.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {"message": "GymAI Tracker API", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
