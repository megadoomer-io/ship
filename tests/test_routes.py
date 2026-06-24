import pytest

from ship.dev import create_mock_vault
from tests.conftest import CAPTAIN_GROUPS, CARGO_GROUPS, CREW_GROUPS, OFFICERS_GROUPS, auth_headers

# ---------------------------------------------------------------------------
# Healthz -- no auth required
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


@pytest.mark.parametrize("groups", [CAPTAIN_GROUPS, OFFICERS_GROUPS, CREW_GROUPS, CARGO_GROUPS])
def test_healthz_returns_200_for_any_role(client, groups):
    response = client.get("/healthz", headers=auth_headers("testuser", groups))
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Anonymous (no header) -> 401 on all protected routes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/", "/bridge", "/porthole", "/observation-deck", "/captains-log", "/course"])
def test_anonymous_gets_401(client, path):
    response = client.get(path)
    assert response.status_code == 401
    assert b"Sign in" in response.data


# ---------------------------------------------------------------------------
# Authenticated but no ship groups -> 401
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/", "/bridge", "/porthole", "/observation-deck"])
def test_no_ship_groups_gets_401(client, path):
    response = client.get(path, headers=auth_headers("testuser", "megadoomer-io:media"))
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Cargo (megadoomer-ship only, no sub-role) -> 403 on content routes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/bridge", "/porthole", "/observation-deck", "/captains-log", "/course"])
def test_cargo_gets_403(client, path):
    response = client.get(path, headers=auth_headers("testuser", CARGO_GROUPS))
    assert response.status_code == 403
    assert b"cargo hold" in response.data


# ---------------------------------------------------------------------------
# Full role x route access matrix
# ---------------------------------------------------------------------------


class TestBridge:
    def test_captain_gets_200(self, client):
        response = client.get("/bridge", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 200
        assert b"Bridge" in response.data

    def test_officers_gets_403(self, client):
        response = client.get("/bridge", headers=auth_headers("testuser", OFFICERS_GROUPS))
        assert response.status_code == 403

    def test_crew_gets_403(self, client):
        response = client.get("/bridge", headers=auth_headers("testuser", CREW_GROUPS))
        assert response.status_code == 403


class TestObservationDeck:
    def test_captain_gets_200(self, client):
        response = client.get("/observation-deck", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 200
        assert b"Observation Deck" in response.data

    def test_officers_gets_200(self, client):
        response = client.get("/observation-deck", headers=auth_headers("testuser", OFFICERS_GROUPS))
        assert response.status_code == 200
        assert b"Observation Deck" in response.data

    def test_crew_gets_403(self, client):
        response = client.get("/observation-deck", headers=auth_headers("testuser", CREW_GROUPS))
        assert response.status_code == 403


class TestPorthole:
    def test_captain_gets_200(self, client):
        response = client.get("/porthole", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 200
        assert b"Porthole" in response.data

    def test_officers_gets_200(self, client):
        response = client.get("/porthole", headers=auth_headers("testuser", OFFICERS_GROUPS))
        assert response.status_code == 200
        assert b"Porthole" in response.data

    def test_crew_gets_200(self, client):
        response = client.get("/porthole", headers=auth_headers("testuser", CREW_GROUPS))
        assert response.status_code == 200
        assert b"Porthole" in response.data


class TestCaptainsLog:
    def test_captain_gets_200(self, client):
        response = client.get("/captains-log", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 200

    def test_crew_gets_200(self, client):
        response = client.get("/captains-log", headers=auth_headers("testuser", CREW_GROUPS))
        assert response.status_code == 200

    def test_cargo_gets_403(self, client):
        response = client.get("/captains-log", headers=auth_headers("testuser", CARGO_GROUPS))
        assert response.status_code == 403


class TestCourse:
    def test_captain_gets_200(self, client):
        response = client.get("/course", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 200

    def test_crew_gets_200(self, client):
        response = client.get("/course", headers=auth_headers("testuser", CREW_GROUPS))
        assert response.status_code == 200

    def test_cargo_gets_403(self, client):
        response = client.get("/course", headers=auth_headers("testuser", CARGO_GROUPS))
        assert response.status_code == 403

    def test_contains_plan_content(self, client):
        response = client.get("/course", headers=auth_headers("testuser", CREW_GROUPS))
        assert b"Course" in response.data
        assert b"charted course" in response.data


# ---------------------------------------------------------------------------
# Index redirect targets by role
# ---------------------------------------------------------------------------


class TestIndexRedirects:
    def test_captain_redirects_to_bridge(self, client):
        response = client.get("/", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 302
        assert "/bridge" in response.headers["Location"]

    def test_officers_redirects_to_observation_deck(self, client):
        response = client.get("/", headers=auth_headers("testuser", OFFICERS_GROUPS))
        assert response.status_code == 302
        assert "/observation-deck" in response.headers["Location"]

    def test_crew_redirects_to_porthole(self, client):
        response = client.get("/", headers=auth_headers("testuser", CREW_GROUPS))
        assert response.status_code == 302
        assert "/porthole" in response.headers["Location"]


# ---------------------------------------------------------------------------
# API token auth
# ---------------------------------------------------------------------------


class TestApiToken:
    def test_x_ship_token_header(self, client):
        response = client.get("/bridge", headers={"X-Ship-Token": "test-api-token-secret"})
        assert response.status_code == 200

    def test_bearer_token(self, client):
        response = client.get("/bridge", headers={"Authorization": "Bearer test-api-token-secret"})
        assert response.status_code == 200

    def test_invalid_token_gets_401(self, client):
        response = client.get("/bridge", headers={"X-Ship-Token": "wrong-token"})
        assert response.status_code == 401

    def test_query_param_token_ignored(self, client):
        response = client.get("/bridge?token=test-api-token-secret")
        assert response.status_code == 401

    def test_empty_token_config_disables_api_auth(self, client):
        client.application.config["API_TOKEN"] = ""
        response = client.get("/bridge", headers={"X-Ship-Token": ""})
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# View-as
# ---------------------------------------------------------------------------


class TestViewAs:
    def test_captain_can_view_as_crew(self, client):
        response = client.get("/porthole?view_as=crew", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 200

    def test_view_as_denies_restricted_page(self, client):
        response = client.get("/bridge?view_as=crew", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 403

    def test_view_as_persists_in_session(self, client):
        with client.session_transaction() as sess:
            sess["view_as"] = "crew"
        response = client.get("/bridge", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 403

    def test_view_as_reset(self, client):
        with client.session_transaction() as sess:
            sess["view_as"] = "crew"
        response = client.get("/bridge?view_as=reset", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 200

    def test_cannot_view_as_higher_role(self, client):
        response = client.get("/bridge?view_as=captain", headers=auth_headers("testuser", CREW_GROUPS))
        assert response.status_code == 403

    def test_403_suggests_roles_when_viewing_as(self, client):
        response = client.get("/bridge?view_as=crew", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 403
        assert b"view_as=captain" in response.data or b"view_as=officers" in response.data


# ---------------------------------------------------------------------------
# 404 handling
# ---------------------------------------------------------------------------


class TestNotFound:
    def test_unknown_route_returns_404(self, client):
        response = client.get("/nonexistent", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 404
        assert b"Not Found" in response.data

    def test_404_shows_username(self, client):
        response = client.get("/nonexistent", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert b"testuser" in response.data

    def test_404_without_auth_gets_401(self, client):
        response = client.get("/nonexistent")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# shared.css dev route
# ---------------------------------------------------------------------------


class TestSharedCssDev:
    def test_shared_css_served_in_debug_mode(self, tmp_path, monkeypatch):
        import ship

        vault_path = str(tmp_path / "vault")
        create_mock_vault(vault_path)
        monkeypatch.setenv("SHIP_VAULT_REPO", "")
        monkeypatch.setenv("SHIP_VAULT_PATH", vault_path)
        monkeypatch.setenv("FLASK_DEBUG", "1")

        app = ship.create_app()
        app.config["TESTING"] = True

        with app.test_client() as c:
            response = c.get("/shared.css")
            if ship._PORTAL_SHARED_CSS.exists():
                assert response.status_code == 200
                assert response.content_type == "text/css; charset=utf-8"
            else:
                assert response.status_code in (401, 404)

    def test_shared_css_not_served_in_production(self, client):
        response = client.get("/shared.css")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


class TestApiFeed:
    def test_returns_html(self, client):
        response = client.get("/api/feed", headers=auth_headers("testuser", OFFICERS_GROUPS))
        assert response.status_code == 200
        assert "text/html" in response.content_type

    def test_requires_officers(self, client):
        response = client.get("/api/feed", headers=auth_headers("testuser", CREW_GROUPS))
        assert response.status_code == 403

    def test_no_auth_returns_401(self, client):
        response = client.get("/api/feed")
        assert response.status_code == 401

    def test_offset_and_limit(self, client):
        response = client.get("/api/feed?offset=0&limit=2", headers=auth_headers("testuser", OFFICERS_GROUPS))
        assert response.status_code == 200

    def test_caps_limit(self, client):
        response = client.get("/api/feed?limit=100", headers=auth_headers("testuser", OFFICERS_GROUPS))
        assert response.status_code == 200


class TestApiTimeline:
    def test_returns_html(self, client):
        response = client.get("/api/timeline", headers=auth_headers("testuser", CREW_GROUPS))
        assert response.status_code == 200
        assert "text/html" in response.content_type

    def test_requires_crew(self, client):
        response = client.get("/api/timeline", headers=auth_headers("testuser", CARGO_GROUPS))
        assert response.status_code == 403

    def test_no_auth_returns_401(self, client):
        response = client.get("/api/timeline")
        assert response.status_code == 401

    def test_offset(self, client):
        response = client.get("/api/timeline?offset=10", headers=auth_headers("testuser", CREW_GROUPS))
        assert response.status_code == 200


class TestApiVersion:
    def test_returns_generation(self, client):
        response = client.get("/api/version", headers=auth_headers("testuser", CREW_GROUPS))
        assert response.status_code == 200
        data = response.get_json()
        assert "generation" in data
        assert isinstance(data["generation"], int)

    def test_requires_crew(self, client):
        response = client.get("/api/version", headers=auth_headers("testuser", CARGO_GROUPS))
        assert response.status_code == 403

    def test_no_auth_returns_401(self, client):
        response = client.get("/api/version")
        assert response.status_code == 401


class TestApiCaptainsLog:
    def test_returns_html(self, client):
        response = client.get("/api/captains-log", headers=auth_headers("testuser", CREW_GROUPS))
        assert response.status_code == 200
        assert "text/html" in response.content_type

    def test_requires_crew(self, client):
        response = client.get("/api/captains-log", headers=auth_headers("testuser", CARGO_GROUPS))
        assert response.status_code == 403

    def test_no_auth_returns_401(self, client):
        response = client.get("/api/captains-log")
        assert response.status_code == 401

    def test_offset_beyond_data_returns_empty(self, client):
        response = client.get("/api/captains-log?offset=1000", headers=auth_headers("testuser", CREW_GROUPS))
        assert response.status_code == 200
        assert response.data.strip() == b""


class TestFilterBar:
    """The filter bar is shared base-layout UI; it should render on every
    authenticated content page and load filter.js."""

    @pytest.mark.parametrize("path", ["/bridge", "/porthole", "/observation-deck", "/captains-log", "/course"])
    def test_filter_bar_present_for_captain(self, client, path):
        response = client.get(path, headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 200
        assert b"data-filter-bar" in response.data
        assert b'id="filter-input"' in response.data
        assert b"press / to filter" in response.data
        assert b"filter.js" in response.data

    def test_filter_bar_absent_for_unauthenticated(self, client):
        # 401 page has no nav; filter bar is part of the nav row stack.
        response = client.get("/bridge")
        assert response.status_code == 401
        assert b"data-filter-bar" not in response.data

    def test_bridge_daily_entries_marked_filterable(self, client):
        response = client.get("/bridge", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 200
        assert b"data-filterable" in response.data

    def test_obs_deck_entries_marked_filterable(self, client):
        response = client.get("/observation-deck", headers=auth_headers("testuser", CAPTAIN_GROUPS))
        assert response.status_code == 200
        # Per-day entries inside the feed fragment carry data-filterable.
        assert b"data-filterable" in response.data
