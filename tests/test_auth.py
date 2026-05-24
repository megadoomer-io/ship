import pytest

from ship.auth import Role, check_route_access, get_user_role, parse_user_list

# ---------------------------------------------------------------------------
# parse_user_list
# ---------------------------------------------------------------------------


class TestParseUserList:
    def test_empty_string(self):
        assert parse_user_list("") == frozenset()

    def test_single_user(self):
        assert parse_user_list("alice") == frozenset({"alice"})

    def test_multiple_users(self):
        result = parse_user_list("alice,bob,carol")
        assert result == frozenset({"alice", "bob", "carol"})

    def test_whitespace_handling(self):
        result = parse_user_list("  alice , bob , carol  ")
        assert result == frozenset({"alice", "bob", "carol"})

    def test_case_normalization(self):
        result = parse_user_list("Alice,BOB,Carol")
        assert result == frozenset({"alice", "bob", "carol"})

    def test_trailing_comma(self):
        result = parse_user_list("alice,bob,")
        assert result == frozenset({"alice", "bob"})

    def test_empty_entries_ignored(self):
        result = parse_user_list("alice,,bob,,,carol")
        assert result == frozenset({"alice", "bob", "carol"})


# ---------------------------------------------------------------------------
# get_user_role
# ---------------------------------------------------------------------------


class TestGetUserRole:
    @pytest.fixture()
    def config(self) -> dict[str, object]:
        return {
            "AUTH_OWNERS": frozenset({"alice"}),
            "AUTH_MANAGERS": frozenset({"bob"}),
            "AUTH_TEAMMATES": frozenset({"carol"}),
        }

    def test_owner(self, config):
        assert get_user_role(config, "alice") == Role.OWNER

    def test_manager(self, config):
        assert get_user_role(config, "bob") == Role.MANAGER

    def test_teammate(self, config):
        assert get_user_role(config, "carol") == Role.TEAMMATE

    def test_unlisted_user_returns_none(self, config):
        assert get_user_role(config, "stranger") is None

    def test_case_insensitive(self, config):
        assert get_user_role(config, "ALICE") == Role.OWNER
        assert get_user_role(config, "Bob") == Role.MANAGER
        assert get_user_role(config, "CAROL") == Role.TEAMMATE

    def test_owner_takes_precedence_over_manager(self):
        """A user listed in both owners and managers gets OWNER."""
        config: dict[str, object] = {
            "AUTH_OWNERS": frozenset({"alice"}),
            "AUTH_MANAGERS": frozenset({"alice"}),
            "AUTH_TEAMMATES": frozenset(),
        }
        assert get_user_role(config, "alice") == Role.OWNER

    def test_empty_lists_returns_none(self):
        config: dict[str, object] = {
            "AUTH_OWNERS": frozenset(),
            "AUTH_MANAGERS": frozenset(),
            "AUTH_TEAMMATES": frozenset(),
        }
        assert get_user_role(config, "anyone") is None


# ---------------------------------------------------------------------------
# check_route_access
# ---------------------------------------------------------------------------


class TestCheckRouteAccess:
    """Routes require minimum role: bridge=OWNER, porthole=MANAGER,
    observation_deck=TEAMMATE, index=TEAMMATE."""

    @pytest.mark.parametrize(
        ("endpoint", "role", "expected"),
        [
            # bridge — OWNER only
            ("ship.bridge", Role.OWNER, True),
            ("ship.bridge", Role.MANAGER, False),
            ("ship.bridge", Role.TEAMMATE, False),
            # porthole — MANAGER+
            ("ship.porthole", Role.OWNER, True),
            ("ship.porthole", Role.MANAGER, True),
            ("ship.porthole", Role.TEAMMATE, False),
            # observation_deck — TEAMMATE+
            ("ship.observation_deck", Role.OWNER, True),
            ("ship.observation_deck", Role.MANAGER, True),
            ("ship.observation_deck", Role.TEAMMATE, True),
            # index — TEAMMATE+
            ("ship.index", Role.OWNER, True),
            ("ship.index", Role.MANAGER, True),
            ("ship.index", Role.TEAMMATE, True),
            # healthz — not in ROUTE_MINIMUM_ROLE, so any role gets access
            ("ship.healthz", Role.TEAMMATE, True),
        ],
    )
    def test_access_matrix(self, endpoint: str, role: Role, expected: bool):
        assert check_route_access(endpoint, role) is expected

    def test_none_endpoint_denied(self):
        assert check_route_access(None, Role.OWNER) is False

    def test_unknown_endpoint_allowed(self):
        """Endpoints not in ROUTE_MINIMUM_ROLE default to open."""
        assert check_route_access("ship.some_unknown_route", Role.TEAMMATE) is True
