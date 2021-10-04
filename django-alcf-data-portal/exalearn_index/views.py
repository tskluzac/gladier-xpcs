import os
import logging
from urllib.parse import urlunparse, urlparse, urlencode
from django.middleware import csrf
from django.shortcuts import redirect
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse
import globus_sdk

from globus_portal_framework.gclients import load_transfer_client
from globus_portal_framework.gsearch import get_index

from alcf_data_portal.views import ProjectSearch, ProjectsView, ProjectDetail
from exalearn_index.exalearn_fields import EXALEARN_EP

log = logging.getLogger(__name__)


class LandingPage(ProjectsView):
    DEFAULT_TEMPLATE = 'exalearn/global/tabbed-project/landing-page.html'


class CSRFValidationFailure(Exception):
    pass


class TransferUtils(View):
    session_transfer_var = 'transfers'
    csrf_token_name = 'custom_transfer_csrf_token'
    csrf_token_param_name = 'csrf_token'

    def verify_session_csrf_token(self, token):
        session_csrf = self.request.session.get(self.csrf_token_param_name)
        if not session_csrf or session_csrf != token:
            log.debug(f'Request CSRF {token}, stored CSRF {session_csrf}')
            # If there was a previous task, clear it out.
            self.set_task({})
            raise CSRFValidationFailure('Request Token does not '
                                        'match stored token.')

    def set_session_csrf_token(self, token):
        self.request.session[self.csrf_token_param_name] = token

    def get_task(self):
        transfers = self.request.session.get(self.session_transfer_var, {})
        return transfers.get(self.kwargs['subject'], {})

    def set_task(self, data):
        transfers = self.request.session.get(self.session_transfer_var, {})
        transfers[self.kwargs['subject']] = data
        self.request.session[self.session_transfer_var] = transfers

    def update_task(self):
        task = self.get_task()
        if task:
            if task.get('data') and task['data']['status'] != 'ACTIVE':
                return task
            tc = load_transfer_client(self.request.user)
            task['data'] = tc.get_task(task['task_id']).data
            self.set_task(task)
            return task
        return {}


@method_decorator(csrf_exempt, name='dispatch')
class SubmitTransfer(ProjectDetail, TransferUtils):
    manifest_data = 'remote_file_manifest'
    # https://globus-sdk-python.readthedocs.io/en/stable/clients/transfer/#globus_sdk.TransferData  # noqa
    transfer_params = {
        'label': None,
        'submission_id': None,
        'sync_level': 'checksum',
        'verify_checksum': False,
        'preserve_timestamp': False,
        'encrypt_data': True,
        'deadline': None,
        'recursive_symlinks': 'ignore'
    }

    def get_label(self):
        return f'{get_index(self.kwargs.get("index"))["name"]} Transfer'

    def get_context_data(self, *args, **kwargs):
        """Returns a dict of """
        context = super().get_context_data(*args, **kwargs)
        remote_file_manifest = context.get(self.manifest_data)
        destination_info = {
            'endpoint': self.request.POST.get('endpoint', ''),
            'endpoint_id': self.request.POST.get('endpoint_id', ''),
            'path': os.path.join(self.request.POST.get('path', ''),
                                 self.request.POST.get('folder[0]', '')),
            'transfer_label': self.request.POST.get('label', self.get_label())
        }
        if any(destination_info.values()):
            self.verify_session_csrf_token(self.request.GET.get('csrf_token'))
            # Set token to None so it can't be used again
            self.set_session_csrf_token(None)
            return {'remote_file_manifest': remote_file_manifest,
                    'destination_info': destination_info}
        return dict()

    def submit_transfer(self, context):
        """
        """
        tc = load_transfer_client(self.request.user)
        params = self.transfer_params.copy()
        params['label'] = self.get_label()
        destination = context['destination_info']
        td = globus_sdk.TransferData(tc, EXALEARN_EP,
                                     destination['endpoint_id'], **params)
        for ent in context['remote_file_manifest']:
            item = urlparse(ent['url']).path
            dest = os.path.join(destination['path'], os.path.basename(item))
            log.debug(f'User {self.request.user} submitted detail transfer '
                      f'{item} to {dest}')
            td.add_item(item, dest)
        result = tc.submit_transfer(td)
        self.set_task({'task_id': result['task_id'], 'data': {}})

    def get(self, request, index, project, subject):
        log.warning(f'{request.user} did GET request to submit-transfer')
        return redirect('tp-project-detail', index, project, subject)

    def post(self, request, index, project, subject):
        try:
            context = self.get_context_data(index, project, subject)
            if context:
                self.submit_transfer(context)
        except CSRFValidationFailure:
            log.warning('CSRF Validation Failure for attempted transfer of '
                        'files for user {}. Someone may be doing something '
                        'nasty!'.format(self.request.user.username))
            messages.error(request, 'CSRF Validation failed, unable to start '
                                    'your transfer.')
        return redirect('tp-project-detail', index, project, subject)


class TransferAwareDetailOverview(ProjectDetail, TransferUtils):
    submit_transfer_url_name = 'tp-submit-transfer'
    csrf_token_name = 'custom_transfer_csrf_token'
    csrf_token_param_name = 'csrf_token'
    template_name = 'concierge-app/tabbed-project/manifests.html'
    helper_page_params = {
        'method': 'POST',
        'filelimit': 0,
        'folderlimit': 1,
        'label': '',
        'action': '',
        'cancelurl': ''
    }

    def __init__(self, manifest_key_name='remote_file_manifest'):
        super().__init__()
        self.manifest_key_name = manifest_key_name

    def get_redirect_url(self, path):
        return urlunparse((self.request.scheme, self.request.get_host(),
                           path, '', '', ''))

    def get_helper_page_url(self):
        """Generate the helper page URL for the the Globus Webapp. Details:
        https://docs.globus.org/api/helper-pages/browse-endpoint/

        The callback url also includes a CSRF Token to prevent CSRF attacks.
        This is technically a misuse of CSRF tokens, since they weren't
        intended to leave the portal into a request sent somewhere else.
        Additionally, Django can't verify the token properly due to the helper
        pages not posting the token along with the other transfer POST data,
        so the token needs to be passed as a GET param. It's later compared
        in the SubmitTransfer view with verify_session_csrf_token
        """
        # Setup general helper page parameters and encode them into queryparams
        hp_params = self.helper_page_params.copy()
        index_data = get_index(self.kwargs.get('index'))
        cancel_url = self.get_redirect_url(self.request.get_full_path())
        hp_params.update({'label': f'{index_data["name"]} Transfer',
                          'cancelurl': cancel_url})
        hp_params_enc = urlencode(hp_params)

        token = csrf.get_token(self.request)
        # The "action" param needs to be encoded separately, since it's the
        # full redirect URL the Globus Webapp will respond with, and the
        # csrf token will be separate
        action_param_param = urlencode({self.csrf_token_param_name: token})
        self.set_session_csrf_token(token)
        base_url = reverse(self.submit_transfer_url_name,
                           kwargs={'index': self.kwargs['index'],
                                   'project': self.kwargs['project'],
                                   'subject': self.kwargs['subject']})
        redirect_url = '{}?{}'.format(
            self.get_redirect_url(base_url),
            action_param_param
        )
        # Encode the full action param url and add it to the other helper page
        # URLs
        action_param = urlencode({'action': redirect_url})
        log.debug(f'"action" redirect helper page url: {action_param}')
        hp_params_enc = f'{hp_params_enc}&{action_param}'
        return urlunparse(('https', 'app.globus.org', 'file-manager', '',
                           hp_params_enc, ''))

    # Will add if this is asked for, currently it has problems with sessions
    # def parse_task_dates(self, task):
    #     if not task or not task.get('data'):
    #         return
    #     date_fields = ['request_time', 'deadline']
    #     for df in date_fields:
    #         task['data'][df] = datetime.strptime(task['data'][df],
    #                                              '%Y-%m-%d %H:%M:%S%z')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['transfer'] = self.update_task()
        context['helper_page_transfer_url'] = self.get_helper_page_url()
        return context


class SliderFacetsSearch(ProjectSearch):

    def get_context_data(self, index):
        context = super().get_context_data(index)
        facets = context.get('search', {}).get('facets')
        if facets:
            context['search']['facets'] = self.get_slider_facets(facets)
        return context

    def get_slider_facets(self, facets):

        filters = {f['field_name']: f['values'][0] for f in self.filters}

        processed = []
        for facet in facets:
            buckets = facet.get('buckets', [])
            if not buckets:
                continue
            facet['filter_type'] = buckets[0]['filter_type']
            facet['filter_query_key'] = buckets[0]['search_filter_query_key']
            if facet['filter_type'] != 'range':
                processed.append(facet)
                continue
            ranges = [(float(low), float(high)) for low, high in [
                      b['value'].split('--') for b in buckets]]
            low, high = zip(*ranges)
            # There seems to be a problem where sliding the sliders all the way
            # to one side will result in the upper_bound or lower_bound getting
            # 'stuck' on one side, where the filter is permanently stuck to a
            # subset of results. This forces the sliders to be a little wider
            # so this hopefully won't happen.
            incr = (max(high) - min(low)) / 20
            facet['lower_bound'] = min(low) - incr
            facet['upper_bound'] = max(high) + incr
            # Set the upper and lower bounds on the filter based on the
            # values in settings
            facet_filter = filters.get(buckets[0]['field_name'], {})
            facet['filter_low'] = facet_filter.get('from')
            facet['filter_high'] = facet_filter.get('to')
            processed.append(facet)
        return processed
