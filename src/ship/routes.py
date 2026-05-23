import os

import flask
import werkzeug.wrappers

from ship import content

bp = flask.Blueprint("ship", __name__)


def _get_user() -> str | None:
    return flask.request.headers.get(
        "X-Auth-Request-User",
        flask.request.headers.get("X-Auth-Request-Preferred-Username"),
    )


def _is_owner(user: str | None) -> bool:
    if not user:
        return False
    owner: str = flask.current_app.config["OWNER_GITHUB_USER"]
    return user == owner


@bp.route("/healthz")
def healthz() -> flask.Response:
    return flask.jsonify({"status": "ok", "git_sha": os.environ.get("GIT_SHA", "unknown")})


@bp.route("/")
def index() -> werkzeug.wrappers.Response:
    user = _get_user()
    if _is_owner(user):
        return flask.redirect(flask.url_for("ship.bridge"))
    return flask.redirect(flask.url_for("ship.porthole"))


@bp.route("/bridge")
def bridge() -> tuple[str, int] | str:
    user = _get_user()
    if not _is_owner(user):
        flask.abort(403)

    vault_path = flask.current_app.config["VAULT_PATH"]
    return flask.render_template(
        "bridge.html",
        is_owner=True,
        user=user,
        active_work=content.get_active_work(vault_path),
        weekly_summary=content.get_weekly_summary(vault_path),
        daily_entries=content.get_daily_entries(vault_path),
    )


@bp.route("/porthole")
def porthole() -> str:
    user = _get_user()
    vault_path = flask.current_app.config["VAULT_PATH"]
    return flask.render_template(
        "porthole.html",
        is_owner=_is_owner(user),
        user=user,
        weekly_summary=content.get_weekly_summary(vault_path),
        active_work=content.get_active_work(vault_path),
    )


@bp.route("/observation-deck")
def observation_deck() -> str:
    user = _get_user()
    return flask.render_template(
        "observation_deck.html",
        is_owner=_is_owner(user),
        user=user,
    )
