import pathlib
from datetime import date


def get_active_work(vault_path: str) -> str:
    index = pathlib.Path(vault_path) / "claude" / "active-work" / "INDEX.md"
    if index.exists():
        return index.read_text()
    return "No active work index found."


def get_weekly_summary(vault_path: str) -> str | None:
    summaries_dir = pathlib.Path(vault_path) / "journal" / "summaries" / "weekly"
    if not summaries_dir.exists():
        return None

    files = sorted(summaries_dir.rglob("*.md"), reverse=True)
    if files:
        return files[0].read_text()
    return None


def get_daily_entries(vault_path: str) -> list[str]:
    today = date.today().isoformat()
    entries_dir = pathlib.Path(vault_path) / "journal" / "entries"
    if not entries_dir.exists():
        return []

    today_dirs = list(entries_dir.rglob(today))
    entries: list[str] = []
    for d in today_dirs:
        if d.is_dir():
            for f in sorted(d.glob("*.md")):
                entries.append(f.read_text())
    return entries
