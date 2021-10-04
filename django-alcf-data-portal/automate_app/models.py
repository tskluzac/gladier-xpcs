import json
import logging
import threading
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import models
import globus_sdk

import automate_app.exc

from globus_portal_framework.gclients import (
    load_globus_access_token
)

from automate_app.parsing import (
    parse_date, parse_details, parse_automate_response
)

try:
    import globus_automate_client
except ImportError:
    globus_automate_client = None

log = logging.getLogger(__name__)


class FlowConsumer(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name


class Flow(models.Model):
    flow_id = models.UUIDField()
    title = models.CharField(max_length=256)
    scope = models.CharField(max_length=256)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now_add=True)
    definition_checksum = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.title}-{self.id}'

    @staticmethod
    def __start_flows(actions):
        for action in actions:
            action.run_flow()
        log.debug(f'Finished starting {len(actions)} automate runs.')

    def batch(self, user, flow_input_list):
        """
        Start a batch of flows in a separate thread, given a list of input for each
        flow.
        :param user: User running the flow
        :param flow_input_list: A two tuple containing (flow_input, flow_parameters)
        :return: None
        """
        actions = []
        for flow_input, flow_parameters in flow_input_list:
            action = Action(flow=self, user=user)
            action.payload = flow_input
            action.parameters = flow_parameters
            action.save()
            actions.append(action)

        thread = threading.Thread(target=self.__start_flows, args=(actions,))
        thread.start()
        log.debug(f'User {user} batch started {len(actions)} flow runs using {self}')


class Action(models.Model):
    """A collection of actions for a flow, after a flow has been started."""
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=128)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now_add=True)
    parameter_data = models.TextField()
    payload_data = models.TextField()
    cache_data = models.TextField()

    @property
    def action_id(self):
        """WOULD REALLY be nice if we got this at the start of the flow, and
        set it as as base model property..."""
        return self.latest.get('action_id', '')

    def get_absolute_url(self):
        return reverse('automate-app:action-detail', args=[str(self.id)])

    @property
    def cache(self):
        return json.loads(self.cache_data or '{}')

    @property
    def latest(self):
        if not self.cache:
            return {}
        states_by_date = [(name, data.get('start_time', '0'))
                          for name, data in self.cache.items()]
        states_by_date.sort(key=lambda x: x[1])
        latest_state, _ = states_by_date[0]
        return self.cache[latest_state]

    @cache.setter
    def cache(self, value):
        self.cache_data = json.dumps(value or {}, indent=2)

    @property
    def parameters(self):
        return json.loads(self.parameter_data or '{}')

    @parameters.setter
    def parameters(self, value):
        self.parameter_data = json.dumps(value or '{}', indent=2)

    @property
    def payload(self):
        return json.loads(self.payload_data or '{}')

    @payload.setter
    def payload(self, value):
        self.payload_data = json.dumps(value or '{}', indent=2)

    @property
    def date_completed(self):
        return parse_date(self.latest.get('completion_time'))

    def get_flow_instance_authorizations(self):
        authorizations = [fia for fia in self.user.flow_delegations.all()
                          if fia.flow_id == self.flow_id]
        if authorizations:
            return authorizations
        # TODO -- Check group authorization
        # group_ids = [group['id'] for group in get_user_groups(self.user)]
        raise automate_app.exc.AuthorizationException(
            f'User {self.user} not authorized to run {self.flow.title}'
        )

    def get_flows_client(self):
        authorized_flows = self.get_flow_instance_authorizations()
        if not authorized_flows:
            raise automate_app.exc.AuthorizationException(f'User {self.user} not authorized '
                                                          f'for flow {self.flow}')
        return authorized_flows[0].flows_client

    def run_flow(self):
        fc = self.get_flows_client()
        r = fc.run_flow(self.flow.flow_id, self.flow.scope, self.payload,
                        **self.parameters).data
        self.status = r['status'] or 'Started'
        self.cache = {r['action_id']: r}
        self.save()
        log.info(f'Flow {self.flow} has been started by {self.user}.')

    def update_flow(self):
        action_id = self.latest.get('action_id')
        if action_id is None:
            log.warning(f'{self}: No action_id on flow! Skipping update...')
            return
        fc = self.get_flows_client()
        r = fc.flow_action_status(self.flow.flow_id, self.flow.scope,
                                  action_id).data
        new_action_id = r['action_id']

        # never call setitem (self.cache['foo'] = foo) on properties.
        # Only-ever set the base property (self.cache = foo)
        cache = self.cache
        cache[new_action_id] = parse_automate_response(r)
        self.cache = cache
        self.status = r['status']
        self.save()

    def get_details(self):
        return parse_details(self.latest)

    def __str__(self):
        return f'{self.flow.title} - {self.user} - {self.id} - {self.status}'


class FlowInstanceAuthorizer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE)
    delegations = models.ManyToManyField(User, related_name='flow_delegations')
    group = models.UUIDField(null=True, blank=True)
    client_id = models.CharField(max_length=128)
    access_token = models.CharField(max_length=128)
    refresh_token = models.CharField(max_length=128)
    expires_at_seconds = models.FloatField()

    @property
    def flows_client(self):
        """
        :returns an authorized Gloubs Automate Client
        """
        auto_auth = load_globus_access_token(self.user, 'flows.globus.org')
        flow_authorizer = self.get_flow_authorizer()

        # def flow_authorizer_callback(*args, **kwargs):
        #     return flow_authorizer
        log.debug(f'Flow authorizer: {flow_authorizer}')

        fc = globus_automate_client.FlowsClient.new_client(
            self.client_id,
            lambda *argc, **argv: flow_authorizer,
            globus_sdk.AccessTokenAuthorizer(auto_auth),
        )
        return fc

    def get_flow_authorizer(self):
        authorizer = globus_sdk.RefreshTokenAuthorizer(
            self.refresh_token,
            globus_sdk.NativeAppAuthClient(self.client_id),
            access_token=self.access_token,
            expires_at=self.expires_at_seconds,
        )
        authorizer.check_expiration_time()
        self.access_token = authorizer.access_token
        self.expires_at_seconds = authorizer.expires_at
        self.save()
        return authorizer
