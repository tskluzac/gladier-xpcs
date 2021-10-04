import os
from urllib.parse import urlsplit, urlencode, urlunsplit


def search_results(result):

    return {}


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


def project_metadata(result):
    return result[0]['project_metadata']


def fetch_all_previews(result):
    # Gather base previews from the remote file manifest
    base_previews = {
        entry['url']: {
            'caption': get_xpcs_field_title(entry['filename'].rstrip('png'),
                                            ''),
            'name': get_xpcs_field_title(entry['filename'], ''),
            'url': entry['url'],
            'filename': entry['filename'],
        } for entry in result[0].get('files', {})
        if 'image' in entry.get('mime_type')}
    # If the user provided 'preview' info, overwrite the manifest entry with
    # the 'preview' entry
    base_previews.update(
        {entry['url']: entry
         for entry in result[0]['project_metadata'].get('preview', {})})
    # Add a preview id. The preview id is used by a javascript library to
    # determine how the data should be fetched/displayed.
    previews = list(base_previews.values())
    for idx, preview in enumerate(previews):
        preview['id'] = idx
    return sorted(previews, key=lambda p: p['url'], reverse=False)


def get_full_description(result):
    try:
        return result[0]['dc']['descriptions'][0]['description']
    except KeyError:
        return ''


def get_truncated_description(result):
    size_limit = 100
    try:
        desc = get_full_description(result)
        if len(desc) > size_limit:
            desc = desc[:size_limit]
            desc += '...'
        return desc
    except Exception:
        pass


def get_file(result):
    if result[0].get('remote_file_manifest'):
        return result[0]['remote_file_manifest']
    elif result[0].get('files'):
        return result[0]['files'][0]
    return {}


def remote_file_manifest(result):
    return result[0].get('files')


def filename(result):
    return get_file(result)['filename']


def https_url(result):
    rfm = get_file(result)
    if rfm and rfm.get('url'):
        gurl = urlsplit(rfm.get('url'))
        return urlunsplit(
            ('https',
             'e55b4eab-6d04-11e5-ba46-22000b92c6ec.e.globus.org',
             gurl.path,
             '', '')
            )


def globus_app_link(result):
    rfm = get_file(result)
    if rfm and rfm.get('url'):
        gurl = urlsplit(os.path.dirname(rfm.get('url')))
        query_params = {'origin_id': gurl.netloc.replace('.e.globus.org', ''),
                        'origin_path': gurl.path}
        return urlunsplit(('https', 'app.globus.org', 'file-manager',
                           urlencode(query_params), ''))


def title(result):
    return result[0]['dc']['titles'][0]['title']


def field_metadata(result):
    metadata = get_file(result).get('field_metadata')
    if not metadata:
        return {}

    labels = metadata.get('labels', {})
    label_headers = [
        {'field': 'name', 'name': labels.get('name'), 'type': 'str'},
        {'field': 'reference', 'name': 'Reference', 'type': 'url'},
        # {'field': 'description', 'name': metadata['labels']['description']},
        # {'field': 'format', 'name': metadata['labels']['format']},
        {'field': 'type', 'name': labels.get('type'), 'type': 'str'},
        {'field': 'count', 'name': 'Count', 'type': 'int'},
        {'field': 'frequency', 'name': 'Frequency', 'type': 'int'},
        {'field': 'top', 'name': 'Top', 'type': 'str'},
        {'field': 'unique', 'name': 'Unique Items', 'type': 'int'},

        {'field': 'min', 'name': 'Minimum', 'type': 'float'},
        {'field': 'max', 'name': 'Maximum', 'type': 'float'},
        {'field': 'mean', 'name': 'Mean', 'type': 'float'},
        {'field': 'std', 'name': 'Standard Deviation', 'type': 'float'},
        {'field': '25', 'name': '25th Percentile', 'type': 'float'},
        {'field': '50', 'name': '50th Percentile', 'type': 'float'},
        {'field': '75', 'name': '75th Percentile', 'type': 'float'},
    ]

    if result[0]['project_metadata'].get('dataframe_type') == 'Matrix':
        # Remove 'reference' line
        label_headers.pop(1)
    metadata['label_headers'] = label_headers

    field_data = []
    for row in label_headers:
        row_data = [{'field': row['field'], 'value': row['name']}]
        for column in metadata.get('field_definitions', []):
            row_data.append({
                'field': row['field'],
                'value': column.get(row.get('field', '')),
                'type': row.get('type')
            })
        field_data.append(row_data)

    # It's possible we won't get any usable data from the fields. Metadata may
    # only be constrained to images, and we don't want to display that for
    # xpcs.
    data_exists = bool([row for row in field_data if len(row) > 1])
    if data_exists is False:
        return {}
    return {'fields': field_data}
