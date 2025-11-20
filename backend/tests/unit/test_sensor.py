"""Tests for sensor module."""


import pytest

from tarameteo.auth import key_hasher
from tarameteo.models import Sensor
from tarameteo.sensor import SensorCreate, SensorUpdate


def test_sensor_manager_create_sensor(sensor_manager, unique):
    """Create a sensor and verify it was created correctly."""
    name = unique("text")
    sensor_create = SensorCreate(name=name)
    api_key = sensor_manager.create_sensor(sensor_create)

    sensor = sensor_manager.db.query(Sensor).filter_by(name=name).one()
    assert key_hasher.verify(api_key, sensor.key_hash)


def test_sensor_manager_authenticate(sensor_manager, unique):
    """Verify that sensor authentication works correctly."""
    name = unique("text")
    sensor_create = SensorCreate(name=name)
    api_key = sensor_manager.create_sensor(sensor_create)

    sensor = sensor_manager.authenticate(api_key)
    assert sensor.name == name


def test_sensor_manager_authenticate_invalid_key(sensor_manager):
    """Verify that authentication fails with an invalid key."""
    with pytest.raises(KeyError, match="Sensor not found"):
        sensor_manager.authenticate("invalid_key")


def test_sensor_manager_update_sensor(sensor_manager, unique):
    """Update a sensor and verify the changes."""
    name = unique("text")
    sensor_create = SensorCreate(name=name)
    sensor_manager.create_sensor(sensor_create)

    new_name = unique("text")
    sensor_update = SensorUpdate(name=new_name)
    details = sensor_manager.update_sensor(name, sensor_update)
    sensor_manager.db.flush()

    assert details.name == new_name


def test_sensor_manager_update_sensor_not_found(sensor_manager, unique):
    """Verify that updating a non-existent sensor fails."""
    name = unique("text")
    with pytest.raises(KeyError, match=f"Sensor not found: {name}"):
        sensor_manager.update_sensor(name, SensorUpdate(name=None))


def test_sensor_manager_delete_sensor(sensor_manager):
    """Delete a sensor and verify it was removed."""
    name = "test_sensor"
    api_key = sensor_manager.create_sensor(SensorCreate(name=name))

    sensor_manager.delete_sensor(name)
    with pytest.raises(KeyError, match="Sensor not found"):
        sensor_manager.authenticate(api_key)


def test_sensor_manager_delete_sensor_not_found(sensor_manager):
    """Verify that deleting a non-existent sensor is a no-op."""
    sensor_manager.delete_sensor("test_sensor")  # Should not raise
