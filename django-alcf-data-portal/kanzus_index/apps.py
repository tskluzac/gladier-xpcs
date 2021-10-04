import os
from django.apps import AppConfig
from kanzus_index import fields

APP_DIR = os.path.join(os.path.dirname(__file__))


class KanzusIndexConfig(AppConfig):
    name = 'kanzus_index'


REPROCESSING_TASK_FLOW = os.path.join(
    APP_DIR, 'flows/reprocessing_flow_definition.json'
)
REPROCESSING_TASK_GROUP = 'e31ed13f-e9e0-11e9-bbd0-0a8c64af9bb2'

SEARCH_INDEXES = {
    'kanzus': {
        'uuid': '5e63bb08-5b39-4a02-86f3-44cec03e8bc0',
        'name': 'Kanzus Beamline Chip Analysis',
        'description':
            'Synchrotron serial crystallography for the study of protein and '
            'enzyme dynamic processes',
        # 'tagline': 'APS Beamline Data',
        'access': 'private',
        'tabbed_project': True,
        'group': 'e31ed13f-e9e0-11e9-bbd0-0a8c64af9bb2',
        'template_override_dir': 'kanzus',
        'fields': [
            ('title', fields.title),
            ('truncated_description',
             fields.get_truncated_description),
            ('description', fields.get_full_description),
            ('search_results', fields.search_results),
            ('detail_results', fields.detail_results),
            ('project_metadata', fields.project_metadata),
            # ('detail_field_groups', fields.detail_field_groups),
            # ('field_metadata', fields.field_metadata),
            ('globus_app_link', fields.globus_app_link),
            ('filename', fields.filename),
            ('remote_file_manifest',
             fields.remote_file_manifest),
            # ('cherry_picked_detail', fields.cherry_picked_detail),
            'dc',
            ('batch_runs', fields.get_batch_run_info),
            'ncipilot',
            ('https_url', fields.https_url),
            ('https_url_filename', fields.https_url_filename),
            ('listing_preview_filename', fields.listing_preview_filename),
            ('copy_to_clipboard_link', fields.https_url),
            ('resource_server',
             lambda r: 'c7683485-3c3f-454a-94c0-74310c80b32a'),
            ('all_preview', fields.fetch_all_previews),
            ('listing_preview', fields.listing_preview),
            ('other_previews', fields.other_previews),
            ('non_composite_batch_previews',
             fields.latest_non_composite_batch_previews),
            ('latest_date', fields.latest_date),
        ],
        'sort': [
            {'field_name': 'dc.dates.date', 'order': 'desc'}
        ],
        'facets': [
            {
                "name": "Run",
                "field_name": "project_metadata.run_name",
            },
            {
                "name": "Date Processed",
                "field_name": "dc.dates.date",
                "type": "date_histogram",
                "date_interval": "year",
            },
            {
                "name": "Protein",
                "field_name": "project_metadata.protein",
            },
            {
                "name": "CBF Files",
                "field_name": "project_metadata.batch_info.cbf_files",
                "type": "numeric_histogram",
                "histogram_range": {"low": 0, "high": 100000},
                "size": 100,
            },
            {
                "name": "Number of Ints",
                "field_name": "project_metadata.batch_info."
                              "total_number_of_int_files",
                "type": "numeric_histogram",
                "histogram_range": {"low": 0, "high": 10000},
                "size": 100,
            },
            {
                "name": "Hit Rate",
                "field_name": "project_metadata.batch_info.hit_rate",
                "type": "numeric_histogram",
                "histogram_range": {"low": 0, "high": 100},
                "size": 100,
            },
        ]
    }
}
