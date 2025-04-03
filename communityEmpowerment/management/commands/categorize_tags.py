from django.core.management.base import BaseCommand
from communityEmpowerment.models import Tag

class Command(BaseCommand):
    help = "Categorize existing tags into relevant categories"

    def handle(self, *args, **kwargs):
        for tag in Tag.objects.all():
            tag.save() 
        self.stdout.write(self.style.SUCCESS("Successfully updated all tags with correct categories!"))
