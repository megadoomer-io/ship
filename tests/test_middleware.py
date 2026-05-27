import flask
import flask.testing

from ship.middleware import PathPrefixMiddleware

# ---------------------------------------------------------------------------
# Unit tests — exercise the middleware directly
# ---------------------------------------------------------------------------


def _make_environ(path_info: str, script_name: str = "") -> dict[str, str]:
    """Build a minimal WSGI-style environ dict."""
    return {"PATH_INFO": path_info, "SCRIPT_NAME": script_name}


def _noop_app(
    environ: dict[str, object],
    start_response: object,
) -> list[bytes]:
    return [b"ok"]


class TestPathPrefixUnit:
    """Unit tests for PathPrefixMiddleware WSGI environ rewriting."""

    def test_empty_prefix_is_noop(self, monkeypatch: object) -> None:
        """Empty prefix leaves SCRIPT_NAME and PATH_INFO unchanged."""
        import os

        os.environ.pop("SHIP_PATH_PREFIX", None)
        mw = PathPrefixMiddleware(_noop_app)
        env = _make_environ("/bridge")
        mw(env, lambda *a: None)
        assert env["PATH_INFO"] == "/bridge"
        assert env["SCRIPT_NAME"] == ""

    def test_prefix_match_with_content(self, monkeypatch: object) -> None:
        """Prefix stripped, remainder kept in PATH_INFO."""
        import os

        os.environ["SHIP_PATH_PREFIX"] = "/ship"
        try:
            mw = PathPrefixMiddleware(_noop_app)
            env = _make_environ("/ship/bridge")
            mw(env, lambda *a: None)
            assert env["PATH_INFO"] == "/bridge"
            assert env["SCRIPT_NAME"] == "/ship"
        finally:
            del os.environ["SHIP_PATH_PREFIX"]

    def test_prefix_exact_match(self, monkeypatch: object) -> None:
        """Exact prefix match sets PATH_INFO to '/'."""
        import os

        os.environ["SHIP_PATH_PREFIX"] = "/ship"
        try:
            mw = PathPrefixMiddleware(_noop_app)
            env = _make_environ("/ship")
            mw(env, lambda *a: None)
            assert env["PATH_INFO"] == "/"
            assert env["SCRIPT_NAME"] == "/ship"
        finally:
            del os.environ["SHIP_PATH_PREFIX"]

    def test_prefix_with_trailing_slash(self, monkeypatch: object) -> None:
        """Prefix + trailing slash sets PATH_INFO to '/'."""
        import os

        os.environ["SHIP_PATH_PREFIX"] = "/ship"
        try:
            mw = PathPrefixMiddleware(_noop_app)
            env = _make_environ("/ship/")
            mw(env, lambda *a: None)
            assert env["PATH_INFO"] == "/"
            assert env["SCRIPT_NAME"] == "/ship"
        finally:
            del os.environ["SHIP_PATH_PREFIX"]

    def test_prefix_no_match(self, monkeypatch: object) -> None:
        """Non-matching path passes through unchanged."""
        import os

        os.environ["SHIP_PATH_PREFIX"] = "/ship"
        try:
            mw = PathPrefixMiddleware(_noop_app)
            env = _make_environ("/other")
            mw(env, lambda *a: None)
            assert env["PATH_INFO"] == "/other"
            assert env["SCRIPT_NAME"] == ""
        finally:
            del os.environ["SHIP_PATH_PREFIX"]

    def test_prefix_similar_but_not_match(self, monkeypatch: object) -> None:
        """/shipwreck must NOT match prefix /ship."""
        import os

        os.environ["SHIP_PATH_PREFIX"] = "/ship"
        try:
            mw = PathPrefixMiddleware(_noop_app)
            env = _make_environ("/shipwreck")
            mw(env, lambda *a: None)
            assert env["PATH_INFO"] == "/shipwreck"
            assert env["SCRIPT_NAME"] == ""
        finally:
            del os.environ["SHIP_PATH_PREFIX"]

    def test_prefix_nested_path(self, monkeypatch: object) -> None:
        """Deeply nested path retains everything after prefix."""
        import os

        os.environ["SHIP_PATH_PREFIX"] = "/ship"
        try:
            mw = PathPrefixMiddleware(_noop_app)
            env = _make_environ("/ship/static/css/style.css")
            mw(env, lambda *a: None)
            assert env["PATH_INFO"] == "/static/css/style.css"
            assert env["SCRIPT_NAME"] == "/ship"
        finally:
            del os.environ["SHIP_PATH_PREFIX"]


# ---------------------------------------------------------------------------
# Integration tests — Flask test client with prefix
# ---------------------------------------------------------------------------


class TestPathPrefixIntegration:
    """Integration tests verifying Flask routing with the prefix middleware."""

    def test_url_for_includes_prefix(self, prefixed_client: flask.testing.FlaskClient) -> None:
        """url_for generates URLs that include the prefix in redirects."""
        _g = "megadoomer-io:megadoomer-ship"
        response = prefixed_client.get(
            "/ship/",
            headers={
                "X-Auth-Request-User": "testuser",
                "X-Auth-Request-Groups": f"{_g}-captain,{_g}",
            },
        )
        assert response.status_code == 302
        assert "/ship/bridge" in response.headers["Location"]

    def test_url_for_static_includes_prefix(self, prefixed_app: flask.Flask) -> None:
        """url_for for static files includes the prefix."""
        # test_request_context bypasses WSGI middleware, so set SCRIPT_NAME
        # via environ_overrides to simulate what the middleware would do.
        with prefixed_app.test_request_context("/bridge", environ_overrides={"SCRIPT_NAME": "/ship"}):
            url = flask.url_for("static", filename="css/style.css")
            assert url == "/ship/static/css/style.css"

    def test_healthz_accessible_with_prefix(self, prefixed_client: flask.testing.FlaskClient) -> None:
        """Healthz responds 200 at the prefixed path."""
        response = prefixed_client.get("/ship/healthz")
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert data["status"] == "ok"

    def test_auth_bypass_works_with_prefix(self, prefixed_client: flask.testing.FlaskClient) -> None:
        """Auth bypass applies to prefixed healthz and static paths."""
        # healthz — no auth header, should still get 200
        response = prefixed_client.get("/ship/healthz")
        assert response.status_code == 200

        # static — no auth header, should still get 200 or 404 (not 401)
        response = prefixed_client.get("/ship/static/css/style.css")
        assert response.status_code != 401
