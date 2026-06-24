import contextlib
import datetime
import logging
import pathlib
import re
import typing

import yaml

from ship import markdown

logger = logging.getLogger(__name__)

_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_WEEK_RE = re.compile(r"(\d{4})-W(\d{2})")


class TimelineItem(typing.TypedDict):
    date: datetime.date
    content_type: str
    title: str
    rendered_html: str
    metadata: dict[str, object]


class DailyGroup(typing.TypedDict):
    date: datetime.date
    date_label: str
    entries: list[str]


class WeekGroup(typing.TypedDict):
    week: str
    period_start: datetime.date
    period_end: datetime.date
    summary_label: str
    metrics: dict[str, object]
    weekly_summary_html: str | None
    daily_groups: list[DailyGroup]


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return {}, text

    end = stripped.find("\n---", 3)
    if end == -1:
        return {}, text

    yaml_block = stripped[3:end].strip()
    body = stripped[end + 4 :].lstrip("\n")

    try:
        parsed = yaml.safe_load(yaml_block)
    except yaml.YAMLError:
        logger.warning("Malformed YAML frontmatter, skipping")
        return {}, text

    if not isinstance(parsed, dict):
        return {}, text

    return parsed, body


def _extract_title(body: str) -> str:
    match = _H1_RE.search(body)
    if match:
        return match.group(1).strip()
    return "Untitled"


def _parse_date_field(value: object) -> datetime.date | None:
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _week_from_date(d: datetime.date) -> str:
    iso = d.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _week_date_range(year: int, week: int) -> tuple[datetime.date, datetime.date]:
    start = datetime.date.fromisocalendar(year, week, 1)
    end = datetime.date.fromisocalendar(year, week, 7)
    return start, end


def get_active_work(vault_path: str) -> str:
    index = pathlib.Path(vault_path) / "claude" / "active-work" / "INDEX.md"
    if index.exists():
        return markdown.render(index.read_text())
    return "<p>No active work index found.</p>"


def get_weekly_summary(vault_path: str) -> str | None:
    summaries_dir = pathlib.Path(vault_path) / "journal" / "summaries" / "weekly"
    if not summaries_dir.exists():
        return None

    files = sorted(summaries_dir.rglob("*.md"), reverse=True)
    if files:
        return markdown.render(files[0].read_text())
    return None


def get_daily_entries(vault_path: str) -> list[str]:
    today = datetime.date.today().isoformat()
    entries_dir = pathlib.Path(vault_path) / "journal" / "entries"
    if not entries_dir.exists():
        return []

    today_dirs = list(entries_dir.rglob(today))
    entries: list[str] = []
    for d in today_dirs:
        if d.is_dir():
            for f in sorted(d.glob("*.md")):
                entries.append(markdown.render(f.read_text()))
    return entries


def _get_weekly_items(vault_path: str, limit: int = 4, offset: int = 0) -> list[TimelineItem]:
    summaries_dir = pathlib.Path(vault_path) / "journal" / "summaries" / "weekly"
    if not summaries_dir.exists():
        return []

    fetch_limit = limit + offset
    items: list[TimelineItem] = []
    for f in sorted(summaries_dir.rglob("*.md"), reverse=True):
        if len(items) >= fetch_limit:
            break
        try:
            text = f.read_text()
        except OSError:
            logger.warning("Could not read %s", f)
            continue

        meta, body = parse_frontmatter(text)
        title = _extract_title(body)

        item_date: datetime.date | None = None
        period_start = meta.get("period_start")
        if period_start is not None:
            item_date = _parse_date_field(period_start)

        if item_date is None:
            week_str = meta.get("week", "")
            year_val = meta.get("year")
            if isinstance(week_str, str) and week_str.startswith("W") and isinstance(year_val, int):
                with contextlib.suppress(ValueError):
                    item_date = datetime.date.fromisocalendar(year_val, int(week_str[1:]), 1)

        if item_date is None:
            stem = f.stem
            match = _WEEK_RE.match(stem)
            if match:
                with contextlib.suppress(ValueError):
                    item_date = datetime.date.fromisocalendar(int(match.group(1)), int(match.group(2)), 1)

        if item_date is None:
            item_date = datetime.date.today()

        items.append(
            TimelineItem(
                date=item_date,
                content_type="weekly",
                title=title,
                rendered_html=markdown.render(body),
                metadata=meta,
            )
        )

    return items[offset:]


def get_retro_summaries(vault_path: str, limit: int = 4, offset: int = 0) -> list[TimelineItem]:
    retro_dir = pathlib.Path(vault_path) / "journal" / "summaries" / "retro"
    if not retro_dir.exists():
        return []

    fetch_limit = limit + offset
    items: list[TimelineItem] = []
    for f in sorted(retro_dir.rglob("*.md"), reverse=True):
        if len(items) >= fetch_limit:
            break
        try:
            text = f.read_text()
        except OSError:
            logger.warning("Could not read %s", f)
            continue

        meta, body = parse_frontmatter(text)
        title = _extract_title(body)

        item_date: datetime.date | None = None
        period_start = meta.get("period_start")
        if period_start is not None:
            item_date = _parse_date_field(period_start)

        if item_date is None:
            stem = f.stem
            match = _WEEK_RE.match(stem)
            if match:
                with contextlib.suppress(ValueError):
                    item_date = datetime.date.fromisocalendar(int(match.group(1)), int(match.group(2)), 1)

        if item_date is None:
            item_date = datetime.date.today()

        # Derive the week-stamp anchor for weekly retros (YYYY-Www.md). This is
        # the target for plan->retro links and the existing obs-deck link, which
        # was dormant because retros don't carry a `period` field in frontmatter.
        if "period" not in meta:
            stem_match = _WEEK_RE.match(f.stem)
            if stem_match:
                meta["period"] = f"{stem_match.group(1)}-W{stem_match.group(2)}"

        items.append(
            TimelineItem(
                date=item_date,
                content_type="retro",
                title=title,
                rendered_html=markdown.render(body),
                metadata=meta,
            )
        )

    return items[offset:]


_PLAN_WEEK_RE = re.compile(r"(\d{4})-W(\d{2})")


def get_weekly_plans(vault_path: str, limit: int = 10, offset: int = 0) -> list[TimelineItem]:
    plans_dir = pathlib.Path(vault_path) / "claude" / "plans" / "weekly"
    if not plans_dir.exists():
        return []

    fetch_limit = limit + offset
    items: list[TimelineItem] = []
    for f in sorted(plans_dir.rglob("*.md"), reverse=True):
        if len(items) >= fetch_limit:
            break
        try:
            text = f.read_text()
        except OSError:
            logger.warning("Could not read %s", f)
            continue

        meta, body = parse_frontmatter(text)
        title = _extract_title(body)

        item_date: datetime.date | None = None
        week_field = meta.get("week")
        if isinstance(week_field, str):
            match = _PLAN_WEEK_RE.match(week_field)
            if match:
                with contextlib.suppress(ValueError):
                    item_date = datetime.date.fromisocalendar(int(match.group(1)), int(match.group(2)), 1)

        if item_date is None:
            match = _PLAN_WEEK_RE.search(f.stem)
            if match:
                with contextlib.suppress(ValueError):
                    item_date = datetime.date.fromisocalendar(int(match.group(1)), int(match.group(2)), 1)

        if item_date is None:
            item_date = datetime.date.today()

        # Stable anchor id for this plan version (YYYY-Www-vN). Retro frontmatter's
        # `related_plan` points at this; the filename stem already matches when
        # week/version aren't both present in frontmatter.
        if "plan_id" not in meta:
            week_val = meta.get("week")
            version_val = meta.get("version")
            if isinstance(week_val, str) and version_val is not None:
                meta["plan_id"] = f"{week_val}-v{version_val}"
            else:
                meta["plan_id"] = f.stem

        items.append(
            TimelineItem(
                date=item_date,
                content_type="plan",
                title=title,
                rendered_html=markdown.render(body),
                metadata=meta,
            )
        )

    return items[offset:]


def get_timeline(vault_path: str, limit: int = 20, offset: int = 0) -> list[TimelineItem]:
    fetch_limit = limit + offset
    items: list[TimelineItem] = []
    items.extend(_get_weekly_items(vault_path, limit=fetch_limit))
    items.sort(key=lambda item: item["date"], reverse=True)
    return items[offset : offset + limit]


def _collect_daily_entries_for_date(entries_dir: pathlib.Path, target_date: str) -> list[str]:
    entries: list[str] = []
    for d in entries_dir.rglob(target_date):
        if d.is_dir():
            for f in sorted(d.glob("*.md")):
                try:
                    entries.append(markdown.render(f.read_text()))
                except OSError:
                    logger.warning("Could not read %s", f)
    return entries


def get_hierarchical_feed(
    vault_path: str,
    period: str = "week",
    offset: int = 0,
    limit: int | None = None,
) -> list[WeekGroup]:
    vault = pathlib.Path(vault_path)
    entries_dir = vault / "journal" / "entries"
    summaries_dir = vault / "journal" / "summaries" / "weekly"

    weeks_to_show = {"week": 4, "month": 12, "all": 52}.get(period, 4)
    if limit is not None:
        weeks_to_show = max(weeks_to_show, offset + limit)

    today = datetime.date.today()

    week_groups: list[WeekGroup] = []

    for week_offset in range(weeks_to_show):
        target = today - datetime.timedelta(weeks=week_offset)
        iso = target.isocalendar()
        week_label = f"{iso.year}-W{iso.week:02d}"

        with contextlib.suppress(ValueError):
            period_start, period_end = _week_date_range(iso.year, iso.week)

            summary_html: str | None = None
            metrics: dict[str, object] = {}

            for sf in summaries_dir.rglob("*.md") if summaries_dir.exists() else []:
                match = _WEEK_RE.match(sf.stem)
                if match and int(match.group(1)) == iso.year and int(match.group(2)) == iso.week:
                    try:
                        meta, body = parse_frontmatter(sf.read_text())
                        summary_html = markdown.render(body)
                        raw_metrics = meta.get("metrics")
                        if isinstance(raw_metrics, dict):
                            metrics = raw_metrics
                    except OSError:
                        logger.warning("Could not read %s", sf)
                    break

            daily_groups: list[DailyGroup] = []
            if entries_dir.exists():
                for day_offset in range(7):
                    day = period_start + datetime.timedelta(days=6 - day_offset)
                    day_entries = _collect_daily_entries_for_date(entries_dir, day.isoformat())
                    if day_entries:
                        daily_groups.append(
                            DailyGroup(
                                date=day,
                                date_label=day.strftime("%A, %b %d"),
                                entries=day_entries,
                            )
                        )

            if not summary_html and not daily_groups:
                continue

            metrics_parts: list[str] = []
            commits = metrics.get("commits")
            prs = metrics.get("prs_authored")
            if isinstance(commits, int):
                metrics_parts.append(f"{commits} commits")
            if isinstance(prs, int):
                metrics_parts.append(f"{prs} PRs")
            metrics_suffix = f" -- {', '.join(metrics_parts)}" if metrics_parts else ""
            date_range = f"{period_start.strftime('%b %d')}-{period_end.strftime('%b %d')}"
            summary_label = f"W{iso.week:02d} ({date_range}){metrics_suffix}"

            week_groups.append(
                WeekGroup(
                    week=week_label,
                    period_start=period_start,
                    period_end=period_end,
                    summary_label=summary_label,
                    metrics=metrics,
                    weekly_summary_html=summary_html,
                    daily_groups=daily_groups,
                )
            )

    if limit is not None:
        return week_groups[offset : offset + limit]
    return week_groups
