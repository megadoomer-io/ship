import logging
import pathlib
import subprocess

import flask
from apscheduler.schedulers.background import BackgroundScheduler

log = logging.getLogger(__name__)


def clone_or_pull(repo_url: str, local_path: str) -> None:
    path = pathlib.Path(local_path)
    if (path / ".git").exists():
        subprocess.run(
            ["git", "fetch", "--depth", "1", "origin", "main"],
            cwd=path,
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["git", "reset", "--hard", "origin/main"],
            cwd=path,
            capture_output=True,
            check=False,
        )
        log.info("Pulled latest vault content to %s", local_path)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(path)],
            capture_output=True,
        )
        if result.returncode != 0:
            log.error("Failed to clone vault: %s", result.stderr.decode())
            return
        log.info("Cloned vault to %s", local_path)


def start_sync(app: flask.Flask) -> None:
    repo_url = app.config["VAULT_REPO"]
    local_path = app.config["VAULT_PATH"]
    interval = app.config["PULL_INTERVAL_SECONDS"]

    if not repo_url:
        log.warning("SHIP_VAULT_REPO not set, vault sync disabled")
        return

    clone_or_pull(repo_url, local_path)

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        clone_or_pull,
        "interval",
        seconds=interval,
        args=[repo_url, local_path],
    )
    scheduler.start()
    app.extensions["vault_scheduler"] = scheduler
