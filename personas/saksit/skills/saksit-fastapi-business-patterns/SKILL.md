---
name: saksit-fastapi-business-patterns
title: FastAPI Business Backend Patterns
description: Lightweight FastAPI + SQLite + uv backend patterns for internal business tools — lead trackers, webhook receivers, data APIs, admin dashboards. Beer's go-to Python backend stack.
---

# FastAPI Business Backend Patterns

Reusable patterns for building lightweight business backends using Beer's stack: **Python 3.13 + FastAPI + SQLite + uv + uvicorn**. Designed for internal tools where you need an API fast, without infrastructure overhead.

## When to use

- Beer needs a **quick backend** for a business tool (lead tracker, CRM extension, webhook receiver)
- You're building an **internal API** that serves data to a frontend
- You need **persistent data** (SQLite) without setting up PostgreSQL
- You're **prototyping** something that may become a WorkFlow-SakThai service

## Project Structure

```
project/
├── pyproject.toml         # uv-managed dependencies
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI application entry point
│   ├── models.py          # SQLAlchemy / pydantic models
│   ├── schemas.py         # Request/response schemas
│   ├── database.py        # DB connection + migrations
│   └── routers/
│       ├── __init__.py
│       ├── health.py      # Health check endpoint
│       └── leads.py       # Example: leads CRUD
├── data/                  # SQLite DB lives here (gitignored)
└── tests/
    └── test_api.py
```

## pyproject.toml Template

```toml
[project]
name = "business-api"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "sqlalchemy>=2.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "httpx>=0.28",
    "coverage>=7.0",
]
```

## main.py Template

```python
"""Business API — lightweight FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, init_db
from app.routers import health, leads


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    init_db()
    yield
    engine.dispose()


app = FastAPI(
    title="Business API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow your frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(leads.router, prefix="/api/leads", tags=["leads"])


@app.get("/")
async def root():
    return {"app": "Business API", "status": "running"}
```

## database.py Template

```python
"""SQLite database setup with auto-migration."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "app.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite-specific
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    """Run migrations — creates tables if they don't exist."""
    import app.models  # noqa: F401 — registers models
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency for DB sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## models.py Template

```python
"""SQLAlchemy models for business entities."""

import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    company = Column(String(255), default="")
    source = Column(String(100), default="")       # e.g. "linkedin", "webinar", "referral"
    status = Column(String(50), default="new")     # new → contacted → qualified → won/lost
    score = Column(Float, default=0.0)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
```

## schemas.py Template

```python
"""Pydantic schemas for API request/response validation."""

import datetime
from pydantic import BaseModel, EmailStr


class LeadCreate(BaseModel):
    name: str
    email: str
    company: str = ""
    source: str = ""
    notes: str = ""


class LeadUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    company: str | None = None
    status: str | None = None
    score: float | None = None
    notes: str | None = None


class LeadResponse(BaseModel):
    id: int
    name: str
    email: str
    company: str
    source: str
    status: str
    score: float
    notes: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}
```

## routers/health.py

```python
"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}
```

## routers/leads.py (Example CRUD)

```python
"""Leads CRUD router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead
from app.schemas import LeadCreate, LeadUpdate, LeadResponse

router = APIRouter()


@router.get("/", response_model=list[LeadResponse])
async def list_leads(
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    return query.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=LeadResponse, status_code=201)
async def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    db_lead = Lead(**lead.model_dump())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: int, update: LeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(lead, key, value)
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()
```

## Quick Start

```bash
# Create project
uv init --app business-api
cd business-api

# Install deps
uv add fastapi uvicorn sqlalchemy pydantic pydantic-settings
uv add --dev pytest httpx

# Create directory structure
mkdir -p app/routers data tests

# Create files (use the templates above)

# Run
uv run uvicorn app.main:app --reload --port 8000

# Test
curl http://localhost:8000/health
# → {"status": "ok"}
```

## Pitfalls

- **SQLite concurrency:** Not suitable for high-write workloads. For >10 concurrent writers, use PostgreSQL.
- **CORS in production:** `allow_origins=["*"]` is for development. Pin to your frontend URL in production.
- **Secret key:** Never hardcode. Use `pydantic-settings` with `.env` for configuration.
- **data/ directory:** Add to `.gitignore`. SQLite DBs don't belong in version control.
- **uv sync vs uv run:** `uv sync` installs deps; `uv run` executes in the venv. Use `uv run` as the primary runner.
- **Auto-migrations:** `create_all()` is safe for dev but won't handle column changes. For production, use Alembic.

## Verification

```bash
# Health check
curl -s http://localhost:8000/health | python -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='ok'"

# Create a lead
curl -s -X POST http://localhost:8000/api/leads \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Lead","email":"test@example.com","source":"webinar"}' | python -m json.tool

# List leads
curl -s http://localhost:8000/api/leads | python -m json.tool
```