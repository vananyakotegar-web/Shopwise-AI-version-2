from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, Text, Float, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    preferences: Mapped[str] = mapped_column(Text, default="{}")  # JSON: category/brand counts
    created: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Search(Base):
    __tablename__ = "searches"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    query: Mapped[str] = mapped_column(Text)
    parsed: Mapped[str] = mapped_column(Text, default="{}")
    created: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Saved(Base):
    __tablename__ = "saved_products"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(300))
    payload: Mapped[str] = mapped_column(Text)
    created: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Alert(Base):
    __tablename__ = "price_alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(300))
    target_price: Mapped[float] = mapped_column(Float)
    current_price: Mapped[float] = mapped_column(Float)
    store: Mapped[str] = mapped_column(String(100), default="Online")
    status: Mapped[str] = mapped_column(String(50), default="Active - Tracking")
    created: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class ComparisonHistory(Base):
    __tablename__ = "comparison_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_ids: Mapped[str] = mapped_column(Text)  # JSON list of product IDs
    query: Mapped[str] = mapped_column(String(300), default="")
    created: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def init_db():
    Base.metadata.create_all(engine)
    if DATABASE_URL.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                res = conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()
                cols = [r[1] for r in res]
                if "created" not in cols:
                    conn.exec_driver_sql("ALTER TABLE users ADD COLUMN created DATETIME")
                    conn.exec_driver_sql("UPDATE users SET created = CURRENT_TIMESTAMP WHERE created IS NULL")
                    conn.commit()
        except Exception:
            pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
