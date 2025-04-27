from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from datetime import datetime
from communityEmpowerment.models import CustomUser

class Command(BaseCommand):
    help = 'Send emails to users about their saved schemes expiring in 1 or 7 days'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        users = CustomUser.objects.exclude(email__isnull=True).exclude(email='')

        for user in users:
            saved_schemes = user.saved_schemes.all()
            expiring_schemes = []

            for saved in saved_schemes:
                valid_upto = self.extract_date(saved.valid_upto)
                if valid_upto:
                    days_left = (valid_upto - today).days
                    if days_left in (1, 7):
                        expiring_schemes.append((saved.title, days_left, saved.id))

            if expiring_schemes:
                subject = "Reminder: Your Saved Scheme(s) are Expiring Soon"

                # Plain text version
                plain_message = f"Dear {user.username or 'User'},\n\nThe following saved schemes are expiring:\n\n"
                for scheme_name, days_left, scheme_id in expiring_schemes:
                    scheme_url = f"{settings.FRONTEND_URL}/AllSchemes?tab=Saved&scheme_id={scheme_id}"
                    plain_message += f"- {scheme_name} (Expires in {days_left} day(s))\n  View Scheme: {scheme_url}\n"
                plain_message += "\nPlease take necessary action.\n\nRegards,\nTeam"

                # HTML version with clickable links in purple color
                html_message = f"<p>Dear {user.username or 'User'},</p><p>The following saved schemes are expiring:</p><ul>"
                for scheme_name, days_left, scheme_id in expiring_schemes:
                    scheme_url = f"{settings.FRONTEND_URL}/AllSchemes?tab=Saved&scheme_id={scheme_id}"
                    html_message += (
                        f'<li>{scheme_name} (Expires in {days_left} day(s))<br>'
                        f'<a href="{scheme_url}" target="_blank" style="color: purple; text-decoration: none;">View Scheme</a></li>'
                    )
                html_message += "</ul><p>Please take necessary action.</p><p>Regards,<br>Team</p>"

                # Send email with both plain text and HTML content
                email = EmailMultiAlternatives(subject, plain_message, settings.EMAIL_FROM, [user.email])
                email.attach_alternative(html_message, "text/html")
                email.send()

        self.stdout.write(self.style.SUCCESS('Successfully sent expiry emails.'))

    def extract_date(self, input_str):
        if not input_str or not isinstance(input_str, str):
            return None

        invalid_phrases = [
            'not available',
            'not specified',
            'present',
            'null',
            '-none-',
            'till the scheme is amended or terminated',
            '18 years of age',
            'ongoing',
        ]

        cleaned = input_str.strip().lower()
        if cleaned in invalid_phrases:
            return None

        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%b %Y", "%Y"):
            try:
                parsed = datetime.strptime(
                    input_str.replace('-', '/') if fmt == "%d/%m/%Y" else input_str,
                    fmt
                )
                if fmt == "%b %Y":
                    parsed = parsed.replace(day=1)
                if fmt == "%Y":
                    parsed = parsed.replace(month=12, day=31)
                return parsed.date()
            except Exception:
                continue

        return None
