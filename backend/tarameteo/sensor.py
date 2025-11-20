"""Sensor manager."""

from contextlib import suppress
from datetime import datetime
from typing import Annotated

from attrs import define
from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, NoResultFound

from tarameteo.auth import key_generator, key_hasher
from tarameteo.db import DbDep, DBSession
from tarameteo.models import Sensor, WeatherData


class SensorError(Exception):
    """Base exception for sensor errors."""


class SensorAlreadyExistsError(SensorError):
    """Raised when a sensor already exists."""


class SensorNotFoundError(SensorError):
    """Raised when a sensor is not found."""


class SensorCreate(BaseModel):
    """Model for creating a sensor."""

    name: str


class SensorDetails(BaseModel):
    """Model for sensor details."""

    name: str
    created: datetime
    modified: datetime


class SensorUpdate(BaseModel):
    """Model for updating a sensor."""

    name: str | None


class SensorStatistics(BaseModel):
    """Model for sensor statistics."""

    total_readings: int = Field(..., description="Total number of weather data readings")
    first_reading: datetime | None = Field(None, description="Timestamp of first reading")
    last_reading: datetime | None = Field(None, description="Timestamp of last reading")
    last_24h_readings: int = Field(..., description="Number of readings in last 24 hours")
    average_temperature: float | None = Field(None, description="Average temperature in Celsius")
    average_humidity: float | None = Field(None, description="Average humidity percentage")
    average_pressure: float | None = Field(None, description="Average pressure in hPa")
    average_rssi: int | None = Field(None, description="Average WiFi signal strength")


class SensorInfo(BaseModel):
    """Model for comprehensive sensor information."""

    name: str = Field(..., description="Name of the sensor")
    created: datetime = Field(..., description="When the sensor was created")
    modified: datetime = Field(..., description="When the sensor was last modified")
    statistics: SensorStatistics = Field(..., description="Weather data statistics")


@define(frozen=True)
class SensorManager:
    """Manager for sensor operations."""

    db: DBSession
    key_length: int = 32

    def authenticate(self, api_key: str) -> Sensor:
        """Authenticate a sensor using its API key."""
        index_hash = key_hasher.hash_index(api_key)
        try:
            sensor = self.db.query(Sensor).filter_by(index_hash=index_hash).one()
            if not key_hasher.verify(api_key, sensor.key_hash):
                raise SensorNotFoundError("Sensor not found")
        except NoResultFound as e:
            raise SensorNotFoundError("Sensor not found") from e

        return sensor

    def create_sensor(self, sensor_create: SensorCreate) -> str:
        """Create a new sensor."""
        api_key = key_generator.generate(self.key_length)
        index_hash = key_hasher.hash_index(api_key)
        key_hash = key_hasher.hash_key(api_key)
        sensor = Sensor(
            index_hash=index_hash,
            key_hash=key_hash,
            name=sensor_create.name,
        )
        self.db.add(sensor)
        try:
            self.db.flush()
        except IntegrityError as e:
            raise SensorAlreadyExistsError(f"Sensor already exists: {sensor_create.name}") from e

        return api_key

    def update_sensor(self, name: str, sensor_update: SensorUpdate) -> SensorDetails:
        """Update a sensor."""
        try:
            sensor = self.db.query(Sensor).filter_by(name=name).one()
        except NoResultFound as e:
            raise SensorNotFoundError(f"Sensor not found: {name}") from e

        if sensor_update.name is not None:
            sensor.name = sensor_update.name

        return SensorDetails(
            name=sensor.name,
            created=sensor.created,
            modified=sensor.modified,
        )

    def delete_sensor(self, name: str) -> None:
        """Delete a sensor."""
        with suppress(NoResultFound):
            self.db.query(Sensor).filter_by(name=name).delete()

    def get_sensor_info(self, name: str) -> SensorInfo:
        """Get comprehensive sensor information including statistics."""
        try:
            sensor = self.db.query(Sensor).filter_by(name=name).one()
        except NoResultFound as e:
            raise SensorNotFoundError(f"Sensor not found: {name}") from e

        # Get weather data statistics
        weather_query = self.db.query(WeatherData).filter_by(sensor_id=sensor.id)

        # Basic counts and date ranges
        total_readings = weather_query.count()

        if total_readings > 0:
            # Get first and last reading timestamps
            first_reading = weather_query.order_by(WeatherData.timestamp.asc()).first().timestamp
            last_reading = weather_query.order_by(WeatherData.timestamp.desc()).first().timestamp

            # Get readings from last 24 hours
            from datetime import timedelta
            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
            last_24h_readings = weather_query.filter(
                WeatherData.timestamp >= twenty_four_hours_ago
            ).count()

            # Calculate averages (excluding None values)
            averages = self.db.query(
                func.avg(WeatherData.temperature).label('avg_temp'),
                func.avg(WeatherData.humidity).label('avg_humidity'),
                func.avg(WeatherData.pressure).label('avg_pressure'),
                func.avg(WeatherData.rssi).label('avg_rssi')
            ).filter_by(sensor_id=sensor.id).first()

            # Round averages to reasonable precision
            avg_temp = round(averages.avg_temp, 1) if averages.avg_temp is not None else None
            avg_humidity = round(averages.avg_humidity, 1) if averages.avg_humidity is not None else None
            avg_pressure = round(averages.avg_pressure, 1) if averages.avg_pressure is not None else None
            avg_rssi = round(averages.avg_rssi) if averages.avg_rssi is not None else None
        else:
            first_reading = None
            last_reading = None
            last_24h_readings = 0
            avg_temp = None
            avg_humidity = None
            avg_pressure = None
            avg_rssi = None

        statistics = SensorStatistics(
            total_readings=total_readings,
            first_reading=first_reading,
            last_reading=last_reading,
            last_24h_readings=last_24h_readings,
            average_temperature=avg_temp,
            average_humidity=avg_humidity,
            average_pressure=avg_pressure,
            average_rssi=avg_rssi,
        )

        return SensorInfo(
            name=sensor.name,
            created=sensor.created,
            modified=sensor.modified,
            statistics=statistics,
        )


# Dependencies
def get_sensor_manager(db: DbDep) -> SensorManager:
    return SensorManager(db)

SensorManagerDep = Annotated[SensorManager, Depends(get_sensor_manager)]

# Authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_sensor(
    manager: SensorManagerDep,
    api_key: Annotated[str | None, Security(api_key_header)] = None,
) -> Sensor:
    """Authenticate sensor using API key from header."""
    try:
        return manager.authenticate(api_key)
    except SensorNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        ) from e

SensorDep = Annotated[Sensor, Depends(get_sensor)]
