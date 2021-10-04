import os
from django.apps import AppConfig
# from hedm_sec1_index import fields

APP_DIR = os.path.join(os.path.dirname(__file__))


class HEDMSec1IndexConfig(AppConfig):
    name = 'hedm_sec1_index'


RESOURCE_SERVER = 'petrel_https_server'

SEARCH_INDEXES = {
    'hedm-sec1': {
        'uuid': '9302766a-aefc-47e9-81d1-34a06f3508f3',
        'name': 'HEDM Section 1',
        'group': '3c4a53a5-76d7-11eb-9bcf-0ed81fece70f',
        'tabbed_project': True,
        'access': 'private',
        'template_override_dir': 'hedm_sec1_index',
        'description': (
            'We need to add a description.'
        ),
        'fields': [
            # ('title', fields.title),
            # ('truncated_description',
            #  fields.get_truncated_description),
            # ('description', fields.get_full_description),
            # ('search_results', fields.search_results),
            # ('detail_field_groups', fields.detail_field_groups),
            # ('field_metadata', fields.field_metadata),
            # ('globus_app_link', fields.globus_app_link),
            # ('filename', fields.filename),
            # ('remote_file_manifest',
            #  fields.remote_file_manifest),
            # ('cherry_picked_detail', fields.cherry_picked_detail),
            # 'dc',
            # 'ncipilot',
            # ('https_url', fields.https_url),
            # ('copy_to_clipboard_link', fields.https_url),
            # ('resource_server', lambda r: RESOURCE_SERVER),
            # ('project_metadata', fields.project_metadata),
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
