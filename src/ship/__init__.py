import contextlib
import os
import pathlib
import re
import secrets
from typing import Any

import flask
import flask_compress

from ship import auth, routes, vault
from ship.cache import ContentCache
from ship.collapse import collapse_sections
from ship.middleware import PathPrefixMiddleware

_H1_RE = re.compile(r"<h[13][^>]*>(.*?)</h[13]>", re.DOTALL)

_PORTAL_SHARED_CSS = pathlib.Path(__file__).resolve().parents[3] / "portal" / "static" / "shared.css"
if not _PORTAL_SHARED_CSS.exists():
    _PORTAL_SHARED_CSS = (
        pathlib.Path.home() / "src" / "github.com" / "megadoomer-io" / "portal" / "static" / "shared.css"
    )


def create_app() -> flask.Flask:
    app = flask.Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    app.config["VAULT_REPO"] = os.environ.get("SHIP_VAULT_REPO", "")
    app.config["VAULT_CLONE_PATH"] = os.environ.get("SHIP_VAULT_CLONE_PATH", "/tmp/vault-clone")
    app.config["VAULT_PATH"] = os.environ.get("SHIP_VAULT_PATH", "/tmp/vault")
    app.config["PULL_INTERVAL_SECONDS"] = int(os.environ.get("SHIP_PULL_INTERVAL_SECONDS", "300"))

    app.config["API_TOKEN"] = os.environ.get("SHIP_API_TOKEN", "")
    app.secret_key = os.environ.get("SHIP_SECRET_KEY", secrets.token_hex(32))

    app.config["COMPRESS_MIMETYPES"] = ["text/html", "text/css", "application/json"]
    # Debug serves fresh assets every reload so CSS/JS edits show up without
    # hard-refresh; prod relies on the 1h cache + redeploy cadence.
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0 if app.debug else 3600

    app.extensions["content_cache"] = ContentCache()

    @app.template_filter("extract_title")
    def extract_title_filter(html: str) -> str:
        match = _H1_RE.search(html)
        return match.group(1).strip() if match else "Entry"

    @app.template_filter("collapse_sections")
    def collapse_sections_filter(html: str, content_type: str | None = None) -> str:
        return collapse_sections(html, content_type)

    # Append ?v=<mtime> to static URLs so browsers re-fetch when files change
    # on disk. Without this, the 1h cache + same URL means edits don't show
    # until the cache window expires or the user hard-reloads.
    _static_root = pathlib.Path(app.static_folder) if app.static_folder else None

    @app.url_defaults
    def _static_cache_bust(endpoint: str, values: dict[str, Any]) -> None:
        if endpoint != "static" or not _static_root or "v" in values:
            return
        filename = values.get("filename")
        if not filename:
            return
        path = _static_root / filename
        with contextlib.suppress(OSError):
            values["v"] = int(path.stat().st_mtime)

    flask_compress.Compress(app)
    app.register_blueprint(routes.bp)
    app.before_request(auth.enforce_auth)
    app.register_error_handler(401, auth.handle_401)
    app.register_error_handler(403, auth.handle_403)
    app.register_error_handler(404, auth.handle_404)

    if app.debug and _PORTAL_SHARED_CSS.exists():

        @app.route("/shared.css")
        def shared_css() -> flask.Response:
            return flask.send_file(_PORTAL_SHARED_CSS, mimetype="text/css")

    if not app.config.get("TESTING"):
        vault.start_sync(app)

    app.wsgi_app = PathPrefixMiddleware(app.wsgi_app)  # type: ignore[method-assign]

    return app
