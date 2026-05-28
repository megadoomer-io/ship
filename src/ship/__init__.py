import os
import pathlib
import secrets

import flask
import flask_compress

from ship import auth, routes, vault
from ship.middleware import PathPrefixMiddleware

_PORTAL_SHARED_CSS = (
    pathlib.Path(__file__).resolve().parents[3]
    / "portal"
    / "static"
    / "shared.css"
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
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 3600

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
