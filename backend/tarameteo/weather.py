"""Weather data."""

from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, TYPE_CHECKING

from attrs import define, field
from fastapi import Depends, WebSocket, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload

from tarameteo.db import DbDep, DBSession
from tarameteo.models import Sensor, WeatherData
from tarameteo.queue import AsyncioQueue, QueueManager


class WeatherDataRequest(BaseModel):
    """Weather data model for API requests."""

    timestamp: datetime | int = Field(..., description="Timestamp of the measurement (datetime or Unix timestamp)")
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Relative humidity in percent")
    pressure: float = Field(..., description="Atmospheric pressure in hPa")
    altitude: float | None = Field(None, description="Altitude in meters")
    rssi: int | None = Field(None, description="WiFi signal strength in dBm")
    retry_count: int | None = Field(None, description="Number of retry attempts")

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        """Convert Unix timestamp to datetime if needed."""
        if isinstance(v, int):
            return datetime.fromtimestamp(v)
        return v

    def __str__(self):
        return (
            f"{self.timestamp} - "
            f"T: {self.temperature}°C, "
            f"H: {self.humidity}%, "
            f"P: {self.pressure} hPa, "
            f"Alt: {self.altitude}m, "
            f"RSSI: {self.rssi} dBm, "
            f"Retry: {self.retry_count}"
        )


class WeatherDataResponse(BaseModel):
    """Weather data model for API responses."""

    sensor: str = Field(..., description="Name of the sensor")
    timestamp: datetime = Field(..., description="Timestamp of the measurement")
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Relative humidity in percent")
    pressure: float = Field(..., description="Atmospheric pressure in hPa")
    altitude: float | None = Field(None, description="Altitude in meters")
    rssi: int | None = Field(None, description="WiFi signal strength in dBm")
    retry_count: int | None = Field(None, description="Number of retry attempts")


# Global shared queue for weather data streaming
_global_weather_queue: AsyncioQueue[WeatherDataResponse] = AsyncioQueue()


@define(frozen=True)
class WeatherManager:
    """Manager for weather data operations."""

    db: DBSession
    _queue_manager: QueueManager[WeatherDataResponse] = field(
        factory=lambda: QueueManager(_global_weather_queue)
    )

    async def publish_weather_data(self, data: WeatherDataResponse) -> None:
        """Publish weather data to subscribers."""
        await self._queue_manager.publish(data.sensor, data)
        await self._queue_manager.publish("all", data)

    def create_weather_data(self, sensor: Sensor, data: WeatherDataRequest) -> WeatherDataResponse:
        """Create weather data for a sensor."""
        weather_data = WeatherData(
            sensor_id=sensor.id,
            timestamp=data.timestamp,
            temperature=data.temperature,
            humidity=data.humidity,
            pressure=data.pressure,
            altitude=data.altitude,
            rssi=data.rssi,
            retry_count=data.retry_count,
        )
        self.db.add(weather_data)
        self.db.flush()

        response = WeatherDataResponse(
            sensor=sensor.name,
            timestamp=weather_data.timestamp,
            temperature=weather_data.temperature,
            humidity=weather_data.humidity,
            pressure=weather_data.pressure,
            altitude=weather_data.altitude,
            rssi=weather_data.rssi,
            retry_count=weather_data.retry_count,
        )

        # Note: Publishing will need to be handled outside the transaction context
        # TODO: Implement proper after-commit hook mechanism for async publishing
        return response

    def get_weather_data(
        self,
        sensor: Sensor,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Sequence[WeatherDataResponse]:
        """Get weather data for a sensor between timestamps."""
        query = select(WeatherData).where(WeatherData.sensor_id == sensor.id)

        if start is not None:
            query = query.where(WeatherData.timestamp >= start)
        if end is not None:
            query = query.where(WeatherData.timestamp <= end)

        query = query.order_by(WeatherData.timestamp)
        weather_data = self.db.execute(query).scalars().all()

        return [
            WeatherDataResponse(
                sensor=sensor.name,
                timestamp=data.timestamp,
                temperature=data.temperature,
                humidity=data.humidity,
                pressure=data.pressure,
                altitude=data.altitude,
                rssi=data.rssi,
                retry_count=data.retry_count,
            )
            for data in weather_data
        ]


    def get_sensor_weather(
        self,
        name: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Sequence[WeatherDataResponse]:
        """Get weather data for a sensor by name between timestamps."""
        try:
            sensor = self.db.query(Sensor).filter_by(name=name).one()
        except NoResultFound as e:
            raise KeyError(f"Sensor not found: {name}") from e

        return self.get_weather_data(sensor, start, end)


# Dependencies
def get_weather_manager(db: DbDep) -> WeatherManager:
    return WeatherManager(db)

WeatherManagerDep = Annotated[WeatherManager, Depends(get_weather_manager)]
