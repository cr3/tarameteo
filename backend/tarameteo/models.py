"""SQLAlchemy models."""

import re
from datetime import datetime as dt
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    TextClause,
    text,
)
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    mapped_column,
    relationship,
)
from sqlalchemy.schema import FetchedValue
from sqlalchemy.sql import func

SQLModel = declarative_base()


@compiles(DateTime, "sqlite")
def sqlite_datetime(element, compiler, **kw):
    """Replace CURRENT_TIMESTAMP string with function in SQLite server default."""
    if server_default := kw["type_expression"].server_default:
        arg = server_default.arg
        if isinstance(arg, TextClause) and " ON UPDATE " in arg.text:
            arg.text = re.sub(" ON UPDATE .*", "", arg.text)

    return compiler.visit_datetime(element, **kw)


class Sensor(SQLModel):

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    index_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    key_hash: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    created: Mapped[dt] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
    )
    modified: Mapped[dt] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        server_onupdate=FetchedValue(),
    )

    data: Mapped[list["WeatherData"]] = relationship("WeatherData", back_populates="sensor")

    __tablename__ = "sensors"


class WeatherData(SQLModel):

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    sensor_id: Mapped[UUID] = mapped_column(ForeignKey("sensors.id", ondelete="CASCADE"))
    timestamp: Mapped[dt] = mapped_column(DateTime(timezone=True), index=True)
    temperature: Mapped[float | None] = mapped_column()
    humidity: Mapped[float | None] = mapped_column()
    pressure: Mapped[float | None] = mapped_column()
    altitude: Mapped[float | None] = mapped_column()
    rssi: Mapped[int | None] = mapped_column()
    retry_count: Mapped[int | None] = mapped_column()

    sensor: Mapped["Sensor"] = relationship("Sensor", back_populates="data")

    __tablename__ = "weather_data"
