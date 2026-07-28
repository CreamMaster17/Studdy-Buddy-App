from django.contrib import admin

from .models import Assessment, AssessmentAttempt, ContentItem, Note, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "content_type", "owner", "created_at")
    list_filter = ("subject", "content_type")
    search_fields = ("title", "description")


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "owner", "frequency", "next_due_date", "active")
    list_filter = ("subject", "frequency", "active")


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ("assessment", "score", "taken_at")
    list_filter = ("assessment__subject",)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("subject", "owner", "content_item", "pinned", "created_at", "updated_at")
    list_filter = ("subject", "pinned")
    search_fields = ("body", "tags")