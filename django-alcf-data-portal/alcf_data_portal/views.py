import logging
import time
from urllib.parse import urlparse, unquote_plus
from django.views.generic import View
from django.conf import settings
from django.shortcuts import render
from django.contrib import messages
import globus_sdk
from globus_portal_framework.gsearch import (
    get_template, get_search_filters, get_facets,
    get_search_query, process_search_data, get_index, prepare_search_facets,
    get_pagination, get_subject
    )
from globus_portal_framework.gclients import (
    load_search_client, get_user_groups
)
import globus_portal_framework.exc

log = logging.getLogger(__name__)


def index_selection(request):
    context = {'indexes': []}
    for name, data in settings.SEARCH_INDEXES.items():
        idata = data.copy()
        idata['index_name'] = name
        idata['name'] = idata.get('name', name.capitalize())
        context['indexes'].append(idata)
    return render(request, 'templates/landing-page.html', context)


def kasthuri_landing_page(request):
    return render(request, 'kasthuri/landing-page.html', {})


def tabbed_project_landing_page(request, index):
    groups = []
    if request.user.is_authenticated:
        try:
            user_groups = get_user_groups(request.user)
            groups = {gi['id']: gi for gi in user_groups}
        except ValueError:
            # This can happen if a user logged in previously before we set the
            # groups scope on the portal. Simply ignore it.
            log.debug(f'User {request.user} does not have a groups token!')
    template = get_template(index, 'global/tabbed-project/landing-page.html')
    return render(request, template, {'user_groups': groups})


class CustomSearch(View):
    """
    Customize components of a search during different phases of receiving a
    request from a user to rendering a template. This is a handy class to
    customize if you want to modify the request sent to Globus Search, or
    customize the data received by Globus Search before it is rendered on the
    page.

    See post_search for customizing the result before it is sent to Globus
    Search.

    See process_result to override how the result is processed before it is
    rendered by the template.
    """

    DEFAULT_TEMPLATE = 'search.html'

    def __init__(self, template=None, results_per_page=10):
        super().__init__()
        self.template = template or self.DEFAULT_TEMPLATE
        self.results_per_page = results_per_page

    @property
    def query(self):
        return get_search_query(self.request)

    @property
    def filters(self):
        return get_search_filters(self.request)

    @property
    def facets(self):
        index = self.kwargs.get('index')
        if index:
            return prepare_search_facets(get_index(index).get('facets'))
        return []

    @property
    def page(self):
        return self.request.GET.get('page', 1)

    @property
    def offset(self):
        """Get the calculated offset based on the page number and configured
        results-per-page. This value is sent in the request to Globus Search"""
        return (int(self.page) - 1) * self.results_per_page

    @property
    def sort(self):
        return self.get_index_info().get('sort', [])

    def get_index_info(self, index_uuid=None):
        """Fetch info on an index defined in settings.py"""
        return get_index(index_uuid or self.kwargs.get('index'))

    def get_search_client(self):
        return load_search_client(self.request.user)

    def post_search(self, client, index_uuid, search_client_data):
        """If you want to inject or modify any parameters in the
        globus_sdk.SearchClient.post_search function, you can override this
        function. """
        return client.post_search(index_uuid, search_client_data)

    def set_search_session_data(self, index):
        """Set some metadata about the search in the user's session. This will
        record some data about their last search to fill in some basic DGPF
        context, such as the 'Back To Search' link on a result detail page.
        """
        self.request.session['search'] = {
            'full_query': urlparse(self.request.get_full_path()).query,
            'query': self.query,
            'filters': self.filters,
            'index': index,
        }

    def process_result(self, index_info, search_result):
        """
        Process the result from Globus Search into data ready to be rendered
        into search templates.
        """
        return {
            'search': {
                'search_results': process_search_data(
                    index_info.get('fields', []), search_result.data['gmeta']),
                'facets': get_facets(
                    search_result, index_info.get('facets', []), self.filters,
                    index_info.get('filter_match')),
                'pagination': get_pagination(
                    search_result.data['total'], search_result.data['offset']),
                'count': search_result.data['count'],
                'offset': search_result.data['offset'],
                'total': search_result.data['total'],
            }
        }

    def get_context_data(self, index):
        """calls post_search and process_result. If there is an error, returns
        a context with a single 'error' var and logs the exception."""
        data = {
            'q': self.query,
            'filters': self.filters,
            'facets': self.facets,
            'offset': self.offset,
            'sort': self.sort,
            'limit': self.results_per_page,
            'result_format_version': '2017-09-01',
        }
        try:
            index_info = self.get_index_info(index)
            result = self.post_search(self.get_search_client(),
                                      index_info['uuid'], data)
            return self.process_result(index_info, result)
        except globus_portal_framework.exc.ExpiredGlobusToken:
            # Don't catch this exception. Middleware will automatically
            # redirect the user to login again for fresh tokens.
            raise
        except Exception as e:
            if settings.DEBUG:
                raise
            log.exception(e)
        return {'error': 'There was an error in your search, please try a '
                         'different query or contact your administrator.'}

    def get(self, request, index, *args, **kwargs):
        """
        Fetches the context, then renders a page. Calls 'get_template', which
        checks to see if there is an overridden page for a given index. If
        there is, that is used instead. Otherwise, standard Django template
        precedence loading is used.

        If there is an error, a Django message is sent which can be rendered
        by templates that support them.
        """
        context = self.get_context_data(index)
        self.set_search_session_data(index)
        error = context.get('error')
        if error:
            messages.error(request, error)
        return render(request, get_template(index, self.template), context)


class ProjectManifestSessionCache:
    PROJECT_MANIFEST_INDEX = None
    PROJECT_MANIFEST_SUBJECT = 'globus://project-manifest.json'
    PROJECT_MANIFEST_CACHE_NAME = 'globus_portal_framework_project_manifest'
    # Cache expires in 60 seconds
    PROJECT_MANIFEST_CACHE_EXPIRES = 60
    USE_SESSION_CACHE = True

    def is_cache_expired(self, request, index):
        manifest = request.session.get(self.PROJECT_MANIFEST_CACHE_NAME, {})
        index_manifest = manifest.get(index, {})
        if not index_manifest or index_manifest.get('last_updated') is None:
            return True
        expire_time = (index_manifest['last_updated'] +
                       self.PROJECT_MANIFEST_CACHE_EXPIRES)
        return expire_time <= time.time()

    def get_manifest(self, request, index):
        try:
            search_client = load_search_client(request.user)
            index_info = get_index(self.PROJECT_MANIFEST_INDEX or index)
            globus_response = search_client.get_subject(
                index_info['uuid'], self.PROJECT_MANIFEST_SUBJECT,
                result_format_version='2017-09-01')
            print(f"Get manifest: {globus_response.data['content'][0]}")

            # import json
            #
            # with open("/Users/tylerskluzacek/Desktop/manifest.json", 'w') as to_write:
            #     json.dump(new_man, to_write)

            return globus_response.data['content'][0]
        except globus_sdk.exc.SearchAPIError as sapie:
            if sapie.http_status == 404:
                raise ValueError('Unable to find project manifest {} at index '
                                 '{}. Ingest a project manifest at that '
                                 'location or specify a custom index and/or '
                                 'subject to fetch that information.'.format(
                                    self.PROJECT_MANIFEST_SUBJECT,
                                    self.PROJECT_MANIFEST_INDEX or index)
                                 ) from None
            raise

    def get_project_manifest(self, request, index, force_reload_cache=False):
        if self.USE_SESSION_CACHE is True:
            expired = self.is_cache_expired(request, index)
            if not force_reload_cache and not expired:
                man = request.session[self.PROJECT_MANIFEST_CACHE_NAME]
                return man[index]['data']

        reason = 'Forced Reload' if force_reload_cache else 'Expired'
        log.debug('Refreshing project manifest cache for user {} for reason {}'
                  ' on index {}'.format(request.user, reason, index))

        new_man = self.get_manifest(request, index)
        if self.USE_SESSION_CACHE is False:
            return new_man
        self.set_session_data(request, index, new_man)


        return new_man

    def get_project_context(self, request, index, project,
                            force_reload_cache=False):
        manifest = self.get_project_manifest(
            request, index, force_reload_cache=force_reload_cache
        )

        # import json

        # with open("/Users/tylerskluzacek/Desktop/manifest.json", 'w') as to_write:
        #     json.dump(new_man, to_write)
        return {
            'project': project,
            'project_info': manifest.get('projects', {}).get(project),
            'project_manifest': manifest
        }

    def get_session_data(self, request, index):
        man = request.session.get(self.PROJECT_MANIFEST_CACHE_NAME, {})
        return man.get(index, {}).get('data', {})

    def set_session_data(self, request, index, data):
        smanifest = request.session.get(self.PROJECT_MANIFEST_CACHE_NAME, {})
        smanifest[index] = {
            'data': data,
            'last_updated': int(time.time()),
        }
        request.session[self.PROJECT_MANIFEST_CACHE_NAME] = smanifest


class ProjectsView(CustomSearch, ProjectManifestSessionCache):

    DEFAULT_TEMPLATE = 'global/tabbed-project/projects-page.html'

    def post_search(self, client, index_uuid, data):
        data = {'q': '*',
                'facets': [
                    {
                        'field_name': 'project_metadata.project-slug',
                        'name': 'Project',
                        'type': 'terms'
                    },
                ],
                'limit': 0
                }
        results = client.post_search(index_uuid, data)
        return results

    def process_result(self, index_data, result):
        project_result_counts = {
            d['value']: d['count']
            for d in result.data['facet_results'][0]['buckets']
        }
        pmanifest = self.get_project_manifest(self.request,
                                              self.kwargs.get('index'))
        if not pmanifest:
            log.warning('No manifest found for {} index'.format(index_data))
        projects = []
        groups = {k: v for k, v in pmanifest.get('groups', {}).items()}
        manifest_projects = pmanifest.get('projects', {})
        for project_name, project_data in manifest_projects.items():
            if project_data['search_index'] != index_data['uuid']:
                continue
            data = project_data.copy()
            data['project'] = project_name
            data['count'] = project_result_counts.get(project_name, 0)
            group_name = groups.get(data.get('group'))
            if not group_name:
                log.warning('{} -- {}: No group name in pilot manifest, '
                            'should be set to: uuid = name under [groups] '
                            'Using defaults instead.'.format(
                    index_data['uuid'], project_name))
                group_name = project_name
            data['group_name'] = group_name
            projects.append(data)
        return {'projects': projects, 'groups': pmanifest.get('groups')}


class ProjectSearch(CustomSearch, ProjectManifestSessionCache):
    default_project_field = 'project_metadata.project-slug'

    def __init__(self, project_field=None, **kwargs):
        super().__init__(**kwargs)
        self.project_field = project_field or self.default_project_field

    def post_search(self, client, index_uuid, search_client_data):
        """Search based on the project where the user navigated Expects URLs
        like: exalearn/projects/cosmoflow where 'cosmoflow' is the project
        being filtered."""
        if self.kwargs.get('project'):
            search_client_data['filters'].append({
                'field_name': 'project_metadata.project-slug',
                'type': 'match_all',
                'values': [self.kwargs['project']]
            })
        return client.post_search(index_uuid, search_client_data)

    def process_result(self, index_info, search_result):
        """Add the project in addition to the search results. This is handy
        for rebuilding the current url."""
        results = super().process_result(index_info, search_result)
        results.update(self.get_project_context(self.request,
                                                self.kwargs.get('index'),
                                                self.kwargs.get('project')))

        return results


class ProjectDetail(View, ProjectManifestSessionCache):
    DEFAULT_TEMPLATE = 'detail-overview.html'

    def __init__(self, template=None):
        super().__init__()
        self.template = template or self.DEFAULT_TEMPLATE

    def clean_subject(self, subject_str):
        # For some reason that isn't quite clear, emailing detail subjects
        # seems to result in the links being malformed in a way they cannot
        # be resolved on the server. Email clients seem to play with the
        # encoding of subjects when they are copy/pasted or followed, and when
        # they resolve they may have one slash removed (eg globus:/foo/bar.txt)
        # This makes sure we send a fully unquoted and proper globus:// subject
        # to Globus Search.
        uq_sub = unquote_plus(unquote_plus(subject_str))
        bad_url = (uq_sub.startswith('globus:/')
                   and not uq_sub.startswith('globus://'))
        # Note: No subject *should* ever start with globus:/
        # All Globus Search subjects are encouraged to be URLs, so the sub will
        # always look like "something://". "globus://" is the most common with
        # pilot contstructing them.
        if bad_url:
            uq_sub = uq_sub.replace('globus:/', 'globus://')
        return uq_sub

    def get_context_data(self, index, project, subject):
        clean_sub = self.clean_subject(subject)
        context = get_subject(index, clean_sub, self.request.user)
        context.update(self.get_project_context(self.request, index, project))
        return context

    def get(self, request, index, project, subject):
        context = self.get_context_data(index, project, subject)
        return render(request, get_template(index, self.template), context)
