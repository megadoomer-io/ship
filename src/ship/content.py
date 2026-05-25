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


class TimelineItem(typing.TypedDict):
    date: datetime.date
    content_type: str
    title: str
    rendered_html: str
    metadata: dict[str, object]


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


def _get_weekly_items(vault_path: str, limit: int = 4) -> list[TimelineItem]:
    summaries_dir = pathlib.Path(vault_path) / "journal" / "summaries" / "weekly"
    if not summaries_dir.exists():
        return []

    items: list[TimelineItem] = []
    for f in sorted(summaries_dir.rglob("*.md"), reverse=True):
        if len(items) >= limit:
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
            match = re.match(r"(\d{4})-W(\d{2})", stem)
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

    return items


def get_retro_summaries(vault_path: str, limit: int = 4) -> list[TimelineItem]:
    retro_dir = pathlib.Path(vault_path) / "journal" / "summaries" / "retro"
    if not retro_dir.exists():
        return []

    items: list[TimelineItem] = []
    for f in sorted(retro_dir.rglob("*.md"), reverse=True):
        if len(items) >= limit:
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
            match = re.match(r"(\d{4})-W(\d{2})", stem)
            if match:
                with contextlib.suppress(ValueError):
                    item_date = datetime.date.fromisocalendar(int(match.group(1)), int(match.group(2)), 1)

        if item_date is None:
            item_date = datetime.date.today()

        items.append(
            TimelineItem(
                date=item_date,
                content_type="retro",
                title=title,
                rendered_html=markdown.render(body),
                metadata=meta,
            )
        )

    return items


def get_timeline(vault_path: str, limit: int = 20) -> list[TimelineItem]:
    items: list[TimelineItem] = []
    items.extend(get_retro_summaries(vault_path, limit=limit))
    items.extend(_get_weekly_items(vault_path, limit=limit))
    items.sort(key=lambda item: item["date"], reverse=True)
    return items[:limit]
