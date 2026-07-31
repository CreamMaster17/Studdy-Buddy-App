from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

from ...models import Assessment
from ...views import is_on_track


class Command(BaseCommand):
    help = "Find due assessments and flag users who are off track. Run on a daily schedule."

    def handle(self, *args, **options):
        due = Assessment.objects.filter(active=True).select_related("subject", "owner")
        due = [a for a in due if a.is_due()]

        
        for assessment in due:
            on_track = is_on_track(assessment)
            status = "off track" if on_track is False else "on track" if on_track else "no data yet"
            self.stdout.write(
                f"[DUE] {assessment.owner} - {assessment.title} ({assessment.subject}): {status}"
            )

            owner_email = getattr(assessment.owner, "email", "")
            if owner_email:
                send_mail(
                    subject=f"Study Buddy: {assessment.title} is due",
                    message=(
                        f'Your assessment "{assessment.title}" for {assessment.subject} is due.\n'
                        f"Current status: {status}."
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    recipient_list=[owner_email],
                    fail_silently=True,
                )