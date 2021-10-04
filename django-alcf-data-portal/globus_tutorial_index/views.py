import logging
from urllib.parse import unquote
from django.shortcuts import render
import globus_sdk
from globus_portal_framework.gsearch import (
    get_template, get_index, process_search_data
)
from globus_portal_framework import (
    PreviewURLNotFound, PreviewException
)
from globus_portal_framework.gclients import (
    load_search_client
)
from globus_portal_framework.gtransfer import preview
from globus_portal_framework.apps import get_setting
from alcf_data_portal.views import CustomSearch

log = logging.getLogger(__name__)


def _custom_get_subject(index, subject, user, index_uuid):
    """Custom get subject to get by uuid without lookup"""
    client = load_search_client(user)
    try:
        idata = get_index(index)
        result = client.get_subject(index_uuid, unquote(subject),
                                    result_format_version='2017-09-01')
        return process_search_data(idata.get('fields', {}), [result.data])[0]
    except globus_sdk.exc.SearchAPIError:
        return {'subject': subject, 'error': 'No data was found for subject'}


def landing_page(request, index):
    indices = []
    if request.user.is_authenticated:
        try:
            sc = load_search_client(request.user)
            indices = [si for si in sc.get("/v1/index_list").data['index_list']
                       if si['is_trial']]
        except globus_sdk.exc.SearchAPIError:
            log.debug('Failed to fetch user indices', exc_info=True)

    template = get_template(index, 'landing-page.html')
    return render(request, template, {'indices': indices})


def tutorial_detail(request, index, index_uuid, subject):
    ctx = _custom_get_subject(index, subject, request.user, index_uuid)
    ctx['index_uuid'] = index_uuid
    return render(request, get_template(index, 'detail-overview.html'), ctx)


def tutorial_detail_preview(request, index, index_uuid, subject, endpoint=None, url_path=None):
    context = _custom_get_subject(index, subject, request.user, index_uuid)
    context['index_uuid'] = index_uuid
    try:
        scope = request.GET.get('scope')
        if not any((endpoint, url_path, scope)):
            log.error('Preview Error: Endpoint, Path, or Scope not given. '
                      '(Got: {}, {}, {})'.format(endpoint, url_path, scope))
            raise PreviewURLNotFound(subject)
        url = 'https://{}/{}'.format(endpoint, url_path)
        log.debug('Previewing with url: {}'.format(url))
        context['preview_data'] = \
            preview(request.user, url, scope, get_setting('PREVIEW_DATA_SIZE'))
    except PreviewException as pe:
        if pe.code in ['UnexpectedError', 'ServerError']:
            log.exception(pe)
        context['detail_error'] = pe
        log.debug('User error: {}'.format(pe), exc_info=True)
    return render(request, get_template(index, 'detail-preview.html'), context)


class TutorialSearch(CustomSearch):
    """
    Custom tutorial search to fetch with user's chosen index instead of pre-configured
    index.
    """
    def post_search(self, client, index_uuid, search_client_data):
        """If you want to inject or modify any parameters in the
        globus_sdk.SearchClient.post_search function, you can override this
        function. """
        return client.post_search(self.kwargs['index_uuid'], search_client_data)

    def get_context_data(self, index):
        """calls post_search and process_result. If there is an error, returns
        a context with a single 'error' var and logs the exception."""
        if not self.kwargs.get('index_uuid'):
            return {'error': 'No index uuid provided with search.'}
        ctx = super().get_context_data(index)
        ctx['index_uuid'] = self.kwargs['index_uuid']
        return ctx
