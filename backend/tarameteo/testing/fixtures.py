"""Testing fixtures."""

import logging
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from tarameteo.api import app
from tarameteo.db import get_db
from tarameteo.logger import setup_logger
from tarameteo.testing.logger import LoggerHandler


@pytest.fixture
def api_app(db_session, memcached_store, postfix_mailer, redis_queue, redis_store, env_vars):
    """API testing app."""
    app.dependency_overrides[get_db] = lambda: db_session

    url = db_session.bind.engine.url
    env = {
        "DBDRIVER": url.drivername,
        "DBNAME": url.database,
    }

    with patch.dict(os.environ, env), TestClient(app) as client:
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
