"""Unit tests for the api module."""

from datetime import (
    UTC,
    datetime,
)

from hamcrest import (
    assert_that,
    has_entries,
    has_properties,
)

from tarameteo.api import app
from tarameteo.issuer import (
    MintRequest,
    MintResponse,
    get_issuer_client,
)


def test_healthz_get(api_app):
    """Getting the /healthz should return an "ok" status."""
    result = api_app.get("/healthz")

    assert_that(result.json(), has_entries(status="ok"))


def test_certs_post(api_app, unique):
    device_id = unique("text")
    key_pem, cert_pem, ca_pem = unique("text"), unique("text"), unique("text")
    serial = unique("text")

    class StubIssuerClient:
        async def mint(self, request: MintRequest) -> MintResponse:
            assert_that(request, has_properties(device_id=device_id))
            return MintResponse(
                key_pem=key_pem,
                cert_pem=cert_pem,
                ca_pem=ca_pem,
                expires_at=datetime.now(UTC),
                serial=serial,
            )

    app.dependency_overrides[get_issuer_client] = lambda: StubIssuerClient()

    response = api_app.post("/api/certs", json={
        "device_id": device_id,
    })
    assert_that(response.json(), has_entries(
        key_pem=key_pem,
        cert_pem=cert_pem,
        ca_pem=ca_pem,
        serial=serial,
    ))
