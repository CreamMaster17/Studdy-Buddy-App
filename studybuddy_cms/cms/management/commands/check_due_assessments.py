from django.core.management.base import BaseCommand

from cms.models import Assessment
from cms.views import is_on_track


class Command(BaseCommand):
    help = "Find due assessments and flag users who are off track. Run on a daily schedule."

    def handle(self, *args, **options):
        due = Assessment.objects.filter(active=True).select_related("subject", "owner")
        due = [a for a in due if a.is_due()]

        # need to hook into notifications app and email once that exists
        for assessment in due:
            on_track = is_on_track(assessment)
            status = "off track" if on_track is False else "on track" if on_track else "no data yet"
            self.stdout.write(
                f"[DUE] {assessment.owner} - {assessment.title} ({assessment.subject}): {status}"
            )
            
