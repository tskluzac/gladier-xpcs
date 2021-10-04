import logging
import json
import os
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from automate_app.models import Action, Flow
from kanzus_index import apps

log = logging.getLogger(__name__)

INDEX_NAME = 'kanzus'
assert getattr(apps, 'SEARCH_INDEXES').get(INDEX_NAME), 'Index name changed.'


class SampleReprocess(models.Model):
    """
    Take an existing SSX subject, and reprocess the job with a new PHIL
    file to attempt to find more INT diffractions using DIALS.
    1. Send a user's bagged data (containing many imm files) to Theta
    2. Run CORR on imm files and produce hdfs, metadata, and images
    3. Upload the files to petrel and register them in Globus Search using
        pilot.
    This flow must be run by someone with access to Theta.
    """
    # FLOW_PAYLOAD = payload.SampleReprocessPayload

    subject = models.CharField(max_length=256)
    project = models.CharField(max_length=64)
    # User in this case is the user who created the task. Might not be the
    # original user who authorized the flow.
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    remote_path = models.CharField(max_length=256)
    action = models.ForeignKey('automate_app.Action', on_delete=models.CASCADE)
    nproc = models.IntegerField()
    beamx = models.FloatField()
    beamy = models.FloatField()
    aps_data_root = models.CharField(max_length=256, null=True)
    run_name = models.CharField(max_length=256, null=True)
    options_data = models.TextField(null=True)

    @property
    def options(self):
        return json.loads(self.options_data or '{}')

    @options.setter
    def options(self, value):
        self.options_data = json.dumps(value or {}, indent=2)

    @property
    def display_name(self):
        return os.path.basename(self.subject)

    def get_absolute_url(self):
        return reverse('tp-project-detail',
                       kwargs={
                           'index': INDEX_NAME,
                           'project': self.project,
                           'subject': self.subject
                       })

    def generate_payload(self):
        # Generate the flow payload, do last minute checks
        fp = self.FLOW_PAYLOAD(self)
        #  Fetch the flow and setup the action. DO NOT start the flow yet.
        payload = fp.get_payload_inputs()
        fp.runtime_check(payload)
        self.action.payload = payload
        self.action.save()

    @classmethod
    def new_action(cls, user):
        # Fetch the flow and setup the action. DO NOT start the flow yet.
        checksum = cls.FLOW_PAYLOAD.get_checksum()
        flow = Flow.by_consumer(cls.__name__).filter(
            definition_checksum=checksum).first()
        if not flow:
            name = cls.__name__
            raise Exception('No flow with matching checksum! You need to call '
                            f'"python manage.py authorize_flow {name}"')
        log.debug(f'Using flow {flow} for {user}s new Kanzus Task.')
        action = Action(flow=flow, user=user)
        action.save()
        return action

    @classmethod
    def is_authorized(cls, user):
        # @HACK! This should probably be something queryable, maybe with
        # Django groups, but for now we'll do this to ensure only select
        # people can start flows.
        authorized = user.username in ['nickolaussaint@globusid.org']
        log.debug(f'User {user.username} is Authorized? {authorized}')
        return authorized
