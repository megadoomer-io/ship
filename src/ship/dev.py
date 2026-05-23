import pathlib
import shutil
from datetime import date

FIXTURES_DIR = pathlib.Path(__file__).parent.parent.parent / "tests" / "fixtures"


def create_mock_vault(target_path: str) -> None:
    vault = pathlib.Path(target_path)
    today = date.today()
    year = str(today.year)
    month = f"{today.month:02d}"
    week = today.strftime("W%V")
    decade = f"{year[:3]}x"
    day_iso = today.isoformat()

    active_work_dir = vault / "claude" / "active-work"
    active_work_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_DIR / "active-work-index.md", active_work_dir / "INDEX.md")

    summary_dir = vault / "journal" / "summaries" / "weekly" / decade / year / month
    summary_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_DIR / "weekly-summary.md", summary_dir / f"{year}-{week}.md")

    entries_dir = vault / "journal" / "entries" / decade / year / month / week / day_iso
    entries_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_DIR / "daily-entry-1.md", entries_dir / "09-15-ci-fix.md")
    shutil.copy(FIXTURES_DIR / "daily-entry-2.md", entries_dir / "12-30-pre-commit.md")
