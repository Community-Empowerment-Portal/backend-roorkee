import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from communityEmpowerment.models import UserEvents, Scheme  # Replace 'myapp' with your actual app name
from django.utils import timezone

class Command(BaseCommand):
    help = 'Populate monthly dummy events for the past 12 months'

    def handle(self, *args, **kwargs):
        event_types = ['view', 'search', 'download', 'filter']
        states = ['Uttar Pradesh', 'Bihar', 'Tamil Nadu', 'Kerala', 'Maharashtra']
        today = timezone.now()

        for month_offset in range(12):
            base_date = today.replace(day=15) - timedelta(days=month_offset * 30)

            for _ in range(5):
                UserEvents.objects.create(
                    user=None,
                    event_type=random.choice(event_types),
                    scheme=None,
                    details={"state": random.choice(states)},
                    timestamp=base_date + timedelta(days=random.randint(-5, 5)),
                    ip_address="127.0.0.1",
                    user_agent="Mozilla/5.0"
                )

        self.stdout.write(self.style.SUCCESS("Dummy monthly UserEvents created successfully!"))