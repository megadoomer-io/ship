import os
import pathlib
import typing

import flask
import flask.testing
import pytest

import ship
from ship.dev import create_mock_vault

_G = "megadoomer-io:megadoomer-ship"
CAPTAIN_GROUPS = f"{_G}-captain,{_G}-officers,{_G}-crew,{_G}"
OFFICERS_GROUPS = f"{_G}-officers,{_G}-crew,{_G}"
CREW_GROUPS = f"{_G}-crew,{_G}"
CARGO_GROUPS = _G


def auth_headers(user: str, groups: str) -> dict[str, str]:
    return {"X-Auth-Request-User": user, "X-Auth-Request-Groups": groups}


@pytest.fixture()
def app(tmp_path: pathlib.Path) -> typing.Iterator[flask.Flask]:
    vault_path = str(tmp_path / "vault")
    create_mock_vault(vault_path)

    os.environ["SHIP_VAULT_REPO"] = ""
    os.environ["SHIP_VAULT_PATH"] = vault_path
    os.environ["SHIP_API_TOKEN"] = "test-api-token-secret"

    app = ship.create_app()
    app.config["TESTING"] = True

    yield app

    os.environ.pop("SHIP_API_TOKEN", None)


@pytest.fixture()
def client(app: flask.Flask) -> flask.testing.FlaskClient:
    return app.test_client()


@pytest.fixture()
def prefixed_app(tmp_path: pathlib.Path) -> typing.Iterator[flask.Flask]:
    vault_path = str(tmp_path / "vault")
    create_mock_vault(vault_path)

    os.environ["SHIP_VAULT_REPO"] = ""
    os.environ["SHIP_VAULT_PATH"] = vault_path
    os.environ["SHIP_API_TOKEN"] = "test-api-token-secret"
    os.environ["SHIP_PATH_PREFIX"] = "/ship"

    app = ship.create_app()
    app.config["TESTING"] = True

    yield app

    del os.environ["SHIP_PATH_PREFIX"]
    os.environ.pop("SHIP_API_TOKEN", None)


@pytest.fixture()
def prefixed_client(prefixed_app: flask.Flask) -> flask.testing.FlaskClient:
    return prefixed_app.test_client()
