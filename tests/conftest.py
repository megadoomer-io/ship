import os
import pathlib
import typing

import flask
import flask.testing
import pytest

import ship
from ship.dev import create_mock_vault


@pytest.fixture()
def app(tmp_path: pathlib.Path) -> typing.Iterator[flask.Flask]:
    vault_path = str(tmp_path / "vault")
    create_mock_vault(vault_path)

    os.environ["SHIP_VAULT_REPO"] = ""
    os.environ["SHIP_VAULT_PATH"] = vault_path
    os.environ["SHIP_OWNER_GITHUB_USER"] = "testowner"
    os.environ["SHIP_OWNERS"] = "testowner"
    os.environ["SHIP_MANAGERS"] = "testmanager"
    os.environ["SHIP_TEAMMATES"] = "testmate"

    app = ship.create_app()
    app.config["TESTING"] = True

    yield app


@pytest.fixture()
def client(app: flask.Flask) -> flask.testing.FlaskClient:
    return app.test_client()


@pytest.fixture()
def prefixed_app(tmp_path: pathlib.Path) -> typing.Iterator[flask.Flask]:
    vault_path = str(tmp_path / "vault")
    create_mock_vault(vault_path)

    os.environ["SHIP_VAULT_REPO"] = ""
    os.environ["SHIP_VAULT_PATH"] = vault_path
    os.environ["SHIP_OWNER_GITHUB_USER"] = "testowner"
    os.environ["SHIP_OWNERS"] = "testowner"
    os.environ["SHIP_MANAGERS"] = "testmanager"
    os.environ["SHIP_TEAMMATES"] = "testmate"
    os.environ["SHIP_PATH_PREFIX"] = "/ship"

    app = ship.create_app()
    app.config["TESTING"] = True

    yield app

    del os.environ["SHIP_PATH_PREFIX"]


@pytest.fixture()
def prefixed_client(prefixed_app: flask.Flask) -> flask.testing.FlaskClient:
    return prefixed_app.test_client()
