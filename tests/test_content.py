import datetime
import pathlib

import flask
import flask.testing
import pytest

import ship
import ship.content as content
from ship.dev import create_mock_vault


@pytest.fixture()
def vault(tmp_path: pathlib.Path) -> str:
    vault_path = str(tmp_path / "vault")
    create_mock_vault(vault_path)
    return vault_path


class TestParseFrontmatter:
    def test_valid_frontmatter(self) -> None:
        text = "---\ntitle: hello\ncount: 5\n---\n\nBody text here."
        meta, body = content.parse_frontmatter(text)
        assert meta["title"] == "hello"
        assert meta["count"] == 5
        assert "Body text here." in body

    def test_no_frontmatter(self) -> None:
        text = "Just a plain document.\nNo frontmatter."
        meta, body = content.parse_frontmatter(text)
        assert meta == {}
        assert body == text

    def test_malformed_yaml(self) -> None:
        text = "---\n: bad: yaml: [unclosed\n---\n\nBody."
        meta, body = content.parse_frontmatter(text)
        assert meta == {}
        assert body == text

    def test_nested_frontmatter(self) -> None:
        text = "---\nprojects:\n  - ship\n  - argo\nmetrics:\n  prs: 12\n---\n\nBody."
        meta, body = content.parse_frontmatter(text)
        assert meta["projects"] == ["ship", "argo"]
        assert isinstance(meta["metrics"], dict)
        assert meta["metrics"]["prs"] == 12

    def test_non_dict_frontmatter(self) -> None:
        text = "---\n- just\n- a\n- list\n---\n\nBody."
        meta, body = content.parse_frontmatter(text)
        assert meta == {}

    def test_unclosed_frontmatter(self) -> None:
        text = "---\ntitle: hello\nNo closing fence here."
        meta, body = content.parse_frontmatter(text)
        assert meta == {}
        assert body == text


class TestExtractTitle:
    def test_no_heading(self) -> None:
        assert content._extract_title("No headings here.\nJust text.") == "Untitled"

    def test_h1_heading(self) -> None:
        assert content._extract_title("# My Title\n\nBody.") == "My Title"


class TestParseDateField:
    def test_date_object(self) -> None:
        d = datetime.date(2026, 5, 18)
        assert content._parse_date_field(d) == d

    def test_valid_iso_string(self) -> None:
        assert content._parse_date_field("2026-05-18") == datetime.date(2026, 5, 18)

    def test_invalid_string(self) -> None:
        assert content._parse_date_field("not-a-date") is None

    def test_non_date_type(self) -> None:
        assert content._parse_date_field(12345) is None


class TestGetRetroSummaries:
    def test_returns_items(self, vault: str) -> None:
        items = content.get_retro_summaries(vault)
        assert len(items) >= 1
        item = items[0]
        assert item["content_type"] == "retro"
        assert isinstance(item["date"], datetime.date)
        assert "Retro:" in item["title"]
        assert "<" in item["rendered_html"]

    def test_metadata_preserved(self, vault: str) -> None:
        items = content.get_retro_summaries(vault)
        meta = items[0]["metadata"]
        assert meta["type"] == "retro"
        assert meta["period"] == "2026-W21"

    def test_empty_vault(self, tmp_path: pathlib.Path) -> None:
        items = content.get_retro_summaries(str(tmp_path))
        assert items == []

    def test_limit(self, vault: str) -> None:
        items = content.get_retro_summaries(vault, limit=0)
        assert items == []

    def test_higher_limit_returns_all(self, vault: str) -> None:
        items = content.get_retro_summaries(vault, limit=20)
        assert len(items) >= 1


class TestGetTimeline:
    def test_returns_mixed_items(self, vault: str) -> None:
        items = content.get_timeline(vault)
        types = {item["content_type"] for item in items}
        assert "retro" in types
        assert "weekly" in types

    def test_sorted_descending(self, vault: str) -> None:
        items = content.get_timeline(vault)
        if len(items) > 1:
            for i in range(len(items) - 1):
                assert items[i]["date"] >= items[i + 1]["date"]

    def test_limit(self, vault: str) -> None:
        items = content.get_timeline(vault, limit=1)
        assert len(items) <= 1

    def test_empty_vault(self, tmp_path: pathlib.Path) -> None:
        items = content.get_timeline(str(tmp_path))
        assert items == []


class TestRetroDateFallbacks:
    def test_retro_with_bare_yaml_date(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        retro_dir = vault / "journal" / "summaries" / "retro" / "202x" / "2026" / "W20"
        retro_dir.mkdir(parents=True)
        (retro_dir / "2026-W20.md").write_text(
            "---\ntype: retro\nperiod_start: 2026-05-11\n---\n\n# Retro: W20\n\nContent."
        )
        items = content.get_retro_summaries(str(vault))
        assert len(items) == 1
        assert items[0]["date"] == datetime.date(2026, 5, 11)

    def test_retro_filename_fallback(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        retro_dir = vault / "journal" / "summaries" / "retro" / "202x" / "2026" / "W19"
        retro_dir.mkdir(parents=True)
        (retro_dir / "2026-W19.md").write_text("---\ntype: retro\n---\n\n# Retro: W19\n\nNo date.")
        items = content.get_retro_summaries(str(vault))
        assert len(items) == 1
        assert items[0]["date"] == datetime.date.fromisocalendar(2026, 19, 1)

    def test_weekly_filename_fallback(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        weekly_dir = vault / "journal" / "summaries" / "weekly" / "202x" / "2026" / "05"
        weekly_dir.mkdir(parents=True)
        (weekly_dir / "2026-W20.md").write_text("---\nperiod: weekly\n---\n\n# W20 Summary\n\nContent.")
        items = content._get_weekly_items(str(vault))
        assert len(items) == 1
        assert items[0]["date"] == datetime.date.fromisocalendar(2026, 20, 1)


class TestGetHierarchicalFeed:
    def test_returns_week_groups(self, vault: str) -> None:
        feed = content.get_hierarchical_feed(vault)
        assert isinstance(feed, list)
        for group in feed:
            assert "week" in group
            assert "period_start" in group
            assert "summary_label" in group

    def test_week_group_has_daily_entries(self, vault: str) -> None:
        feed = content.get_hierarchical_feed(vault)
        has_entries = any(len(g["daily_groups"]) > 0 for g in feed)
        assert has_entries

    def test_period_filter_week(self, vault: str) -> None:
        feed = content.get_hierarchical_feed(vault, period="week")
        assert len(feed) <= 4

    def test_period_filter_month(self, vault: str) -> None:
        feed = content.get_hierarchical_feed(vault, period="month")
        assert len(feed) <= 12

    def test_empty_vault(self, tmp_path: pathlib.Path) -> None:
        feed = content.get_hierarchical_feed(str(tmp_path))
        assert feed == []

    def test_metrics_in_summary_label(self, vault: str) -> None:
        feed = content.get_hierarchical_feed(vault)
        for group in feed:
            if group["metrics"]:
                assert "--" in group["summary_label"]


class TestRouteIntegration:
    @pytest.fixture()
    def app(self, vault: str) -> flask.Flask:
        import os

        os.environ["SHIP_VAULT_REPO"] = ""
        os.environ["SHIP_VAULT_PATH"] = vault
        os.environ["SHIP_OWNER_GITHUB_USER"] = "testowner"
        os.environ["SHIP_OWNERS"] = "testowner"
        os.environ["SHIP_MANAGERS"] = "testmanager"
        os.environ["SHIP_TEAMMATES"] = "testmate"

        test_app = ship.create_app()
        test_app.config["TESTING"] = True
        return test_app

    @pytest.fixture()
    def client(self, app: flask.Flask) -> flask.testing.FlaskClient:
        return app.test_client()

    def test_observation_deck_has_hierarchy(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/observation-deck", headers={"X-Auth-Request-Preferred-Username": "testmate"})
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "The view from above" in html
        assert "week-group" in html
        assert "Activity" in html

    def test_observation_deck_period_filter(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/observation-deck?period=month", headers={"X-Auth-Request-Preferred-Username": "testmate"})
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "period-btn active" in html

    def test_porthole_has_timeline_feed(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/porthole", headers={"X-Auth-Request-Preferred-Username": "testmanager"})
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "badge-retro" in html
        assert "A window into the work" in html

    def test_captains_log_renders(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/captains-log", headers={"X-Auth-Request-Preferred-Username": "testmate"})
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Captain's Log" in html
        assert "Reflections on the voyage" in html
        assert "retro-card" in html

    def test_captains_log_has_metrics_table(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/captains-log", headers={"X-Auth-Request-Preferred-Username": "testmate"})
        html = resp.data.decode()
        assert "metrics-table" in html

    def test_captains_log_has_cross_link(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/captains-log", headers={"X-Auth-Request-Preferred-Username": "testmate"})
        html = resp.data.decode()
        assert "observation-deck" in html

    def test_bridge_has_blurb(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/bridge", headers={"X-Auth-Request-Preferred-Username": "testowner"})
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Full operational control" in html

    def test_nav_has_captains_log(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/bridge", headers={"X-Auth-Request-Preferred-Username": "testowner"})
        html = resp.data.decode()
        assert "Captain&#39;s Log" in html or "Captain's Log" in html
