import enum
import secrets

import flask

ORG_PREFIX = "megadoomer-io:"
SHIP_GROUP_PREFIX = "megadoomer-ship"


class Role(enum.IntEnum):
    CARGO = 0
    CREW = 1
    OFFICERS = 2
    CAPTAIN = 3


ADMIN_GROUP = f"{ORG_PREFIX}admins"

ROLE_GROUPS: list[tuple[str, Role]] = [
    (ADMIN_GROUP, Role.CAPTAIN),
    (f"{ORG_PREFIX}{SHIP_GROUP_PREFIX}-captain", Role.CAPTAIN),
    (f"{ORG_PREFIX}{SHIP_GROUP_PREFIX}-officers", Role.OFFICERS),
    (f"{ORG_PREFIX}{SHIP_GROUP_PREFIX}-crew", Role.CREW),
    (f"{ORG_PREFIX}{SHIP_GROUP_PREFIX}", Role.CARGO),
]

ROUTE_MINIMUM_ROLE: dict[str, Role] = {
    "ship.bridge": Role.CAPTAIN,
    "ship.porthole": Role.CREW,
    "ship.observation_deck": Role.OFFICERS,
    "ship.captains_log": Role.CREW,
    "ship.index": Role.CREW,
}

_SKIP_AUTH_ENDPOINTS = frozenset({"ship.healthz", "static"})
_SKIP_AUTH_PREFIXES = ("/healthz", "/static/")


def parse_groups(header: str) -> list[str]:
    return [g.strip() for g in header.split(",") if g.strip()]


def resolve_role(groups: list[str]) -> Role | None:
    for group, role in ROLE_GROUPS:
        if group in groups:
            return role
    return None


def role_label(role: Role) -> str:
    return role.name.lower()


def available_view_as_roles(actual: Role) -> list[Role]:
    return [r for r in Role if r < actual]


def get_effective_role(actual: Role) -> Role:
    view_as = flask.request.args.get("view_as")
    if view_as == "reset" or view_as == "":
        flask.session.pop("view_as", None)
        return actual
    if view_as is not None:
        try:
            requested = Role[view_as.upper()]
        except KeyError:
            return actual
        if requested < actual:
            flask.session["view_as"] = view_as.lower()
            return requested
        return actual
    stored = flask.session.get("view_as")
    if stored is not None:
        try:
            requested = Role[stored.upper()]
        except KeyError:
            flask.session.pop("view_as", None)
            return actual
        if requested < actual:
            return requested
        flask.session.pop("view_as", None)
    return actual


def check_route_access(endpoint: str | None, role: Role) -> bool:
    if endpoint is None:
        return True
    minimum = ROUTE_MINIMUM_ROLE.get(endpoint)
    if minimum is None:
        return True
    return role >= minimum


def enforce_auth() -> flask.Response | None:
    if flask.request.endpoint in _SKIP_AUTH_ENDPOINTS:
        return None
    if any(flask.request.path.startswith(p) for p in _SKIP_AUTH_PREFIXES):
        return None

    api_token = flask.current_app.config.get("API_TOKEN")
    token_header = flask.request.headers.get("X-Ship-Token")
    if not token_header:
        auth_header = flask.request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token_header = auth_header[7:]
    if not token_header:
        token_header = flask.request.args.get("token")

    if api_token and token_header and secrets.compare_digest(api_token, token_header):
        flask.g.user = "_api"
        flask.g.actual_role = Role.CAPTAIN
        flask.g.role = get_effective_role(Role.CAPTAIN)
        if not check_route_access(flask.request.endpoint, flask.g.role):
            flask.abort(403)
        return None

    user = flask.request.headers.get(
        "X-Auth-Request-Preferred-Username",
        flask.request.headers.get("X-Auth-Request-User"),
    )
    if not user:
        flask.abort(401)

    flask.g.user = user

    groups_header = flask.request.headers.get("X-Auth-Request-Groups", "")
    groups = parse_groups(groups_header)
    actual_role = resolve_role(groups)

    if actual_role is None:
        flask.abort(401)

    flask.g.actual_role = actual_role
    flask.g.role = get_effective_role(actual_role)

    if not check_route_access(flask.request.endpoint, flask.g.role):
        flask.abort(403)

    return None


def handle_403(error: Exception) -> tuple[str, int]:
    role = getattr(flask.g, "role", None)
    actual_role = getattr(flask.g, "actual_role", None)
    endpoint = flask.request.endpoint
    minimum = ROUTE_MINIMUM_ROLE.get(endpoint or "") if endpoint else None

    viewing_as = role != actual_role if (role is not None and actual_role is not None) else False
    suggested_roles: list[Role] = []
    if viewing_as and actual_role is not None and minimum is not None:
        suggested_roles = [r for r in Role if minimum <= r <= actual_role and r != role]

    return flask.render_template(
        "403.html",
        user=getattr(flask.g, "user", None),
        role=role,
        actual_role=actual_role,
        viewing_as=viewing_as,
        minimum_role=minimum,
        suggested_roles=suggested_roles,
        role_label=role_label,
    ), 403


def handle_404(error: Exception) -> tuple[str, int]:
    role = getattr(flask.g, "role", None)
    actual_role = getattr(flask.g, "actual_role", None)
    return flask.render_template(
        "404.html",
        user=getattr(flask.g, "user", None),
        role=role,
        actual_role=actual_role,
    ), 404


def handle_401(error: Exception) -> tuple[str, int]:
    return flask.render_template("401.html"), 401
