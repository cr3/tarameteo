"""Command-line interface."""

import random
import sys
from argparse import ArgumentParser
from collections.abc import Generator
from datetime import (
    UTC,
    datetime,
    timedelta,
)
from functools import partial
from typing import TypeVar

from attrs import (
    define,
    field,
)
from configargparse import ArgParser
from requests.exceptions import HTTPError

from tarameteo.http import HTTPSession
from tarameteo.sensor import SensorCreate
from tarameteo.weather import WeatherDataRequest

DEFAULT_API_URL = "https://meteo.taram.ca/"

T = TypeVar("T")

def make_generator(base: T, variation: T, lower: T | None = None, upper: T | None = None, ndigits: int = 1) -> Generator[T]:
    while True:
        offset = random.uniform(-variation, variation) if isinstance(variation, float) else random.randint(-variation, variation)  # noqa: S311
        value = base + offset
        value = round(value, ndigits)
        if lower is not None:
            value = max(lower, value)
        if upper is not None:
            value = min(value, upper)

        yield value


@define(frozen=True)
class WeatherDataGenerator:

    temperature_generator: Generator[float] = field()
    humidity_generator: Generator[float] = field()
    pressure_generator: Generator[float] = field()
    altitude_generator: Generator[float] = field()
    rssi_generator: Generator[int] = field()

    @classmethod
    def from_config(cls, config) -> "WeatherDataGenerator":
        temperature_generator = make_generator(config.temperature_base, config.temperature_variation)
        humidity_generator = make_generator(config.humidity_base, config.humidity_variation, lower=0.0, upper=100.0)
        pressure_generator = make_generator(config.pressure_base, config.pressure_variation)
        altitude_generator = make_generator(config.altitude_base, config.altitude_variation)
        rssi_generator = make_generator(config.rssi_base, config.rssi_variation, lower=-100, upper=-20)

        return cls(
            temperature_generator,
            humidity_generator,
            pressure_generator,
            altitude_generator,
            rssi_generator,
        )

    def generate(self, timestamp: datetime | int) -> WeatherDataRequest:
        return WeatherDataRequest(
            timestamp=timestamp,
            temperature=next(self.temperature_generator),
            humidity=next(self.humidity_generator),
            pressure=next(self.pressure_generator),
            altitude=next(self.altitude_generator),
            rssi=int(next(self.rssi_generator)),
        )


@define(frozen=True)
class SampleDataGenerator:
    """Generate and send sample weather data."""

    session: HTTPSession = field()
    start_time: datetime = field()
    interval_seconds: int = field(default=60)
    duration_hours: int = field(default=24)
    weather_data_generator: WeatherDataGenerator = field(factory=WeatherDataGenerator)

    @classmethod
    def from_api_url(cls, api_url, api_key, **kwargs):
        """Initialize sample weather data from API URL and key."""
        session = HTTPSession(api_url)
        session.headers.update({
            "X-API-Key": api_key,
        })
        return cls(session, **kwargs)

    def generate(self) -> None:
        """Generate and send weather data over the specified duration."""
        print(f"Duration: {self.duration_hours} hours")
        print(f"Interval: {self.interval_seconds} seconds")
        print(f"Start time: {self.start_time}")
        print("-" * 50)

        current_time = self.start_time
        end_time = current_time + timedelta(hours=self.duration_hours)

        while current_time < end_time:
            data = self.weather_data_generator.generate(current_time)

            print(f"Sending: {data}")
            self.session.post("/api/weather", json=data.model_dump(mode="json"))

            current_time += timedelta(seconds=self.interval_seconds)


def create_sensor(api_url, sensor_name) -> None:
    session = HTTPSession(api_url)
    data = SensorCreate(name=sensor_name)
    response = session.post("/api/sensors", json=data.model_dump(mode="json"))

    data = response.json()
    print(f"Created sensor with API key: {data['api_key']}")


def delete_sensor(api_url, sensor_name) -> None:
    session = HTTPSession(api_url)
    session.delete(f"/api/sensors/{sensor_name}")


def parse_datetime(datetime_str: str) -> datetime:
    """Parse datetime string in various formats."""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue

    raise ValueError(f"Could not parse datetime: {datetime_str}")


def make_config_parser(config_files):
    """Make a parser for configuration files and command-line arguments."""
    config = ArgParser(
        default_config_files=config_files,
        add_help=False,
    )
    config.add_argument(
        "--temperature-base",
        type=float,
        default=20.0,
        help="Temperature base in Celcius (default %(default)s)",
    )
    config.add_argument(
        "--temperature-variation",
        type=float,
        default=5.0,
        help="Temperature variation (default %(default)s)",
    )
    config.add_argument(
        "--humidity-base",
        type=float,
        default=60.0,
        help="Relative humidity base in percent (default %(default)s)",
    )
    config.add_argument(
        "--humidity-variation",
        type=float,
        default=20.0,
        help="Relative humidity variation (default %(default)s)",
    )
    config.add_argument(
        "--pressure-base",
        type=float,
        default=1013.25,
        help="Atmospheric pressure base in hPa (default %(default)s)",
    )
    config.add_argument(
        "--pressure-variation",
        type=float,
        default=10.0,
        help="Atmospheric pressure variation (default %(default)s)",
    )
    config.add_argument(
        "--altitude-base",
        type=float,
        default=100.0,
        help="Altitude base in meters (default %(default)s)",
    )
    config.add_argument(
        "--altitude-variation",
        type=float,
        default=5.0,
        help="Altitude variation (default %(default)s)",
    )
    config.add_argument(
        "--rssi-base",
        type=int,
        default=-50,
        help="WiFi signal strength base in dBm (default %(default)s)",
    )
    config.add_argument(
        "--rssi-variation",
        type=int,
        default=15,
        help="WiFi signal strength variation (default %(default)s)",
    )
    return config


def make_args_parser():
    """Make a parser for command-line arguments only."""
    args_parser = ArgumentParser()
    args_parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help="API base URL (default %(default)s)",
    )
    command = args_parser.add_subparsers(
        dest="command",
        help="taramail command",
    )
    command.add_parser(
        "help",
        help="Show configuration help",
    )
    create = command.add_parser(
        "create",
        help="Create a sensor",
    )
    create.add_argument(
        "sensor_name",
        help="Name of the sensor to create",
    )
    delete = command.add_parser(
        "delete",
        help="Delete a sensor",
    )
    delete.add_argument(
        "sensor_name",
        help="Name of the sensor to delete",
    )
    generate = command.add_parser(
        "generate",
        help="Generate sample data",
    )
    generate.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval between data points in seconds (default %(default)s)",
    )
    generate.add_argument(
        "--duration",
        type=int,
        default=24,
        help="Duration in hours (default %(default)s)",
    )
    generate.add_argument(
        "--start-time",
        type=parse_datetime,
        default=datetime.now(UTC),
        help="Start time (YYYY-MM-DD HH:MM:SS or YYYY-MM-DD, default now)",
    )
    generate.add_argument(
        "api_key",
        help="API key for the sensor",
    )
    return args_parser


def main(argv=None) -> None:
    config_parser = make_config_parser(["~/.tarameteo", ".tarameteo"])
    args_parser = make_args_parser()

    args, remaining = args_parser.parse_known_args(argv)
    config = config_parser.parse_args(remaining)

    match args.command:
        case "create":
            action = partial(create_sensor, args.api_url, args.sensor_name)
        case "delete":
            action = partial(delete_sensor, args.api_url, args.sensor_name)
        case "generate":
            weather_data_generator = WeatherDataGenerator.from_config(config)
            sample_data_generator = SampleDataGenerator.from_api_url(
                api_url=args.api_url,
                api_key=args.api_key,
                interval_seconds=args.interval,
                duration_hours=args.duration,
                start_time=args.start_time,
                weather_data_generator=weather_data_generator,
            )

            action = sample_data_generator.generate
        case "help":
            config_parser.print_help()
            sys.exit(0)
        case command:
            args_parser.error(f"Programming error for command: {command}")

    try:
        action()
    except KeyboardInterrupt:
        print("\nStopped by user")
    except HTTPError as e:
        message = e.response.json()
        args_parser.error(message.get('detail') or message['error'])
    except Exception as e:
        args_parser.error(e)
