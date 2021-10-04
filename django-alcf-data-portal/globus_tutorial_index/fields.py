import os
from urllib.parse import urlsplit, urlencode, urlunsplit

PETREL_HTTP_SUFFIX = '.e.globus.org'  # Old petrel suffix


def title(result):
    """Title for a search result"""
    try:
        return result[0]['title']
    except KeyError:
        return 'Result'


def search_results(result):
    fields = [
        {'field': 'date', 'name': 'Date'},
        {'field': 'identifier', 'name': 'Identifier'},
    ]
    return get_fields(fields, result[0])


def get_fields(fields, result):
    """Takes a list of dictionaries describing data to fetch, and searches
    for matches in the given result (can be any dict). If a result is not found
    no entry is placed in the return data."""
    populated_fields = []
    for field in fields:
        if result.get(field['field']):
            field['value'] = result.get(field['field'])
            populated_fields.append(field)

    return populated_fields

def remote_file_manifest(result):
    return result[0].get('files', [])


def get_rfm_path(result):
    rfm = remote_file_manifest(result)
    if rfm and rfm[0].get('url'):
        return urlsplit(rfm[0]['url']).path


def https_url(result):
    return 'https://b18709.69a6.dn.glob.us/ssx/Plague1_images/prime.zip'


def https_url_filename(result):
    return os.path.basename(https_url(result))


def globus_app_link(result):
    rfm = remote_file_manifest(result)[0]
    if rfm and rfm.get('url'):
        gurl = urlsplit(os.path.dirname(rfm.get('url')))
        # Petrel#testbed
        origin_id = 'e56c36e4-1063-11e6-a747-22000bf2d559'
        query_params = {'origin_id': origin_id, 'origin_path': gurl.path}
        return urlunsplit(('https', 'app.globus.org', 'file-manager',
                           urlencode(query_params), ''))
