from django.core.management.base import BaseCommand
from automate_app.models import Flow


class Command(BaseCommand):
    help = 'List current automate flows'

    def handle(self, *args, **options):
        self.stdout.write('Flows:')
        for flow in Flow.objects.all():
            self.stdout.write(f'{flow.title} -- {flow.scope}')
