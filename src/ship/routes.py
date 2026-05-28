import os

import flask
import werkzeug.wrappers

from ship import content
from ship.auth import Role
from ship.cache import cached

bp = flask.Blueprint("ship", __name__)


@bp.route("/healthz")
def healthz() -> flask.Response:
    return flask.jsonify({"status": "ok", "git_sha": os.environ.get("GIT_SHA", "unknown")})


@bp.route("/")
def index() -> werkzeug.wrappers.Response:
    role: Role = flask.g.role
    if role >= Role.CAPTAIN:
        return flask.redirect(flask.url_for("ship.bridge"))
    if role >= Role.OFFICERS:
        return flask.redirect(flask.url_for("ship.observation_deck"))
    return flask.redirect(flask.url_for("ship.porthole"))


@bp.route("/bridge")
def bridge() -> str:
    vault_path = flask.current_app.config["VAULT_PATH"]
    return flask.render_template(
        "bridge.html",
        role=flask.g.role,
        actual_role=flask.g.actual_role,
        user=flask.g.user,
        active_work=cached("active_work", content.get_active_work, vault_path),
        weekly_summary=cached("weekly_summary", content.get_weekly_summary, vault_path),
        daily_entries=cached("daily_entries", content.get_daily_entries, vault_path),
    )


@bp.route("/porthole")
def porthole() -> str:
    vault_path = flask.current_app.config["VAULT_PATH"]
    limit = 10
    return flask.render_template(
        "porthole.html",
        role=flask.g.role,
        actual_role=flask.g.actual_role,
        user=flask.g.user,
        timeline=cached(f"timeline:{limit}", content.get_timeline, vault_path, limit=limit),
    )


@bp.route("/observation-deck")
def observation_deck() -> str:
    vault_path = flask.current_app.config["VAULT_PATH"]
    period = flask.request.args.get("period", "week")
    highlight_week = flask.request.args.get("week")
    feed = cached(f"feed:{period}", content.get_hierarchical_feed, vault_path, period=period)
    return flask.render_template(
        "observation_deck.html",
        role=flask.g.role,
        actual_role=flask.g.actual_role,
        user=flask.g.user,
        feed=feed,
        active_work=cached("active_work", content.get_active_work, vault_path),
        current_period=period,
        highlight_week=highlight_week,
    )


@bp.route("/captains-log")
def captains_log() -> str:
    vault_path = flask.current_app.config["VAULT_PATH"]
    limit = 10
    retros = cached(f"retros:{limit}", content.get_retro_summaries, vault_path, limit=limit)
    return flask.render_template(
        "captains_log.html",
        role=flask.g.role,
        actual_role=flask.g.actual_role,
        user=flask.g.user,
        retros=retros,
    )


@bp.route("/api/feed")
def api_feed() -> str:
    vault_path = flask.current_app.config["VAULT_PATH"]
    offset = flask.request.args.get("offset", 0, type=int)
    limit = min(flask.request.args.get("limit", 4, type=int), 20)
    period = flask.request.args.get("period", "week")
    feed = cached(
        f"feed:{period}:{offset}:{limit}",
        content.get_hierarchical_feed,
        vault_path,
        period=period,
        offset=offset,
        limit=limit,
    )
    return flask.render_template("_feed_fragment.html", feed=feed, is_fragment=True)


@bp.route("/api/timeline")
def api_timeline() -> str:
    vault_path = flask.current_app.config["VAULT_PATH"]
    offset = flask.request.args.get("offset", 0, type=int)
    limit = min(flask.request.args.get("limit", 10, type=int), 50)
    timeline = cached(
        f"timeline:{offset}:{limit}",
        content.get_timeline,
        vault_path,
        limit=limit,
        offset=offset,
    )
    return flask.render_template("_timeline_fragment.html", timeline=timeline, is_fragment=True)


@bp.route("/api/retros")
def api_retros() -> str:
    vault_path = flask.current_app.config["VAULT_PATH"]
    offset = flask.request.args.get("offset", 0, type=int)
    limit = min(flask.request.args.get("limit", 10, type=int), 20)
    retros = cached(
        f"retros:{offset}:{limit}",
        content.get_retro_summaries,
        vault_path,
        limit=limit,
        offset=offset,
    )
    return flask.render_template("_retros_fragment.html", retros=retros, is_fragment=True)
