def test_index_redirects_to_bridge_for_owner(client):
    response = client.get("/", headers={"X-Auth-Request-User": "testowner"})
    assert response.status_code == 302
    assert "/bridge" in response.headers["Location"]


def test_index_redirects_to_porthole_for_non_owner(client):
    response = client.get("/", headers={"X-Auth-Request-User": "someone-else"})
    assert response.status_code == 302
    assert "/porthole" in response.headers["Location"]


def test_index_redirects_to_porthole_for_anonymous(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/porthole" in response.headers["Location"]


def test_bridge_returns_200_for_owner(client):
    response = client.get("/bridge", headers={"X-Auth-Request-User": "testowner"})
    assert response.status_code == 200
    assert b"Bridge" in response.data


def test_bridge_returns_403_for_non_owner(client):
    response = client.get("/bridge", headers={"X-Auth-Request-User": "someone-else"})
    assert response.status_code == 403


def test_bridge_returns_403_for_anonymous(client):
    response = client.get("/bridge")
    assert response.status_code == 403


def test_porthole_returns_200(client):
    response = client.get("/porthole", headers={"X-Auth-Request-User": "someone-else"})
    assert response.status_code == 200
    assert b"Porthole" in response.data


def test_observation_deck_returns_200(client):
    response = client.get("/observation-deck", headers={"X-Auth-Request-User": "someone-else"})
    assert response.status_code == 200
    assert b"Observation Deck" in response.data
