"""Background execution of research jobs.

A small in-process queue with daemon worker threads: no Redis/Celery needed, works on
Windows, and Ctrl+C stops the server immediately. Limits: jobs waiting in the queue are
lost when the server restarts (they are marked failed by ResearchJob.expire_if_stale),
and it only scales to one server process. If you outgrow that, replace submit() with a
Celery task that calls _run(job_id).
"""

import logging
import os
import queue
import threading
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.utils import timezone

from .agent import AgentConfigError, check_setup, run_agent
from .exporter import clean, save_answer
from .models import ResearchJob

logger = logging.getLogger(__name__)

_queue: "queue.Queue[int]" = queue.Queue()
_workers_started = False
_lock = threading.Lock()


def _worker():
    while True:
        job_id = _queue.get()
        try:
            _run(job_id)
        except Exception:  # noqa: BLE001
            logger.exception("Unexpected error in job %s", job_id)
        finally:
            connection.close()
            _queue.task_done()


def _ensure_workers():
    global _workers_started
    with _lock:
        if _workers_started:
            return
        for i in range(max(1, settings.RESEARCH_WORKERS)):
            threading.Thread(target=_worker, name=f"research-worker-{i}", daemon=True).start()
        _workers_started = True


def submit(job_id: int) -> None:
    _ensure_workers()
    _queue.put(job_id)


def _finish(job_id, **fields):
    ResearchJob.objects.filter(pk=job_id).update(finished_at=timezone.now(), **fields)


def _run(job_id: int) -> None:
    job = ResearchJob.objects.filter(pk=job_id).first()
    if job is None or job.status != ResearchJob.Status.PENDING:
        return
    ResearchJob.objects.filter(pk=job_id).update(status=ResearchJob.Status.RUNNING)

    lines: list[str] = []

    def on_step(text: str) -> None:
        lines.append(text)
        ResearchJob.objects.filter(pk=job_id).update(log="\n".join(lines))

    try:
        check_setup()
        answer = clean(run_agent(job.question, on_step))
        if not answer:
            raise RuntimeError("The model returned an empty answer. Try again or rephrase.")

        media_root = Path(settings.MEDIA_ROOT)
        out_dir = media_root / "research" / str(job.user_id) / str(job.pk)
        saved = save_answer(job.question, answer, out_dir=str(out_dir))

        def rel(path):
            return os.path.relpath(path, media_root) if path else ""

        _finish(
            job_id,
            status=ResearchJob.Status.DONE,
            answer=answer,
            pdf_path=rel(saved.get("pdf")),
            docx_path=rel(saved.get("docx")),
        )
    except AgentConfigError as exc:
        _finish(job_id, status=ResearchJob.Status.ERROR, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Job %s failed", job_id)
        _finish(job_id, status=ResearchJob.Status.ERROR, error=f"{type(exc).__name__}: {exc}")
