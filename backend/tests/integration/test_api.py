"""Integration tests for the api module."""


import pytest
from hamcrest import (
    assert_that,
    contains_string,
    has_entries,
    matches_regexp,
)


@pytest.mark.asyncio
async def test_api_certs_post(api_client, unique):
    device_id = unique("text")
    response = await api_client.post("/api/certs", json={
        "device_id": device_id,
    })
    assert_that(response.json(), has_entries(
        key_pem=contains_string("BEGIN RSA PRIVATE KEY"),
        cert_pem=contains_string("BEGIN CERTIFICATE"),
        ca_pem=contains_string("BEGIN CERTIFICATE"),
        serial=matches_regexp(r"0x[a-f0-9]{40}"),
    ))
