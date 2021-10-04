from django.apps import AppConfig
from globus_tutorial_index import fields


class LoganIndexConfig(AppConfig):
    name = 'globus_tutorial_index'


SEARCH_INDEXES = {
    'globus-tutorial': {
        # No single uuid is configured for this project. Instead, it scans a users indices
        # and chooses one to use
        'uuid': 'multi-index-project',
        'name': 'Globus Tutorial',
        'description': 'A simple portal to learn more about how Globus Search works.',
        'access': 'public',
        # This allows for the 'project' page layout, required for using pilot.
        'tabbed_project': False,
        # Your project's group uuid
        'group': 'e31ed13f-e9e0-11e9-bbd0-0a8c64af9bb2',
        # This tells the portal where to replace the base templates with your custom ones.
        # Typically the name of the project
        'template_override_dir': 'globus_tutorial_index',
        'fields': [
            ('title', fields.title),
            ('search_results', fields.search_results),
            # ('detail_results', fields.detail_results),
            # ('project_metadata', fields.project_metadata),
            ('globus_app_link', fields.globus_app_link),
            # 'dc',
            # ('https_url', fields.https_url),
            # ('https_url_filename', fields.https_url_filename),
            # ('copy_to_clipboard_link', fields.https_url),
            # List any data you want to use in your search results
            ('remote_file_manifest', fields.remote_file_manifest),
            ('globus_http_endpoint', lambda x: 'testbed.petrel.host'),
            ('globus_http_scope', lambda x: 'petrel_https_server'),
            ('globus_http_path', fields.get_rfm_path),
        ],
        'facets': [
            {
                "name": "Dates",
                "field_name": "date",
                "type": "date_histogram",
                "date_interval": "day",
            },
            {
                "name": "Contributors",
                "field_name": "contributors",
            },
            {
                "name": "Keywords",
                "field_name": "keywords",
            },
        ]
    }
}
