import pytest

import ship


@pytest.fixture()
def app():
    import os

    os.environ["SHIP_VAULT_REPO"] = ""
    os.environ["SHIP_VAULT_PATH"] = "/tmp/ship-test-vault"
    os.environ["SHIP_OWNER_GITHUB_USER"] = "testowner"

    app = ship.create_app()
    app.config["TESTING"] = True

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()
