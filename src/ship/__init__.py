import os

import flask

from ship import routes, vault


def create_app() -> flask.Flask:
    app = flask.Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    app.config["VAULT_REPO"] = os.environ.get("SHIP_VAULT_REPO", "")
    app.config["VAULT_PATH"] = os.environ.get("SHIP_VAULT_PATH", "/tmp/vault")
    app.config["OWNER_GITHUB_USER"] = os.environ.get("SHIP_OWNER_GITHUB_USER", "")
    app.config["PULL_INTERVAL_SECONDS"] = int(os.environ.get("SHIP_PULL_INTERVAL_SECONDS", "300"))

    app.register_blueprint(routes.bp)

    if not app.config.get("TESTING"):
        vault.start_sync(app)

    return app
