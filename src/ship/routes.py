import os

import flask
import werkzeug.wrappers

from ship import content
from ship.auth import Role

bp = flask.Blueprint("ship", __name__)


@bp.route("/healthz")
def healthz() -> flask.Response:
    return flask.jsonify({"status": "ok", "git_sha": os.environ.get("GIT_SHA", "unknown")})


@bp.route("/")
def index() -> werkzeug.wrappers.Response:
    role: Role = flask.g.role
    if role >= Role.OWNER:
        return flask.redirect(flask.url_for("ship.bridge"))
    if role >= Role.MANAGER:
        return flask.redirect(flask.url_for("ship.porthole"))
    return flask.redirect(flask.url_for("ship.observation_deck"))


@bp.route("/bridge")
def bridge() -> str:
    vault_path = flask.current_app.config["VAULT_PATH"]
    return flask.render_template(
        "bridge.html",
        role=flask.g.role,
        user=flask.g.user,
        active_work=content.get_active_work(vault_path),
        weekly_summary=content.get_weekly_summary(vault_path),
        daily_entries=content.get_daily_entries(vault_path),
    )


@bp.route("/porthole")
def porthole() -> str:
    vault_path = flask.current_app.config["VAULT_PATH"]
    return flask.render_template(
        "porthole.html",
        role=flask.g.role,
        user=flask.g.user,
        active_work=content.get_active_work(vault_path),
        weekly_summary=content.get_weekly_summary(vault_path),
        timeline=content.get_timeline(vault_path, limit=10),
    )


@bp.route("/observation-deck")
def observation_deck() -> str:
    vault_path = flask.current_app.config["VAULT_PATH"]
    return flask.render_template(
        "observation_deck.html",
        role=flask.g.role,
        user=flask.g.user,
        timeline=content.get_timeline(vault_path),
    )
