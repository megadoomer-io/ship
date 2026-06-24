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
    def test_returns_weekly_items_only(self, vault: str) -> None:
        items = content.get_timeline(vault)
        types = {item["content_type"] for item in items}
        assert "weekly" in types
        assert "retro" not in types

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


class TestGetWeeklyPlans:
    def test_returns_plan_items(self, vault: str) -> None:
        items = content.get_weekly_plans(vault)
        assert len(items) >= 1
        assert items[0]["content_type"] == "plan"

    def test_parses_frontmatter(self, vault: str) -> None:
        items = content.get_weekly_plans(vault)
        assert items[0]["metadata"].get("type") == "weekly-plan"
        assert items[0]["metadata"].get("items_triaged") is not None

    def test_limit(self, vault: str) -> None:
        items = content.get_weekly_plans(vault, limit=1)
        assert len(items) <= 1

    def test_empty_vault(self, tmp_path: pathlib.Path) -> None:
        items = content.get_weekly_plans(str(tmp_path))
        assert items == []

    def test_date_from_week_field(self, vault: str) -> None:
        items = content.get_weekly_plans(vault)
        assert items[0]["date"].year >= 2026


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


class TestPlanVersionMetadata:
    def _write_plan(self, vault: pathlib.Path, name: str, frontmatter: str) -> None:
        plans_dir = vault / "claude" / "plans" / "weekly"
        plans_dir.mkdir(parents=True, exist_ok=True)
        (plans_dir / name).write_text(f"---\n{frontmatter}\n---\n\n# Plan\n\nContent.")

    def test_plan_id_from_week_and_version(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        self._write_plan(vault, "2026-W26-v2.md", "type: weekly-plan\nweek: 2026-W26\nversion: 2")
        items = content.get_weekly_plans(str(vault))
        assert items[0]["metadata"]["plan_id"] == "2026-W26-v2"

    def test_plan_id_falls_back_to_stem(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        self._write_plan(vault, "2026-W26-v2.md", "type: weekly-plan")
        items = content.get_weekly_plans(str(vault))
        assert items[0]["metadata"]["plan_id"] == "2026-W26-v2"

    def test_superseded_by_passthrough(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        self._write_plan(
            vault,
            "2026-W26-v1.md",
            "type: weekly-plan\nweek: 2026-W26\nversion: 1\nsuperseded_by: 2026-W26-v2",
        )
        items = content.get_weekly_plans(str(vault))
        assert items[0]["metadata"]["superseded_by"] == "2026-W26-v2"

    def test_related_retro_passthrough(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        self._write_plan(
            vault,
            "2026-W26-v1.md",
            "type: weekly-plan\nweek: 2026-W26\nversion: 1\nrelated_retro: 2026-W26",
        )
        items = content.get_weekly_plans(str(vault))
        assert items[0]["metadata"]["related_retro"] == "2026-W26"


class TestRetroCrossLinkMetadata:
    def _write_retro(self, vault: pathlib.Path, name: str, frontmatter: str) -> None:
        retro_dir = vault / "journal" / "summaries" / "retro" / "202x" / "2026" / "W26"
        retro_dir.mkdir(parents=True, exist_ok=True)
        (retro_dir / name).write_text(f"---\n{frontmatter}\n---\n\n# Retro\n\nContent.")

    def test_period_derived_from_filename(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        self._write_retro(vault, "2026-W26.md", "type: retro\nperiod_start: 2026-06-22")
        items = content.get_retro_summaries(str(vault))
        assert items[0]["metadata"]["period"] == "2026-W26"

    def test_explicit_period_preserved(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        self._write_retro(vault, "2026-W26.md", "type: retro\nperiod: 2026-W25\nperiod_start: 2026-06-22")
        items = content.get_retro_summaries(str(vault))
        assert items[0]["metadata"]["period"] == "2026-W25"

    def test_related_plan_passthrough(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        self._write_retro(vault, "2026-W26.md", "type: retro\nperiod_start: 2026-06-22\nrelated_plan: 2026-W26-v2")
        items = content.get_retro_summaries(str(vault))
        assert items[0]["metadata"]["related_plan"] == "2026-W26-v2"

    def test_non_weekly_retro_gets_no_period(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        retro_dir = vault / "journal" / "summaries" / "retro" / "202x" / "2026" / "W26"
        retro_dir.mkdir(parents=True)
        (retro_dir / "cpe-1234-thing.md").write_text(
            "---\ntype: retro\nperiod_start: 2026-06-22\n---\n\n# Scoped\n\nx."
        )
        items = content.get_retro_summaries(str(vault))
        assert "period" not in items[0]["metadata"]


class TestGetCurrentPlan:
    def _plan(self, vault: pathlib.Path, name: str, fm: str) -> None:
        d = vault / "claude" / "plans" / "weekly"
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(f"---\n{fm}\n---\n\n# Plan\n\nx.")

    def test_returns_latest_nonsuperseded(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        self._plan(vault, "2026-W23-v1.md", "type: weekly-plan\nweek: 2026-W23\nversion: 1\nsuperseded_by: 2026-W23-v2")
        self._plan(vault, "2026-W23-v2.md", "type: weekly-plan\nweek: 2026-W23\nversion: 2")
        self._plan(vault, "2026-W24-v1.md", "type: weekly-plan\nweek: 2026-W24\nversion: 1")
        current = content.get_current_plan(str(vault))
        assert current is not None
        assert current["metadata"]["plan_id"] == "2026-W24-v1"

    def test_none_when_empty(self, tmp_path: pathlib.Path) -> None:
        assert content.get_current_plan(str(tmp_path)) is None


class TestGetCaptainsLog:
    def _build(self, vault: pathlib.Path) -> None:
        plans = vault / "claude" / "plans" / "weekly"
        plans.mkdir(parents=True, exist_ok=True)
        (plans / "2026-W23-v1.md").write_text("---\ntype: weekly-plan\nweek: 2026-W23\nversion: 1\n---\n\n# P\n\nx.")
        (plans / "2026-W24-v1.md").write_text("---\ntype: weekly-plan\nweek: 2026-W24\nversion: 1\n---\n\n# P\n\nx.")
        retro = vault / "journal" / "summaries" / "retro" / "202x" / "2026" / "W23"
        retro.mkdir(parents=True)
        (retro / "2026-W23.md").write_text(
            "---\ntype: retro\nperiod_start: 2026-06-01\nperiod: 2026-W23\n---\n\n# R\n\nx."
        )

    def test_excludes_current_plan(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        self._build(vault)
        log = content.get_captains_log(str(vault))
        plan_ids = [it["metadata"].get("plan_id") for it in log if it["content_type"] == "plan"]
        assert "2026-W24-v1" not in plan_ids  # current plan lives on Course
        assert "2026-W23-v1" in plan_ids  # past plan in the log

    def test_interleaves_plans_and_retros(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        self._build(vault)
        log = content.get_captains_log(str(vault))
        types = {it["content_type"] for it in log}
        assert types == {"plan", "retro"}

    def test_retro_sorts_above_its_plan(self, tmp_path: pathlib.Path) -> None:
        vault = tmp_path / "vault"
        self._build(vault)
        kinds = [it["content_type"] for it in content.get_captains_log(str(vault))]
        # W23 retro and W23-v1 share the week's Monday; the retro is the later event.
        assert kinds.index("retro") < kinds.index("plan")


class TestPlanRetroCrossLinkRendering:
    """New model: Course shows only the current plan; the Captain's Log
    interleaves past plans + retros with cross-links and superseded dimming."""

    _G = "megadoomer-io:megadoomer-ship"
    CREW_H = {"X-Auth-Request-User": "u", "X-Auth-Request-Groups": f"{_G}-crew,{_G}"}

    @pytest.fixture()
    def app(self, tmp_path: pathlib.Path) -> flask.Flask:
        import os

        vault = tmp_path / "vault"
        plans = vault / "claude" / "plans" / "weekly"
        plans.mkdir(parents=True)
        # Current week (latest): not retrospected -> stays on Course, no retro link.
        (plans / "2026-W24-v1.md").write_text(
            "---\ntype: weekly-plan\nweek: 2026-W24\nversion: 1\n---\n\n"
            "# Weekly Plan: 2026-W24 (v1)\n\n## Commitments\n- [ ] current\n"
        )
        # Past week: v1 superseded, v2 final + retrospected -> both in the Log.
        (plans / "2026-W23-v1.md").write_text(
            "---\ntype: weekly-plan\nweek: 2026-W23\nversion: 1\n"
            "superseded_by: 2026-W23-v2\n---\n\n"
            "# Weekly Plan: 2026-W23 (v1)\n\n## Commitments\n- [ ] old\n"
        )
        (plans / "2026-W23-v2.md").write_text(
            "---\ntype: weekly-plan\nweek: 2026-W23\nversion: 2\nrelated_retro: 2026-W23\n---\n\n"
            "# Weekly Plan: 2026-W23 (v2)\n\n## Commitments\n- [ ] final\n"
        )
        retro = vault / "journal" / "summaries" / "retro" / "202x" / "2026" / "W23"
        retro.mkdir(parents=True)
        (retro / "2026-W23.md").write_text(
            "---\ntype: retro\nperiod_start: 2026-06-01\nperiod: 2026-W23\n"
            "related_plan: 2026-W23-v2\n---\n\n# Retro: W23\n\n## Shipped\n- thing\n"
        )

        os.environ["SHIP_VAULT_REPO"] = ""
        os.environ["SHIP_VAULT_PATH"] = str(vault)

        test_app = ship.create_app()
        test_app.config["TESTING"] = True
        return test_app

    @pytest.fixture()
    def client(self, app: flask.Flask) -> flask.testing.FlaskClient:
        return app.test_client()

    def test_course_shows_only_current_plan(self, client: flask.testing.FlaskClient) -> None:
        html = client.get("/course", headers=self.CREW_H).data.decode()
        assert 'id="2026-W24-v1"' in html  # the current plan
        assert "2026-W23-v1" not in html  # past plans are not on Course
        assert "2026-W23-v2" not in html
        assert "entry-card superseded" not in html  # nothing dimmed on Course

    def test_course_current_plan_has_no_retro_link(self, client: flask.testing.FlaskClient) -> None:
        html = client.get("/course", headers=self.CREW_H).data.decode()
        assert "See the retro" not in html  # W24 not retrospected yet

    def test_log_dims_superseded_past_plan(self, client: flask.testing.FlaskClient) -> None:
        html = client.get("/captains-log", headers=self.CREW_H).data.decode()
        assert 'id="2026-W23-v1"' in html
        assert "entry-card superseded" in html
        assert "badge-superseded" in html

    def test_log_excludes_current_plan(self, client: flask.testing.FlaskClient) -> None:
        html = client.get("/captains-log", headers=self.CREW_H).data.decode()
        assert "2026-W24-v1" not in html  # current plan stays on Course

    def test_log_cross_links(self, client: flask.testing.FlaskClient) -> None:
        html = client.get("/captains-log", headers=self.CREW_H).data.decode()
        # retrospected past plan -> its retro (intra-log anchor)
        assert "See the retro" in html
        assert 'href="#2026-W23"' in html
        # retro -> its plan (intra-log anchor) + activity link out to obs deck
        assert "See the plan" in html
        assert 'href="#2026-W23-v2"' in html
        assert "See all activity" in html
        assert "observation-deck" in html


class TestLogAutoExpandSkipsSuperseded:
    """The Captain's Log must not auto-expand a superseded plan, even when it is
    the most recent log item. The first non-superseded item opens instead."""

    _G = "megadoomer-io:megadoomer-ship"
    CREW_H = {"X-Auth-Request-User": "u", "X-Auth-Request-Groups": f"{_G}-crew,{_G}"}

    @pytest.fixture()
    def app(self, tmp_path: pathlib.Path) -> flask.Flask:
        import os

        vault = tmp_path / "vault"
        plans = vault / "claude" / "plans" / "weekly"
        plans.mkdir(parents=True)
        # W26: v2 is current (Course); v1 is superseded and the most recent LOG item.
        (plans / "2026-W26-v2.md").write_text(
            "---\ntype: weekly-plan\nweek: 2026-W26\nversion: 2\n---\n\n# W26 (v2)\n\n- [ ] now\n"
        )
        (plans / "2026-W26-v1.md").write_text(
            "---\ntype: weekly-plan\nweek: 2026-W26\nversion: 1\nsuperseded_by: 2026-W26-v2\n---\n\n"
            "# W26 (v1)\n\n- [ ] old\n"
        )
        # Older week W25 with a retro -> the first non-superseded log item.
        (plans / "2026-W25-v1.md").write_text(
            "---\ntype: weekly-plan\nweek: 2026-W25\nversion: 1\nrelated_retro: 2026-W25\n---\n\n# W25\n\n- [ ] done\n"
        )
        retro = vault / "journal" / "summaries" / "retro" / "202x" / "2026" / "W25"
        retro.mkdir(parents=True)
        (retro / "2026-W25.md").write_text(
            "---\ntype: retro\nperiod_start: 2026-06-15\nperiod: 2026-W25\n"
            "related_plan: 2026-W25-v1\n---\n\n# Retro: W25\n\n- thing\n"
        )
        os.environ["SHIP_VAULT_REPO"] = ""
        os.environ["SHIP_VAULT_PATH"] = str(vault)
        test_app = ship.create_app()
        test_app.config["TESTING"] = True
        return test_app

    @pytest.fixture()
    def client(self, app: flask.Flask) -> flask.testing.FlaskClient:
        return app.test_client()

    def test_superseded_plan_not_auto_expanded(self, client: flask.testing.FlaskClient) -> None:
        html = client.get("/captains-log", headers=self.CREW_H).data.decode()
        assert 'class="card entry-card superseded">' in html
        assert 'class="card entry-card superseded" open>' not in html

    def test_first_nonsuperseded_item_expanded(self, client: flask.testing.FlaskClient) -> None:
        html = client.get("/captains-log", headers=self.CREW_H).data.decode()
        assert 'id="2026-W25" class="card entry-card" open>' in html


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
    _G = "megadoomer-io:megadoomer-ship"
    CAPTAIN_H = {"X-Auth-Request-User": "u", "X-Auth-Request-Groups": f"{_G}-captain,{_G}"}
    OFFICERS_H = {"X-Auth-Request-User": "u", "X-Auth-Request-Groups": f"{_G}-officers,{_G}"}
    CREW_H = {"X-Auth-Request-User": "u", "X-Auth-Request-Groups": f"{_G}-crew,{_G}"}

    @pytest.fixture()
    def app(self, vault: str) -> flask.Flask:
        import os

        os.environ["SHIP_VAULT_REPO"] = ""
        os.environ["SHIP_VAULT_PATH"] = vault

        test_app = ship.create_app()
        test_app.config["TESTING"] = True
        return test_app

    @pytest.fixture()
    def client(self, app: flask.Flask) -> flask.testing.FlaskClient:
        return app.test_client()

    def test_observation_deck_has_hierarchy(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/observation-deck", headers=self.OFFICERS_H)
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "The view from above" in html
        assert "section-collapse section-h2" in html
        assert "Activity" in html

    def test_observation_deck_period_filter(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/observation-deck?period=month", headers=self.OFFICERS_H)
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "period-btn active" in html

    def test_porthole_has_timeline_feed(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/porthole", headers=self.CREW_H)
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "badge-weekly" in html
        assert "badge-retro" not in html
        assert "A window into the work" in html

    def test_captains_log_renders(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/captains-log", headers=self.CREW_H)
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Captain's Log" in html
        assert "The voyage record" in html
        assert "entry-card" in html

    def test_captains_log_has_metrics_table(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/captains-log", headers=self.CREW_H)
        html = resp.data.decode()
        assert "metrics-table" in html

    def test_captains_log_has_cross_link(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/captains-log", headers=self.CREW_H)
        html = resp.data.decode()
        assert "observation-deck" in html

    def test_bridge_has_blurb(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/bridge", headers=self.CAPTAIN_H)
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Full operational control" in html

    def test_nav_has_captains_log(self, client: flask.testing.FlaskClient) -> None:
        resp = client.get("/bridge", headers=self.CAPTAIN_H)
        html = resp.data.decode()
        assert "Captain&#39;s Log" in html or "Captain's Log" in html


class TestPagination:
    def test_timeline_offset_zero_matches_default(self, vault: str) -> None:
        default = content.get_timeline(vault, limit=20)
        with_offset = content.get_timeline(vault, limit=20, offset=0)
        assert len(default) == len(with_offset)
        for a, b in zip(default, with_offset, strict=True):
            assert a["title"] == b["title"]

    def test_timeline_offset_skips_items(self, vault: str) -> None:
        all_items = content.get_timeline(vault, limit=20)
        if len(all_items) < 2:
            return
        offset_items = content.get_timeline(vault, limit=20, offset=1)
        assert offset_items[0]["title"] == all_items[1]["title"]

    def test_timeline_offset_beyond_end_returns_empty(self, vault: str) -> None:
        items = content.get_timeline(vault, limit=20, offset=1000)
        assert items == []

    def test_retro_offset(self, vault: str) -> None:
        all_items = content.get_retro_summaries(vault, limit=20)
        offset_items = content.get_retro_summaries(vault, limit=20, offset=len(all_items))
        assert offset_items == []

    def test_hierarchical_feed_no_limit_preserves_behavior(self, vault: str) -> None:
        default = content.get_hierarchical_feed(vault, period="week")
        explicit = content.get_hierarchical_feed(vault, period="week", limit=None)
        assert len(default) == len(explicit)

    def test_hierarchical_feed_explicit_limit(self, vault: str) -> None:
        result = content.get_hierarchical_feed(vault, period="all", offset=0, limit=1)
        assert len(result) <= 1
