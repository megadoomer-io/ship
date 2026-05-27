import pytest

from ship.auth import Role, check_route_access, parse_groups, resolve_role, role_label

# ---------------------------------------------------------------------------
# parse_groups
# ---------------------------------------------------------------------------


class TestParseGroups:
    def test_empty_string(self):
        assert parse_groups("") == []

    def test_single_group(self):
        assert parse_groups("megadoomer-io:megadoomer-ship") == ["megadoomer-io:megadoomer-ship"]

    def test_multiple_groups(self):
        result = parse_groups("megadoomer-io:megadoomer-ship,megadoomer-io:media")
        assert result == ["megadoomer-io:megadoomer-ship", "megadoomer-io:media"]

    def test_whitespace_handling(self):
        result = parse_groups("  megadoomer-io:megadoomer-ship , megadoomer-io:media  ")
        assert result == ["megadoomer-io:megadoomer-ship", "megadoomer-io:media"]

    def test_empty_entries_ignored(self):
        result = parse_groups("megadoomer-io:megadoomer-ship,,megadoomer-io:media")
        assert result == ["megadoomer-io:megadoomer-ship", "megadoomer-io:media"]


# ---------------------------------------------------------------------------
# resolve_role
# ---------------------------------------------------------------------------


class TestResolveRole:
    def test_captain(self):
        groups = ["megadoomer-io:megadoomer-ship-captain", "megadoomer-io:megadoomer-ship"]
        assert resolve_role(groups) == Role.CAPTAIN

    def test_officers(self):
        groups = ["megadoomer-io:megadoomer-ship-officers", "megadoomer-io:megadoomer-ship"]
        assert resolve_role(groups) == Role.OFFICERS

    def test_crew(self):
        groups = ["megadoomer-io:megadoomer-ship-crew", "megadoomer-io:megadoomer-ship"]
        assert resolve_role(groups) == Role.CREW

    def test_cargo(self):
        groups = ["megadoomer-io:megadoomer-ship"]
        assert resolve_role(groups) == Role.CARGO

    def test_no_ship_groups(self):
        groups = ["megadoomer-io:media", "megadoomer-io:resonance"]
        assert resolve_role(groups) is None

    def test_empty_groups(self):
        assert resolve_role([]) is None

    def test_captain_takes_precedence(self):
        groups = [
            "megadoomer-io:megadoomer-ship-captain",
            "megadoomer-io:megadoomer-ship-officers",
            "megadoomer-io:megadoomer-ship-crew",
            "megadoomer-io:megadoomer-ship",
        ]
        assert resolve_role(groups) == Role.CAPTAIN

    def test_admins_resolves_to_captain(self):
        groups = ["megadoomer-io:admins"]
        assert resolve_role(groups) == Role.CAPTAIN

    def test_legacy_admins_resolves_to_captain(self):
        groups = ["megadoomer-io:megadoomer-admins"]
        assert resolve_role(groups) == Role.CAPTAIN

    def test_admins_without_ship_groups(self):
        groups = ["megadoomer-io:admins", "megadoomer-io:media"]
        assert resolve_role(groups) == Role.CAPTAIN

    def test_admins_takes_priority_over_lower_ship_role(self):
        groups = ["megadoomer-io:megadoomer-ship-crew", "megadoomer-io:admins"]
        assert resolve_role(groups) == Role.CAPTAIN

    def test_existing_ship_groups_unchanged(self):
        assert resolve_role(["megadoomer-io:megadoomer-ship-officers"]) == Role.OFFICERS
        assert resolve_role(["megadoomer-io:megadoomer-ship-crew"]) == Role.CREW
        assert resolve_role(["megadoomer-io:megadoomer-ship"]) == Role.CARGO


# ---------------------------------------------------------------------------
# role_label
# ---------------------------------------------------------------------------


class TestRoleLabel:
    def test_labels(self):
        assert role_label(Role.CARGO) == "cargo"
        assert role_label(Role.CREW) == "crew"
        assert role_label(Role.OFFICERS) == "officers"
        assert role_label(Role.CAPTAIN) == "captain"


# ---------------------------------------------------------------------------
# check_route_access
# ---------------------------------------------------------------------------


class TestCheckRouteAccess:
    @pytest.mark.parametrize(
        ("endpoint", "role", "expected"),
        [
            # bridge -- CAPTAIN only
            ("ship.bridge", Role.CAPTAIN, True),
            ("ship.bridge", Role.OFFICERS, False),
            ("ship.bridge", Role.CREW, False),
            ("ship.bridge", Role.CARGO, False),
            # observation_deck -- OFFICERS+
            ("ship.observation_deck", Role.CAPTAIN, True),
            ("ship.observation_deck", Role.OFFICERS, True),
            ("ship.observation_deck", Role.CREW, False),
            ("ship.observation_deck", Role.CARGO, False),
            # porthole -- CREW+
            ("ship.porthole", Role.CAPTAIN, True),
            ("ship.porthole", Role.OFFICERS, True),
            ("ship.porthole", Role.CREW, True),
            ("ship.porthole", Role.CARGO, False),
            # captains_log -- CREW+
            ("ship.captains_log", Role.CAPTAIN, True),
            ("ship.captains_log", Role.OFFICERS, True),
            ("ship.captains_log", Role.CREW, True),
            ("ship.captains_log", Role.CARGO, False),
            # index -- CREW+
            ("ship.index", Role.CAPTAIN, True),
            ("ship.index", Role.CREW, True),
            ("ship.index", Role.CARGO, False),
            # healthz -- not in ROUTE_MINIMUM_ROLE, so any role gets access
            ("ship.healthz", Role.CARGO, True),
        ],
    )
    def test_access_matrix(self, endpoint: str, role: Role, expected: bool):
        assert check_route_access(endpoint, role) is expected

    def test_none_endpoint_denied(self):
        assert check_route_access(None, Role.CAPTAIN) is False

    def test_unknown_endpoint_allowed(self):
        assert check_route_access("ship.some_unknown_route", Role.CARGO) is True
