from django.urls import path

from . import views

app_name = "research"

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("jobs/<int:pk>/", views.job_detail, name="job"),
    path("jobs/<int:pk>/status/", views.job_status, name="status"),
    path("jobs/<int:pk>/download/<str:fmt>/", views.download, name="download"),
]
