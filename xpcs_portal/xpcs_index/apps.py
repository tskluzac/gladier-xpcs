import os
# from django.conf import settings
from django.apps import AppConfig
from xpcs_portal.xpcs_index import fields

APP_DIR = os.path.join(os.path.dirname(__file__))


class XPCSIndexConfig(AppConfig):
    name = 'xpcs_portal.xpcs_index'


GLADIER_CFG = os.path.abspath(os.path.join(APP_DIR, 'gladier.cfg'))
RESOURCE_SERVER = 'petrel_https_server'
# RESOURCE_SERVER = 'c7683485-3c3f-454a-94c0-74310c80b32a'

SEARCH_INDEXES = {
    'xpcs': {
        'uuid': '344688c6-cff6-49c7-9bc5-e2fa3c5fedd2',
        'name': 'Petrel Users: XPCS ',
        # 'tagline': 'APS Beamline Data',
        'group': '',
        'tabbed_project': True,
        'access': 'private',
        'template_override_dir': 'xpcs',
        'description': (
            'Select this project to participate in Petrel User Study for XPCS team members (IRB No. XXX)'
        ),
        'fields': [
            ('title', fields.title),
            ('truncated_description',
             fields.get_truncated_description),
            ('description', fields.get_full_description),
            ('search_results', fields.search_results),
            ('detail_field_groups', fields.detail_field_groups),
            ('field_metadata', fields.field_metadata),
            ('globus_app_link', fields.globus_app_link),
            ('filename', fields.filename),
            ('remote_file_manifest',
             fields.remote_file_manifest),
            ('cherry_picked_detail', fields.cherry_picked_detail),
            'dc',
            'ncipilot',
            ('https_url', fields.https_url),
            ('copy_to_clipboard_link', fields.https_url),
            ('resource_server', lambda r: RESOURCE_SERVER),
            ('project_metadata', fields.project_metadata),
            ('all_preview', fields.fetch_all_previews),
            ('listing_preview', fields.listing_preview),
            ('total_intensity_vs_time_preview',
             fields.total_intensity_vs_time_preview),
            ('correlation_plot_previews',
             fields.correlation_plot_previews),
            ('correlation_plot_with_fit_previews',
             fields.correlation_plot_with_fit_previews),
            ('intensity_plot_previews', fields.intensity_plot_previews),
            ('structural_analysis_prev', fields.structural_analysis_prev),
        ],
        'facets': [
            {
                "name": "Creator",
                "field_name": "dc.creators.creatorName",

            },
            {
                "name": "Parent Folder",
                "field_name": "project_metadata.parent",
            },
            {
                "name": "APS Cycle",
                "field_name": "project_metadata.cycle",
            },
            {
                "name": "Dates",
                "field_name": "dc.dates.date",
                "type": "date_histogram",
                "date_interval": "day",
            },
            {
                "name": "Qmap",
                "field_name": "project_metadata.reprocessing.qmap.name",
            },
            {
                "name": "Reprocessed Datasets",
                "field_name": "project_metadata.reprocessing.suffix",
            },
        ],
    }
}
