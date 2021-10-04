from django.core.management.base import BaseCommand
from automate_app import flow_registration


class Command(BaseCommand):
    help = 'Authorizes an Automate Flow'

    def add_arguments(self, parser):
        parser.add_argument('model', nargs=1)
        parser.add_argument('-r', '--re-register', required=False,
                            action='store_true',
                            help='Re-register and authorize the flow')

    def handle(self, *args, **options):

        flow_models = flow_registration.get_flow_models()
        model = flow_models.get(options.get('model')[0])

        if not model:
            mfmt = '\n\t'.join(flow_models.keys())
            self.stderr.write(f'model must be one of: \n\t{mfmt}')
            return

        try:
            flow = flow_registration.native_authorize_flow(model)
            self.stdout.write(f'Flow deployed {flow}.')
        except Exception as e:
            self.stderr.write(str(e))
            return
