"""Issuer service."""

import os
import secrets
from collections.abc import AsyncIterator
from datetime import (
    UTC,
    datetime,
    timedelta,
)
from pathlib import Path

from attrs import define
from cryptography import x509
from cryptography.hazmat.primitives import (
    hashes,
    serialization,
)
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import (
    ExtendedKeyUsageOID,
    NameOID,
)
from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
)
from httpx import AsyncClient
from pydantic import (
    BaseModel,
    Field,
)

app = FastAPI(
    title="TaraMeteo Issuer",
)

CA_KEY = Path(os.getenv("CA_KEY", "/pki/ca.key"))
CA_CRT = Path(os.getenv("CA_CRT", "/pki/ca.crt"))
CERT_DAYS = int(os.getenv("CERT_DAYS", "30"))


class MintRequest(BaseModel):
    device_id: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    ttl_days: int = Field(default=CERT_DAYS, ge=1, le=365)


class MintResponse(BaseModel):
    key_pem: str
    cert_pem: str
    ca_pem: str
    expires_at: datetime
    serial: str


@define(frozen=True)
class IssuerClient:

    _http: AsyncClient
    _token: str

    async def mint(self, request: MintRequest) -> MintResponse:
        response = await self._http.post(
            "/v1/certs",
            headers={"Authorization": f"Bearer {self._token}"},
            json=request.model_dump(),
        )
        response.raise_for_status()
        return MintResponse.model_validate(response.json())


async def get_issuer_client(env = os.environ, timeout: float = 5.0) -> AsyncIterator:
    url = env["ISSUER_URL"]
    token = env["ISSUER_TOKEN"]
    async with AsyncClient(base_url=url, timeout=timeout) as http:
        yield IssuerClient(http, token)


def require_token(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    expected = os.environ["ISSUER_TOKEN"]
    if not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="Invalid token")


@app.post("/v1/certs", response_model=MintResponse, dependencies=[Depends(require_token)])
def mint_cert(request: MintRequest) -> MintResponse:
    ca_crt = x509.load_pem_x509_certificate(CA_CRT.read_bytes())
    ca_key = serialization.load_pem_private_key(CA_KEY.read_bytes(), password=None)

    device_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, request.device_id)])

    now = datetime.now(UTC)
    starts_at = now - timedelta(minutes=5)
    expires_at = now + timedelta(days=request.ttl_days)

    serial = x509.random_serial_number()

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_crt.subject)
        .public_key(device_key.public_key())
        .serial_number(serial)
        .not_valid_before(starts_at)
        .not_valid_after(expires_at)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=False,
        )
    )

    cert = builder.sign(private_key=ca_key, algorithm=hashes.SHA256())

    key_pem = device_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")
    ca_pem = CA_CRT.read_text()

    return MintResponse(
        key_pem=key_pem,
        cert_pem=cert_pem,
        ca_pem=ca_pem,
        expires_at=expires_at,
        serial=hex(serial),
    )


@app.get("/healthz", include_in_schema=False)
def get_healthz() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
