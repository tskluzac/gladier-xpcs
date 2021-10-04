import statistics
import logging
from urllib.parse import unquote_plus
from django.urls import reverse
from django.conf import settings
from alcf_data_portal.views import ProjectSearch, ProjectDetail
from kanzus_index import models

log = logging.getLogger(__name__)


class KanzusExtendedMetadataSearch(ProjectSearch):
    """
    Generate some statistics using Globus Search Facets. The 'stat' facets are
    removed and not shown directly to the user, with the generated data being
    shown elsewhere on the search page.
    """
    METADATA_FACETS = ['CBF Files', 'Number of Ints', 'Hit Rate']

    def get_context_data(self, index):
        facet_names = {f.get('name')
                       for f in settings.SEARCH_INDEXES['kanzus']['facets']}
        assert set(self.METADATA_FACETS).issubset(facet_names), \
            (f'Metadata facets do not match configured facets: '
             f'{self.METADATA_FACETS}')

        context = super().get_context_data(index)
        facets_by_name = {f['name']: f for f in context['search']['facets']}
        metadata_facets = [facets_by_name.pop(f)
                           for f in list(facets_by_name.keys())
                           if f in self.METADATA_FACETS]
        # Remove the 'metadata stat' facets from the normal list of facets
        context['search']['facets'] = list(facets_by_name.values())
        context['search']['search_statistics'] = \
            self.get_facet_stats(metadata_facets)
        return context

    def get_facet_stats(self, facets):
        stats = []
        facets_by_name = {f['name']: f for f in facets}
        for name in self.METADATA_FACETS:
            if not facets_by_name.get(name):
                continue
            buckets = facets_by_name[name]['buckets']
            vals = [sum([float(num) for num in b['value'].split('--')]) / 2
                    for b in buckets if '*' not in b['value']]
            stats.append({'name': name, 'value': statistics.mean(vals)})
        return stats


class KanzusDetail(ProjectDetail):

    def get_absolute_url(self):
        return reverse('tp-project-detail',
                       kwargs={'index': self.kwargs['index'],
                               'project': self.kwargs['project'],
                               'subject': self.kwargs['subject']})

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(self.reprocessing_context(context))
        return context

    def can_reprocess(self):
        return models.SampleReprocess.is_authorized(self.request.user)

    def get_reprocessing_tasks(self):
        sub = unquote_plus(unquote_plus(self.kwargs['subject']))
        return models.SampleReprocess.objects.filter(subject=sub,
                                                     action__status='ACTIVE')

    def reprocessing_context(self, context):
        return {
            'can_reprocess': self.can_reprocess(),
            'reprocessing_tasks': self.get_reprocessing_tasks(),
        }
