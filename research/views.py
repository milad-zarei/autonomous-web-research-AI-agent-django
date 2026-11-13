from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from . import tasks
from .forms import QuestionForm
from .models import ResearchJob


def _active_jobs(user):
    """Active jobs of this user; stale ones are closed first."""
    jobs = list(
        ResearchJob.objects.filter(
            user=user,
            status__in=[ResearchJob.Status.PENDING, ResearchJob.Status.RUNNING],
        )
    )
    for job in jobs:
        job.expire_if_stale()
    return [j for j in jobs if j.is_active]


@login_required
def home(request):
    form = QuestionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        since = timezone.now() - timedelta(days=1)
        today = ResearchJob.objects.filter(user=request.user, created_at__gte=since).count()
        if len(_active_jobs(request.user)) >= settings.RESEARCH_MAX_ACTIVE_PER_USER:
            messages.error(
                request, "You already have research running. Wait for it to finish, then ask again."
            )
        elif today >= settings.RESEARCH_MAX_PER_DAY:
            messages.error(request, "Daily limit reached. Try again tomorrow.")
        else:
            job = ResearchJob.objects.create(
                user=request.user, question=form.cleaned_data["question"]
            )
            tasks.submit(job.pk)
            return redirect("research:job", pk=job.pk)

    jobs = request.user.research_jobs.all()[:15]
    return render(request, "research/home.html", {"form": form, "jobs": jobs})


@login_required
def job_detail(request, pk):
    job = get_object_or_404(ResearchJob, pk=pk, user=request.user).expire_if_stale()
    return render(request, "research/job.html", {"job": job})


@login_required
def job_status(request, pk):
    job = get_object_or_404(ResearchJob, pk=pk, user=request.user).expire_if_stale()
    return JsonResponse({"status": job.status, "label": job.get_status_display(), "log": job.log})


@login_required
def download(request, pk, fmt):
    job = get_object_or_404(ResearchJob, pk=pk, user=request.user)
    rel = {"pdf": job.pdf_path, "docx": job.docx_path}.get(fmt)
    if not rel:
        raise Http404("No such file.")
    media_root = Path(settings.MEDIA_ROOT).resolve()
    path = (media_root / rel).resolve()
    if media_root not in path.parents or not path.is_file():
        raise Http404("No such file.")
    return FileResponse(open(path, "rb"), as_attachment=True, filename=path.name)


def signup(request):
    if not settings.RESEARCH_ALLOW_SIGNUP:
        raise Http404()
    if request.user.is_authenticated:
        return redirect("research:home")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("research:home")
    return render(request, "registration/signup.html", {"form": form})
