from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.db.models as models
from app.core.config import DATABASE_URL

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL and "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(engine)
    try:
        yield db
    finally:
        db.close()
