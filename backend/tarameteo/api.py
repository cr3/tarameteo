"""API service."""

import logging
from collections.abc import Sequence
from datetime import datetime

from fastapi import (
    FastAPI,
    Query,
    Request,
    WebSocket,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

from tarameteo.db import db_transaction, get_db_session
from tarameteo.sensor import (
    SensorAlreadyExistsError,
    SensorCreate,
    SensorDep,
    SensorDetails,
    SensorInfo,
    SensorManagerDep,
    SensorNotFoundError,
    SensorUpdate,
)
from tarameteo.weather import (
    WeatherDataRequest,
    WeatherDataResponse,
    WeatherManagerDep,
)

logger = logging.getLogger("uvicorn")
app = FastAPI(
    docs_url="/swagger",
    openapi_url="/openapi.json",
)

origins = [
    "http://172.22.1.5",
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Query parameters
START_TIMESTAMP = Query(None, description="Start timestamp (inclusive)")
END_TIMESTAMP = Query(None, description="End timestamp (inclusive)")

@app.post("/api/sensors", status_code=201)
def post_sensors(create: SensorCreate, manager: SensorManagerDep) -> dict[str, str]:
    with db_transaction(manager.db):
        api_key = manager.create_sensor(create)

    return {"api_key": api_key}


@app.get("/api/sensors/{name}")
def get_sensor(name: str, manager: SensorManagerDep) -> SensorInfo:
    """Get comprehensive sensor information including statistics."""
    return manager.get_sensor_info(name)


@app.patch("/api/sensors/{name}")
def update_sensor(name: str, update: SensorUpdate, manager: SensorManagerDep) -> SensorDetails:
    with db_transaction(manager.db):
        return manager.update_sensor(name, update)


@app.delete("/api/sensors/{name}")
def delete_sensor(name: str, manager: SensorManagerDep) -> None:
    with db_transaction(manager.db):
        manager.delete_sensor(name)


@app.post("/api/weather", status_code=201)
async def post_weather(
    data: WeatherDataRequest,
    sensor: SensorDep,
    manager: WeatherManagerDep,
) -> WeatherDataResponse:
    """Post weather data for a sensor."""
    with db_transaction(manager.db):
        response = manager.create_weather_data(sensor, data)

    # Publish weather data after successful transaction
    await manager.publish_weather_data(response)
    return response


@app.get("/api/sensors/{name}/weather", response_model=Sequence[WeatherDataResponse])
def get_sensor_weather(
    manager: WeatherManagerDep,
    name: str,
    start: datetime | None = START_TIMESTAMP,
    end: datetime | None = END_TIMESTAMP,
) -> Sequence[WeatherDataResponse]:
    """Get weather data for a sensor between timestamps."""
    return manager.get_sensor_weather(name, start, end)


@app.websocket("/ws/sensors/{name}/weather")
async def websocket_sensor_weather(
    websocket: WebSocket,
    name: str,
) -> None:
    """Stream weather data updates for a specific sensor through WebSocket."""
    from tarameteo.weather import _global_weather_queue
    from tarameteo.models import Sensor
    from sqlalchemy.exc import NoResultFound
    from tarameteo.queue import QueueManager

    await websocket.accept()

    # Verify sensor exists before subscribing
    with get_db_session() as db:
        try:
            db.query(Sensor).filter_by(name=name).one()
        except NoResultFound:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    # Stream updates using the global shared queue (no DB needed)
    queue_manager = QueueManager(_global_weather_queue)
    await queue_manager.stream_messages(
        name,
        lambda data: websocket.send_json(data.model_dump(mode="json")),
        lambda _: None,
    )


@app.websocket("/ws/weather")
async def websocket_weather(
    websocket: WebSocket,
) -> None:
    """Stream weather data updates through WebSocket."""
    from tarameteo.weather import _global_weather_queue
    from tarameteo.queue import QueueManager

    await websocket.accept()

    # Stream updates using the global shared queue (no DB needed)
    queue_manager = QueueManager(_global_weather_queue)
    await queue_manager.stream_messages(
        "all",
        lambda data: websocket.send_json(data.model_dump(mode="json")),
        lambda _: None,
    )


error_handlers = {
    SensorAlreadyExistsError: 409,
    SensorNotFoundError: 404,
}

def create_error_handler(exc_class, status_code):
    async def error_handler(request: Request, exc: Exception):
        logger.warning(f"{exc_class.__name__} at {request.url}: {exc}")
        return JSONResponse(
            status_code=status_code,
            content={"error": exc_class.__name__, "detail": str(exc)},
        )
    return error_handler

for exc_type, status in error_handlers.items():
    app.exception_handler(exc_type)(create_error_handler(exc_type, status))


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception at {request.url}")
    return JSONResponse(
        status_code=500,
        content={"error": "Unhandled exception"},
    )


app.mount("/docs", StaticFiles(directory="./build/html", html=True, check_dir=False))

# Simplify operation IDs to use route names.
for route in app.routes:
    if isinstance(route, APIRoute):
        route.operation_id = route.name
