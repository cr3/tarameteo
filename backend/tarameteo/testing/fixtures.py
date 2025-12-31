"""Testing fixtures."""

import logging

import pytest
from fastapi.testclient import TestClient

from tarameteo.api import app as _api_app
from tarameteo.issuer import app as _issuer_app
from tarameteo.logger import setup_logger
from tarameteo.testing.logger import LoggerHandler


@pytest.fixture
def api_app():
    """API testing app."""
    with TestClient(_api_app) as client:
        yield client


@pytest.fixture
def issuer_app():
    """Issuer testing app."""
    with TestClient(_issuer_app) as client:
        yield client


@pytest.fixture(autouse=True)
def logger_handler():
    """Logger handler fixture."""
    handler = LoggerHandler()
    setup_logger(logging.DEBUG, handler)
    try:
        yield handler
    finally:
        setup_logger()
