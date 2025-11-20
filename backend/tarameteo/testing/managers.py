"""Manager fixtures."""

import pytest

from tarameteo.sensor import SensorManager


@pytest.fixture
def sensor_manager(db_session):
    """Sensor manager fixture."""
    return SensorManager(db_session)

