from django.contrib import admin

from .models import ResearchJob


@admin.register(ResearchJob)
class ResearchJobAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "short_question", "status", "created_at", "finished_at")
    list_filter = ("status", "created_at")
    search_fields = ("question", "user__username")
    readonly_fields = ("created_at", "finished_at")

    @admin.display(description="Question")
    def short_question(self, obj):
        return obj.question[:70]
