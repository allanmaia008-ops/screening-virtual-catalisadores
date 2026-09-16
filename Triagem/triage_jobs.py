"""Fila local e estado persistido em arquivos para execuções CatAiLab."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


ACTIVE_STATES = {"queued", "running"}
FINAL_STATES = {"completed", "failed"}
STATUS_FILE = "status.json"
CONFIG_FILE = "configuracao.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{uuid4().hex}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path, default: dict | None = None) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, TypeError):
        return dict(default or {})


def read_status(job_dir: Path | str | None) -> dict:
    if not job_dir:
        return {}
    return read_json(Path(job_dir) / STATUS_FILE)


def create_job(base_dir: Path, configuration: dict) -> Path:
    created = datetime.now(timezone.utc)
    job_dir = base_dir / f"execucao_{created:%Y%m%d_%H%M%S}_{uuid4().hex}"
    job_dir.mkdir(parents=True, exist_ok=False)
    config = {**configuration, "created_at": created.isoformat(), "job_dir": str(job_dir.resolve())}
    write_json_atomic(job_dir / CONFIG_FILE, config)
    write_json_atomic(job_dir / STATUS_FILE, {
        "state": "queued", "stage": "Aguardando a execução anterior terminar",
        "progress": 0, "created_at": created.isoformat(), "updated_at": _now_iso(),
    })
    return job_dir


def start_worker(job_dir: Path, app_dir: Path, environment: dict[str, str] | None = None) -> int:
    command = [sys.executable, str(app_dir / "triage_worker.py"), str(job_dir.resolve())]
    kwargs: dict = {
        "cwd": str(app_dir), "env": environment or os.environ.copy(),
        "stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL,
        "close_fds": os.name != "nt",
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
    process = subprocess.Popen(command, **kwargs)
    return int(process.pid)


def queue_position(job_dir: Path, base_dir: Path) -> int:
    queued = []
    for candidate in base_dir.glob("execucao_*"):
        status = read_status(candidate)
        if status.get("state") == "queued":
            queued.append((status.get("created_at", ""), candidate.resolve()))
    queued.sort(key=lambda item: (item[0], str(item[1])))
    target = job_dir.resolve()
    return next((index for index, (_, path) in enumerate(queued, 1) if path == target), 0)


def cleanup_old_jobs(base_dir: Path, max_age_hours: int = 24, protected: set[Path] | None = None) -> int:
    """Remove somente pastas de execução finalizadas e antigas."""
    protected_resolved = {path.resolve() for path in (protected or set())}
    cutoff = time.time() - max_age_hours * 3600
    removed = 0
    for job_dir in base_dir.glob("execucao_*"):
        try:
            if job_dir.resolve() in protected_resolved or not job_dir.is_dir():
                continue
            status = read_status(job_dir)
            if status.get("state") in ACTIVE_STATES:
                continue
            newest = max((path.stat().st_mtime for path in job_dir.rglob("*") if path.is_file()), default=job_dir.stat().st_mtime)
            if newest >= cutoff:
                continue
            for path in sorted(job_dir.rglob("*"), key=lambda item: len(item.parts), reverse=True):
                if path.is_file() or path.is_symlink():
                    path.unlink(missing_ok=True)
                elif path.is_dir():
                    path.rmdir()
            job_dir.rmdir()
            removed += 1
        except OSError:
            continue
    return removed

