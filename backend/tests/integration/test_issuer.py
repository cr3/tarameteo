"""Integration tests for the issuer module."""

from datetime import (
    UTC,
    datetime,
)

import pytest
from hamcrest import (
    assert_that,
    contains_string,
    greater_than,
    has_properties,
    matches_regexp,
)

from tarameteo.issuer import MintRequest


@pytest.mark.asyncio
async def test_issuer_mint_cert(issuer_client, unique):
    request = MintRequest(device_id=unique("text"))
    response = await issuer_client.mint(request)
    assert_that(response, has_properties(
        key_pem=contains_string("BEGIN RSA PRIVATE KEY"),
        cert_pem=contains_string("BEGIN CERTIFICATE"),
        ca_pem=contains_string("BEGIN CERTIFICATE"),
        expires_at=greater_than(datetime.now(UTC)),
        serial=matches_regexp(r"0x[a-f0-9]+"),
    ))
