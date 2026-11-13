from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class ResearchJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Waiting"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        ERROR = "error", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="research_jobs"
    )
    question = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    log = models.TextField(blank=True)
    answer = models.TextField(blank=True)
    error = models.TextField(blank=True)
    pdf_path = models.CharField(max_length=500, blank=True)    # relative to MEDIA_ROOT
    docx_path = models.CharField(max_length=500, blank=True)   # relative to MEDIA_ROOT
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.pk} {self.question[:50]}"

    @property
    def is_active(self):
        return self.status in (self.Status.PENDING, self.Status.RUNNING)

    def expire_if_stale(self):
        """A job that never finished (server restarted, worker crashed) must not stay
        'running' forever, otherwise it blocks the user's active-job limit."""
        limit = timedelta(minutes=settings.RESEARCH_JOB_TIMEOUT_MINUTES)
        if self.is_active and timezone.now() - self.created_at > limit:
            self.status = self.Status.ERROR
            self.error = "The job did not finish in time (the server may have been restarted)."
            self.finished_at = timezone.now()
            self.save(update_fields=["status", "error", "finished_at"])
        return self
