import os
# from django.conf import settings
from django.apps import AppConfig
from xrf_2id_index import fields

APP_DIR = os.path.join(os.path.dirname(__file__))


class Xrf2IdIndexConfig(AppConfig):
    name = 'xrf_2id_index'


SEARCH_INDEXES = {
    '2id_xrf': {
        'uuid': 'aeda697d-18e2-40d9-a4bf-1d97543bc632',
        'name': 'APS 2ID XRF',
        'tagline': 'APS Beamline Data',
        'description': 'X-Ray fluorescence imaging for a variety of '
                       'applications',
        'group': '',
        'tabbed_project': True,
        'access': 'private',
        'template_override_dir': 'xrf_2id_index',
        # 'description': 'no description yet',
        'fields': [
            ('title', fields.title),
            ('truncated_description',
             fields.get_truncated_description),
            ('description', fields.get_full_description),
            ('search_results', fields.search_results),
            ('globus_app_link', fields.globus_app_link),
            ('filename', fields.filename),
            ('remote_file_manifest',
             fields.remote_file_manifest),
            'dc',
            ('https_url', fields.https_url),
            ('copy_to_clipboard_link', fields.https_url),
            ('resource_server', lambda r: RESOURCE_SERVER),
        ],
        'facets': [
            {
                "name": "Creator",
                "field_name": "dc.creators.creatorName",

            },
            {
                "name": "Formats",
                "field_name": "dc.formats",
            },
            {
                "name": "Dates",
                "field_name": "dc.dates.date",
                "type": "date_histogram",
                "date_interval": "day",
            },

        ],
        # 'result_format_version': '2019-08-27',
    }
}
