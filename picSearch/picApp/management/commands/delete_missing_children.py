import os
from django.core.management.base import BaseCommand
from picApp.models import MissingChild

class Command(BaseCommand):
    help = 'Delete specific MissingChild records (kalu Vi, gfvdg, Amakalu Vitalis)'

    def handle(self, *args, **options):
        targets = ['kalu Vi', 'gfvdg', 'Amakalu Vi']
        deleted = MissingChild.objects.filter(name__in=targets).delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted records: {targets} (rows affected: {deleted[0]})'))
