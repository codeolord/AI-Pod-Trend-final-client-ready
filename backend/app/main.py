from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import Base, engine
from app.routers import designs, products, trends, auth, realtime


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev-friendly auto-create tables. In production, use Alembic migrations.
    if settings.env != "production":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="POD Trend & Design Automation API",
    version="1.0.0",
    description="API for AI-driven print-on-demand trend discovery, scoring, and design generation.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(realtime.router, tags=["realtime"]) 

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

app.include_router(trends.router, prefix="/api/v1/trends", tags=["trends"])
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(designs.router, prefix="/api/v1/designs", tags=["designs"])


@app.get("/health")
async def health():
    return {"status": "ok"}
