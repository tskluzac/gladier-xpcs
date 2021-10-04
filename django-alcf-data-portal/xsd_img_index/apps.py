from django.apps import AppConfig
from xsd_img_index import fields


class XsdImgIndexConfig(AppConfig):
    name = 'xsd_img_index'


SEARCH_INDEXES = {
    'xsd-img': {
        'uuid': '75edd92c-d448-4c39-af69-e5c72911e3c7',
        'description': 'The IMG group designs, supports, and operates '
                       'state-of-the-art x-ray instrumentation and scientific '
                       'software for 2-D and 3-D full-field imaging.',
        'name': 'X-ray Science Division Imaging',
        'access': 'private',
        # 'tagline': 'APS Beamline Data',
        'group': '',
        'template_override_dir': 'xsd_img_index',
        'tabbed_project': True,
        'fields': [
            ('title', fields.title),
            ('truncated_description',
             fields.get_truncated_description),
            ('description', fields.get_full_description),
            ('search_results', fields.search_results),
            ('detail_field_groups', fields.selected_field_groups),
            ('cherry_picked_detail', fields.cherry_picked_detail),
            ('globus_app_link', fields.globus_app_link),
            ('filename', fields.filename),
            ('remote_file_manifest',
             fields.remote_file_manifest),
            'dc',
            ('https_url', fields.https_url),
            ('copy_to_clipboard_link', fields.https_url),
            ('resource_server', lambda r: 'petrel_https_server'),
        ],
        'facets': [
            {
                "name": "Creator",
                "field_name": "dc.creators.creatorName",

            },
            {
                "name": "Experimenter",
                "field_name": r"project_metadata.measurement\."
                              r"sample\.experimenter\.name",
            },
            {
                "name": "Affiliation",
                "field_name": r"project_metadata.measurement\."
                              r"sample\.experimenter\.affiliation",
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
