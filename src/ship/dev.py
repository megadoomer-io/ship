import pathlib
import shutil
from datetime import date, timedelta

FIXTURES_DIR = pathlib.Path(__file__).parent.parent.parent / "tests" / "fixtures"


def create_mock_vault(target_path: str) -> None:
    vault = pathlib.Path(target_path)
    today = date.today()
    last_week = today - timedelta(weeks=1)

    def _week_parts(d: date) -> tuple[str, str, str, str]:
        iso = d.isocalendar()
        year = str(iso.year)
        decade = f"{year[:3]}x"
        month = f"{d.month:02d}"
        week = f"W{iso.week:02d}"
        return decade, year, month, week

    active_work_dir = vault / "claude" / "active-work"
    active_work_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_DIR / "active-work-index.md", active_work_dir / "INDEX.md")

    # Weekly plans (2 weeks)
    plans_dir = vault / "claude" / "plans" / "weekly"
    plans_dir.mkdir(parents=True, exist_ok=True)
    dec, yr, _, wk = _week_parts(today)
    shutil.copy(FIXTURES_DIR / "weekly-plan.md", plans_dir / f"{yr}-{wk}-v1.md")
    dec2, yr2, _, wk2 = _week_parts(last_week)
    shutil.copy(FIXTURES_DIR / "weekly-plan-2.md", plans_dir / f"{yr2}-{wk2}-v1.md")

    # Weekly summaries (2 weeks)
    dec, yr, mo, wk = _week_parts(today)
    summary_dir = vault / "journal" / "summaries" / "weekly" / dec / yr / mo
    summary_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_DIR / "weekly-summary.md", summary_dir / f"{yr}-{wk}.md")

    dec2, yr2, mo2, wk2 = _week_parts(last_week)
    summary_dir2 = vault / "journal" / "summaries" / "weekly" / dec2 / yr2 / mo2
    summary_dir2.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_DIR / "weekly-summary-2.md", summary_dir2 / f"{yr2}-{wk2}.md")

    # Retro summaries (2 weeks)
    retro_dir = vault / "journal" / "summaries" / "retro" / dec / yr / wk
    retro_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_DIR / "retro-summary.md", retro_dir / f"{yr}-{wk}.md")

    retro_dir2 = vault / "journal" / "summaries" / "retro" / dec2 / yr2 / wk2
    retro_dir2.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_DIR / "retro-summary-2.md", retro_dir2 / f"{yr2}-{wk2}.md")

    # Journal entries: today (2 entries)
    day_iso = today.isoformat()
    entries_dir = vault / "journal" / "entries" / dec / yr / mo / wk / day_iso
    entries_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_DIR / "daily-entry-1.md", entries_dir / "09-15-ci-fix.md")
    shutil.copy(FIXTURES_DIR / "daily-entry-2.md", entries_dir / "12-30-pre-commit.md")

    # Journal entries: yesterday (1 entry)
    yesterday = today - timedelta(days=1)
    yd_dec, yd_yr, yd_mo, yd_wk = _week_parts(yesterday)
    yd_dir = vault / "journal" / "entries" / yd_dec / yd_yr / yd_mo / yd_wk / yesterday.isoformat()
    yd_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_DIR / "daily-entry-3.md", yd_dir / "14-00-cert-manager.md")

    # Journal entries: last week (2 entries on one day, 1 on another)
    lw_day1 = last_week
    lw_day2 = last_week + timedelta(days=2)
    lw_dec, lw_yr, lw_mo, lw_wk = _week_parts(lw_day1)

    lw_dir1 = vault / "journal" / "entries" / lw_dec / lw_yr / lw_mo / lw_wk / lw_day1.isoformat()
    lw_dir1.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_DIR / "daily-entry-3.md", lw_dir1 / "14-00-cert-manager.md")
    shutil.copy(FIXTURES_DIR / "daily-entry-4.md", lw_dir1 / "10-00-kdrift-release.md")

    lw_dir2 = vault / "journal" / "entries" / lw_dec / lw_yr / lw_mo / lw_wk / lw_day2.isoformat()
    lw_dir2.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_DIR / "daily-entry-1.md", lw_dir2 / "09-15-ci-fix.md")
