import logging
import json
import urllib
import re
from base64 import b64encode, b64decode
from django import forms
from django.template.defaultfilters import slugify
from globus_portal_framework.gsearch import (get_search_query,
                                             get_search_filters)
from concierge_app import models
from concierge_app.search import SearchCollector

log = logging.getLogger(__name__)

# Match only chars allowed in 'label'
# https://docs.globus.org/api/transfer/task_submit/#common_transfer_and_delete_fields  # noqa
ALLOWED_NAME_CHARACTERS = r'[\w,\-]'
# Only allow spaces, dashes, and non-symbols
MDF_ALLOWED_TITLE_CHARACTERS = r'[\w\- ]'


class UnboundMultipleChoiceField(forms.MultipleChoiceField):
    """Like MultipleChoiceField, but setting 'choices' is not required."""
    def valid_value(self, value):
        return True


class ManifestCheckoutForm(forms.Form):
    # Constants
    METADATA_FIELDS = ['search_url']
    ALLOWED_NAME_MATCHER = re.compile(ALLOWED_NAME_CHARACTERS)
    SEARCH_COLLECTOR_CLASS = SearchCollector

    # Fields
    index = forms.CharField(label='Index Name', min_length=1)
    name = forms.CharField(label='Manifest Name', min_length=1)
    project = forms.CharField(required=False)
    search_url = forms.CharField(label='Search URL')
    query = forms.CharField(label='Query')
    filters = forms.CharField(label='Filters')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.user = self.request.user if self.request else None
        self.search_url = kwargs.pop('search_url', '')
        self.index = kwargs.pop('index', '')
        self.project = kwargs.pop('project', '')
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial = self.get_initial_values()

    def get_search_collector_data(self):
        if self.is_bound:
            if self.is_valid():
                return self.cleaned_data
            else:
                return self.data
        else:
            return self.initial

    def get_search_collector(self):
        d = self.get_search_collector_data()
        filters = self.decode_filters(d.get('filters'))
        metadata = {f: d.get(f) for f in self.METADATA_FIELDS}
        index = d.get('index', self.index)
        name = d.get('name', f'{index}-collection')
        log.debug(f'Creating Search Collector: {self.SEARCH_COLLECTOR_CLASS}')
        return self.SEARCH_COLLECTOR_CLASS(
            index, name=name, query=d.get('query'), filters=filters,
            project=d.get('project'), search_data=None, user=self.user,
            metadata=metadata
        )

    def get_clean_search_collector(self):
        return self.SEARCH_COLLECTOR_CLASS(**self.cleaned_data)

    def get_initial_values(self):
        query = get_search_query(self.request)
        filters = get_search_filters(self.request)
        return {
            'index': self.index,
            'name': self.generate_name(self.index, query, filters),
            'project': self.project,
            'search_url': f'{self.search_url}?{self.request.GET.urlencode()}',
            'filters': self.encode_filters(filters),
            'query': query,
        }

    def clean_filters(self):
        try:
            return self.decode_filters(self.cleaned_data['filters'])
        except Exception as e:
            raise forms.ValdationError(f'Form Validation Error: {e}')

    def clean_name(self):
        valid_chars = [self.ALLOWED_NAME_MATCHER.match(c) for c in
                       self.cleaned_data['name']]
        if not all(valid_chars):
            hint = slugify(self.cleaned_data['name'])
            raise forms.ValidationError(
                f'This name contains characters which are not allowed. Please '
                f'only use words, spaces, and ",\\-" (HINT: {hint}).'
            )
        return self.cleaned_data['name']

    @staticmethod
    def encode_filters(filters=None):
        bfilters = bytes(json.dumps(filters or []), 'utf-8')
        return b64encode(bfilters).decode('utf-8')

    @staticmethod
    def decode_filters(filters):
        if filters and isinstance(filters, str):
            return json.loads(b64decode(filters))
        return []

    @classmethod
    def generate_name(cls, index, query, filters):
        """
        Generate a bag name based on a search query, index, and filters applied
        by the user. Returns a string.
        """
        name_chunks = []
        for filter in filters:
            try:
                name = filter['field_name'].split('.')[-1]
                if filter.get('type') == 'range':
                    for fval in filter['values']:
                        vfrom = ('*' if fval['from'] == '*'
                                 else f'{fval["from"]:.2f}')
                        vto = '*' if fval['to'] == '*' else f'{fval["to"]:.2f}'
                        val = f'{vfrom}--{vto}'.replace('*', 'all')
                        name_chunks.append(f'{name}-{val}')
                else:
                    val = ''.join(filter['values'])
                    name_chunks.append(f'{val}')
            except ValueError:
                pass
        bag_name = f'{index}' if query == '*' else f'{index}-{query}'
        if name_chunks:
            bag_name = f'{bag_name}-{"-".join(name_chunks)}'
        valid_chars = [c for c in bag_name
                       if cls.ALLOWED_NAME_MATCHER.match(c)]
        return ''.join(valid_chars)


class SubjectSelectManifestCheckoutForm(ManifestCheckoutForm):
    subjects = UnboundMultipleChoiceField(label='User Chosen Subjects')

    def get_search_collector(self):
        sc = super().get_search_collector()
        if not self.is_bound or not self.is_valid():
            return sc
        up = urllib.parse.unquote_plus
        subs = [up(up(s)) for s in self.cleaned_data['subjects']]
        filtered_search_data = filter(lambda r: r['subject'] in subs,
                                      sc.search_data['gmeta'])
        filtered_search_data = list(filtered_search_data)
        new_sdata = {
            'count': len(filtered_search_data),
            'total': len(filtered_search_data),
            'gmeta': filtered_search_data
        }
        log.debug(f'Filtered {len(sc.search_data["gmeta"])} subs to '
                  f'{len(filtered_search_data)}')
        sc.search_data = new_sdata
        return sc

    def clean_subjects(self):
        subs = self.cleaned_data['subjects']
        if not subs:
            raise forms.ValdationError(f'No Subjects Selected')
        for subject in subs:
            if not subject:
                raise forms.ValdationError(f'Invalid Subject: {subject}')
        return subs


class ManifestLimiterCheckoutForm(ManifestCheckoutForm):
    limit = forms.IntegerField(min_value=1, max_value=3000)

    def get_search_collector(self):
        sc = super().get_search_collector()
        if not self.is_bound or not self.is_valid():
            # Don't actually retrieve search results on the checkout page.
            # Only metadata about the search is needed.
            sc.search_kwargs['limit'] = 0
            return sc
        sc.search_kwargs['limit'] = self.cleaned_data['limit']
        return sc

    def clean_project(self):
        if not self.cleaned_data['project']:
            raise forms.ValidationError('This is a required Field')


class MDFCollectionSubmissionForm(forms.ModelForm):
    ALLOWED_TITLE_MATCHER = re.compile(MDF_ALLOWED_TITLE_CHARACTERS)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.index = kwargs.pop('index')
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = models.MDFCollectionSubmission
        fields = ['title', 'search_collection']

    def clean_title(self):
        valid_chars = [self.ALLOWED_TITLE_MATCHER.match(c) for c in
                       self.cleaned_data['title']]
        if not all(valid_chars):
            raise forms.ValidationError('No Symbols are allowed in titles')
        title = self.cleaned_data['title']
        # HACK -- Getting the MDF Forge client currently opens up the native
        # app view and stalls the current thread. Don't attempt to validate
        # this until we can get that fixed!
        # mdf = utils.get_mdf_forge_client(user=self.user)
        # source_name = self.Meta.model.get_source_name(title, self.index,
        #                                               self.project)
        # matches = (mdf.match_source_names(source_name)
        #            .match_resource_types("dataset").search())
        # if matches:
        #     raise forms.ValidationError(f'{title} has been taken, please '
        #                                 f'choose a different title.')
        return title

    def clean(self):
        col_m = self.cleaned_data.get('search_collection')
        if not col_m:
            raise forms.ValidationError('Search Collection is required')
        sc = self.cleaned_data['search_collection'].get_search_collector()
        has_subs = len(sc.get_subjects()) > 0
        has_sources = len(sc.get_sources()) > 0
        if sc.search_data and has_subs and has_sources:
            return self.cleaned_data
        raise forms.ValidationError('Search Collection missing data for '
                                    'publication')
