import os
from django.apps import AppConfig
from exalearn_index import exalearn_fields

APP_DIR = os.path.join(os.path.dirname(__file__))


class ExalearnIndexConfig(AppConfig):
    name = 'exalearn_index'


COSMOFLOW_FACETS = [
    {
        'name': 'Omega M',
        'field_name': 'project_metadata.omega_m_phys',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 0.0,
            'high': .40
        }
    },
    {
        'name': 'Sigma 8',
        'field_name': 'project_metadata.sigma_8_phys',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': .5,
            'high': 1.1
        }
    },
    {
        'name': 'N Spec',
        'field_name': 'project_metadata.nspec_phys',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': .65,
            'high': 1.3
        }
    },
    {
        'name': 'H0',
        'field_name': 'project_metadata.h0_phys',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 40,
            'high': 100
        }
    },
    {
        'name': 'Projections',
        'field_name': 'project_metadata.projections',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 1,
            'high': 1000
        }
    },
    {
        'name': 'Sample',
        'field_name': 'project_metadata.sample',
    },
    {
        'name': 'Algorithm',
        'field_name': 'project_metadata.algorithm',
    },
]

INVERSE_FACETS = [
    {
        'name': 'Instrument',
        'field_name': 'project_metadata.instrument',
    },
    {
        'name': 'Symmetry',
        'field_name': 'project_metadata.symmetry',
    },
    {
        'name': 'Material',
        'field_name': 'project_metadata.material',
    },
    {
        'name': 'Alpha Minimum',
        'field_name': 'project_metadata.ranges.alphamin',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 40,
            'high': 100
        }
    },
    {
        'name': 'Alpha Maximum',
        'field_name': 'project_metadata.ranges.alphamax',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 0,
            'high': 300
        }
    },
    {
        'name': 'Beta Minimum',
        'field_name': 'project_metadata.ranges.betamin',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 0,
            'high': 100
        }
    },
    {
        'name': 'Beta Maximum',
        'field_name': 'project_metadata.ranges.betamax',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 0,
            'high': 300
        }
    },
    {
        'name': 'Gamma Minimum',
        'field_name': 'project_metadata.ranges.gammamin',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 0,
            'high': 100
        }
    },
    {
        'name': 'Gamma Maximum',
        'field_name': 'project_metadata.ranges.gammamax',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 0,
            'high': 300
        }
    },
    {
        'name': 'A Minimum',
        'field_name': 'project_metadata.ranges.amin',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 0,
            'high': 100
        }
    },
    {
        'name': 'A Maximum',
        'field_name': 'project_metadata.ranges.amax',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 0,
            'high': 300
        }
    },
    {
        'name': 'B Minimum',
        'field_name': 'project_metadata.ranges.bmin',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 0,
            'high': 100
        }
    },
    {
        'name': 'B Maximum',
        'field_name': 'project_metadata.ranges.bmax',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 0,
            'high': 300
        }
    },
    {
        'name': 'C Minimum',
        'field_name': 'project_metadata.ranges.cmin',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 0,
            'high': 100
        }
    },
    {
        'name': 'C Maximum',
        'field_name': 'project_metadata.ranges.cmax',
        'type': 'numeric_histogram',
        'size': 10,
        'histogram_range': {
            'low': 0,
            'high': 300
        }
    },
]

RESOURCE_SERVER = 'petrel_https_server'

SEARCH_INDEXES = {
    'exalearn': {
        'uuid': 'be69a351-f893-4268-8647-70bcb06fcd00',
        'name': 'ExaLearn',
        'description':
            'ExaLearn is a US Department of Energy (DOE) Exascale Computing '
            'Project (ECP) center developing and applying machine learning '
            'methods in high-performance computing environments',
        'access': 'public',
        'tagline': 'Data for Extreme-Scale Learning',
        'group': '17cf9883-6857-11e9-8b39-0e4a32f5e3b8',
        'resource_server': 'petrel_https_server',
        'template_override_dir': 'exalearn',
        'fields': [
            ('search_results', exalearn_fields.search_results),
            ('detail_results', exalearn_fields.detail_results),
            ('file_size', exalearn_fields.file_size),
            ('title', exalearn_fields.title),
            ('filename', lambda r: os.path.basename(
                exalearn_fields.https_url(r))
             ),
            ('https_url', exalearn_fields.https_url),
            ('detail_preview_images', exalearn_fields.detail_preview_images),
            ('search_preview_image', exalearn_fields.search_preview_image),
            ('copy_to_clipboard_link', exalearn_fields.globus_app_link),
            ('remote_file_manifest', exalearn_fields.remote_file_manifest),
            ('is_inverse_preview', exalearn_fields.is_inverse_preview),
            'dc',
            'cosmo',
            'project_metadata',
        ],
        'facets': [
            # TODO: This is currently broken. It "works" in that it returns
            # facets, but DGPF cannot currently filter on them.
            # {
            #     'name': 'Date Created',
            #     'field_name': 'project_metadata.gmeta_dates.created',
            #     'type': 'date_histogram',
            #     'histogram_range': {
            #         'low': '2000-01-01',
            #         'high': '2020-01-01'
            #     },
            #     'date_interval': 'month'
            # }
        ] + COSMOFLOW_FACETS + INVERSE_FACETS,
        'filter_match': 'match-any',
    }
}
