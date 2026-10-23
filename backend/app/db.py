from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.config import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PlaidItem(Base):
    """One linked institution. The access token is encrypted at rest and never leaves the server."""

    __tablename__ = "plaid_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    item_id: Mapped[str] = mapped_column(String(128), unique=True)
    institution_name: Mapped[str] = mapped_column(String(128), default="")
    access_token_enc: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class NetWorthSnapshot(Base):
    __tablename__ = "net_worth_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    assets: Mapped[float] = mapped_column(Float)
    liabilities: Mapped[float] = mapped_column(Float)
    net_worth: Mapped[float] = mapped_column(Float)
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SavingsGoal(Base):
    __tablename__ = "savings_goals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(64))
    target: Mapped[float] = mapped_column(Float)
    target_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
