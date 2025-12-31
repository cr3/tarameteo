"""Service fixtures."""

from functools import partial
from pathlib import Path

import pytest
from httpx import AsyncClient

from tarameteo.issuer import get_issuer_client
from tarameteo.testing.compose import ComposeServer


@pytest.fixture(scope="session")
def project():
    return "test"


@pytest.fixture(scope="session")
def env_vars(project):
    """Environment variables for the services.

    Static because they are persisted in volumes, e.g. mysql-vol-1.
    """
    return {
        "COMPOSE_PROJECT_NAME": project,
        "ISSUER_TOKEN": "test",
        "SERVER_HOSTNAME": "test.local",
    }

@pytest.fixture(scope="session")
def env_file(env_vars, request):
    """Environment file containing `env_vars`.

    Cached for troubleshooting purposes.
    """
    env_file = request.config.cache.makedir("compose") / "env"
    with env_file.open("w") as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")

    return env_file


@pytest.fixture(scope="session")
def compose_files(request):
    directory = Path(request.config.rootdir)
    filenames = ["docker-compose.yml", "compose.yaml", "compose.yml"]
    while True:
        for filename in filenames:
            path = directory / filename
            if path.exists():
                all_files = directory.glob(f"{path.stem}.*")
                ordered_files = sorted(all_files, key=lambda p: len(p.name))
                return list(ordered_files)

        if directory == directory.parent:
            raise KeyError("Docker compose file not found")

        directory = directory.parent


@pytest.fixture(scope="session")
def compose_server(project, env_file, compose_files, process):
    return partial(
        ComposeServer,
        project=project,
        env_file=env_file,
        compose_files=compose_files,
        process=process,
    )


@pytest.fixture(scope="session")
def api_service(compose_server):
    """API service fixture."""
    server = compose_server("Application startup complete")
    with server.run("api") as service:
        yield service


@pytest.fixture
async def api_client(api_service):
    """API client to the service fixture."""
    url = f"http://{api_service.ip}"
    async with AsyncClient(base_url=url, timeout=5.0) as client:
        yield client


@pytest.fixture(scope="session")
def issuer_service(compose_server):
    """Issuer service fixture."""
    server = compose_server("Application startup complete")
    with server.run("issuer") as service:
        yield service


@pytest.fixture
async def issuer_client(issuer_service):
    """Issuer client to the service fixture."""
    env = {
        "ISSUER_URL": f"http://{issuer_service.ip}",
        **issuer_service.env,
    }
    async for client in get_issuer_client(env):
        yield client


@pytest.fixture(scope="session")
def mosquitto_service(compose_server):
    """Mosquitto service fixture."""
    server = compose_server("mosquitto version 2.0.22 running")
    with server.run("mosquitto") as service:
        yield service
