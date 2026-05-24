import pytest

# ---------------------------------------------------------------------------
# Healthz — no auth required
# ---------------------------------------------------------------------------


def test_healthz_returns_200_without_auth(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "git_sha" in data


def test_healthz_includes_git_sha(client, monkeypatch):
    monkeypatch.setenv("GIT_SHA", "abc1234")
    response = client.get("/healthz")
    data = response.get_json()
    assert data["git_sha"] == "abc1234"


@pytest.mark.parametrize("user", ["testowner", "testmanager", "testmate", "stranger"])
def test_healthz_returns_200_for_any_user(client, user):
    response = client.get("/healthz", headers={"X-Auth-Request-User": user})
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Anonymous (no header) -> 401 on all protected routes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/", "/bridge", "/porthole", "/observation-deck"])
def test_anonymous_gets_401(client, path):
    response = client.get(path)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Authenticated but unlisted user -> 403 on all protected routes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/", "/bridge", "/porthole", "/observation-deck"])
def test_unlisted_user_gets_403(client, path):
    response = client.get(path, headers={"X-Auth-Request-User": "stranger"})
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Full role x route access matrix
# ---------------------------------------------------------------------------


class TestBridge:
    """Bridge requires OWNER role."""

    def test_owner_gets_200(self, client):
        response = client.get("/bridge", headers={"X-Auth-Request-User": "testowner"})
        assert response.status_code == 200
        assert b"Bridge" in response.data

    def test_manager_gets_403(self, client):
        response = client.get("/bridge", headers={"X-Auth-Request-User": "testmanager"})
        assert response.status_code == 403

    def test_teammate_gets_403(self, client):
        response = client.get("/bridge", headers={"X-Auth-Request-User": "testmate"})
        assert response.status_code == 403


class TestPorthole:
    """Porthole requires MANAGER role (owner also has access)."""

    def test_owner_gets_200(self, client):
        response = client.get("/porthole", headers={"X-Auth-Request-User": "testowner"})
        assert response.status_code == 200
        assert b"Porthole" in response.data

    def test_manager_gets_200(self, client):
        response = client.get("/porthole", headers={"X-Auth-Request-User": "testmanager"})
        assert response.status_code == 200
        assert b"Porthole" in response.data

    def test_teammate_gets_403(self, client):
        response = client.get("/porthole", headers={"X-Auth-Request-User": "testmate"})
        assert response.status_code == 403


class TestObservationDeck:
    """Observation deck requires TEAMMATE role (all listed users have access)."""

    def test_owner_gets_200(self, client):
        response = client.get("/observation-deck", headers={"X-Auth-Request-User": "testowner"})
        assert response.status_code == 200
        assert b"Observation Deck" in response.data

    def test_manager_gets_200(self, client):
        response = client.get("/observation-deck", headers={"X-Auth-Request-User": "testmanager"})
        assert response.status_code == 200
        assert b"Observation Deck" in response.data

    def test_teammate_gets_200(self, client):
        response = client.get("/observation-deck", headers={"X-Auth-Request-User": "testmate"})
        assert response.status_code == 200
        assert b"Observation Deck" in response.data


# ---------------------------------------------------------------------------
# Index redirect targets by role
# ---------------------------------------------------------------------------


class TestIndexRedirects:
    """Index redirects to the highest-access page for each role."""

    def test_owner_redirects_to_bridge(self, client):
        response = client.get("/", headers={"X-Auth-Request-User": "testowner"})
        assert response.status_code == 302
        assert "/bridge" in response.headers["Location"]

    def test_manager_redirects_to_porthole(self, client):
        response = client.get("/", headers={"X-Auth-Request-User": "testmanager"})
        assert response.status_code == 302
        assert "/porthole" in response.headers["Location"]

    def test_teammate_redirects_to_observation_deck(self, client):
        response = client.get("/", headers={"X-Auth-Request-User": "testmate"})
        assert response.status_code == 302
        assert "/observation-deck" in response.headers["Location"]
