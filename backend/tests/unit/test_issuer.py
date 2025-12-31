"""Unit tests for the issuer module."""

from hamcrest import (
    assert_that,
    has_entries,
)


def test_healthz_get(issuer_app):
    """Getting the /healthz should return an "ok" status."""
    result = issuer_app.get("/healthz")

    assert_that(result.json(), has_entries(status="ok"))
