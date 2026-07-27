from django.conf import settings
from django.db import models
from django.utils import timezone


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

#content models for subjects
class ContentItem(models.Model):
    CONTENT_TYPES = [
        ("note", "Note"),
        ("slide", "Slide Deck"),
        ("pdf", "PDF"),
        ("video", "Video"),
        ("link", "External Link"),
        ("other", "Other"),
    ]
    #defining subjects
    subject = models.ForeignKey(Subject, related_name="content_items", on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES, default="other")
    file = models.FileField(upload_to="content_uploads/%Y/%m/", blank=True, null=True)
    external_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["subject", "content_type"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.subject.name})"


class Assessment(models.Model):
    """A routine check-in tied to a subject, used to track whether the user is on pace."""

    FREQUENCY_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("biweekly", "Biweekly"),
        ("monthly", "Monthly"),
    ]

    subject = models.ForeignKey(Subject, related_name="assessments", on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default="weekly")
    passing_score = models.PositiveSmallIntegerField(default=70)  # percent
    next_due_date = models.DateTimeField()
    active = models.BooleanField(default=True)

    FREQUENCY_DAYS = {
        "daily": 1,
        "weekly": 7,
        "biweekly": 14,
        "monthly": 30,
    }

    def advance_due_date(self):
        from datetime import timedelta

        days = self.FREQUENCY_DAYS[self.frequency]
        self.next_due_date = timezone.now() + timedelta(days=days)
        self.save(update_fields=["next_due_date"])

    def is_due(self):
        return self.active and self.next_due_date <= timezone.now()

    def __str__(self):
        return f"{self.title} - {self.subject.name}"

#quiz attempts for "improvement" metric
class AssessmentAttempt(models.Model):
    assessment = models.ForeignKey(Assessment, related_name="attempts", on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField()  # percent
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-taken_at"]

    @property
    def passed(self):
        return self.score >= self.assessment.passing_score

    def __str__(self):
        return f"{self.assessment.title}: {self.score}%"


#not finished atm 
class Note(models.Model):
    subject = models.ForeignKey(Subject, related_name="notes", on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_item = models.ForeignKey(
        ContentItem, related_name="notes", on_delete=models.SET_NULL, blank=True, null=True
    )
    body = models.TextField()
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags.")
    pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    # TODO: content_item link, tags, updated_at, pinning, search indexing

    class Meta:
       ordering = ["-pinned", "-created_at"]
        indexes = [
            models.Index(fields=["subject", "owner"]),
            models.Index(fields=["tags"]),
        ]

    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
    
    def __str__(self):
        return f"Note ({self.subject.name}, {self.created_at:%Y-%m-%d})"
