import enum

import flask


class Role(enum.IntEnum):
    TEAMMATE = 1
    MANAGER = 2
    OWNER = 3


ROUTE_MINIMUM_ROLE: dict[str, Role] = {
    "ship.bridge": Role.OWNER,
    "ship.porthole": Role.MANAGER,
    "ship.observation_deck": Role.TEAMMATE,
    "ship.index": Role.TEAMMATE,
}

_SKIP_AUTH_ENDPOINTS = frozenset({"ship.healthz", "static"})
_SKIP_AUTH_PREFIXES = ("/healthz", "/static/")


def parse_user_list(raw: str) -> frozenset[str]:
    return frozenset(u.strip().lower() for u in raw.split(",") if u.strip())


def get_user_role(config: dict[str, object], username: str) -> Role | None:
    lower = username.lower()
    owners = config.get("AUTH_OWNERS", frozenset())
    managers = config.get("AUTH_MANAGERS", frozenset())
    teammates = config.get("AUTH_TEAMMATES", frozenset())
    assert isinstance(owners, frozenset)
    assert isinstance(managers, frozenset)
    assert isinstance(teammates, frozenset)
    if lower in owners:
        return Role.OWNER
    if lower in managers:
        return Role.MANAGER
    if lower in teammates:
        return Role.TEAMMATE
    return None


def check_route_access(endpoint: str | None, role: Role) -> bool:
    if endpoint is None:
        return False
    minimum = ROUTE_MINIMUM_ROLE.get(endpoint)
    if minimum is None:
        return True
    return role >= minimum


def enforce_auth() -> flask.Response | None:
    if flask.request.endpoint in _SKIP_AUTH_ENDPOINTS:
        return None
    if any(flask.request.path.startswith(p) for p in _SKIP_AUTH_PREFIXES):
        return None

    user = flask.request.headers.get(
        "X-Auth-Request-User",
        flask.request.headers.get("X-Auth-Request-Preferred-Username"),
    )
    if not user:
        flask.abort(401)

    flask.g.user = user

    role = get_user_role(flask.current_app.config, user)
    if role is None:
        flask.abort(403)

    flask.g.role = role

    if not check_route_access(flask.request.endpoint, role):
        flask.abort(403)

    return None


def handle_403(error: Exception) -> tuple[str, int]:
    return flask.render_template(
        "403.html",
        user=getattr(flask.g, "user", None),
        role=getattr(flask.g, "role", None),
    ), 403


def handle_401(error: Exception) -> tuple[str, int]:
    return "Unauthorized", 401
