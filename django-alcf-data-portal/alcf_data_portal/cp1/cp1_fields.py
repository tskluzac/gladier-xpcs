import os
from urllib.parse import urlsplit, urlencode, urlunsplit


def search_results(result):
    tsv_stats = [
        {'field': 'numrows', 'name': 'Row Count', 'type': 'int'},
        {'field': 'numcols', 'name': 'Column Count', 'type': 'int'},
    ]
    project_metadata_fields = [
        {'field': 'data_type', 'name': 'Data Type'},
        {'field': 'dataframe_type', 'name': 'Dataframe Type'},
    ]
    rfm_size = [
        {'field': 'length', 'name': 'Size', 'type': 'filesize'}
    ]
    populated_fields = (
        get_fields(tsv_stats, get_file(result)['field_metadata']) +
        get_fields(project_metadata_fields, result[0]['project_metadata']) +
        get_fields(rfm_size, get_file(result))
        )
    return populated_fields


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
    """
    Get a remote file manifest for all files associated with this search record
    files containing 'metadata' within their filename are pushed to the top
    to be displayed first, and the list is cutoff at 10 files.
    """
    files = result[0].get('files', [])
    m_f = [idx for idx, fdict in enumerate(files)
           if 'metadata' in fdict.get('filename', '')]
    metadata_files = [files.pop(x) for x in reversed(m_f)]
    metadata_files.extend(files)
    files = metadata_files[:10]

    for entry in files:
        entry['field_metadata'] = field_metadata(entry)
        # Fetch previewbytes if it exists
        if entry['field_metadata']:
            pb = entry['field_metadata'][0].get('previewbytes')
            entry['previewbytes'] = pb
    return files


def filename(result):
    return get_file(result)['filename']


def https_url(result):
    rfm = get_file(result)
    if rfm and rfm.get('url'):
        gurl = urlsplit(rfm.get('url'))
        return urlunsplit(
            ('https',
             'ebf55996-33bf-11e9-9fa4-0a06afd4a22e.e.globus.org',
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


def field_metadata(manifest_entry, dataframe_type='List'):
    metadata = manifest_entry.get('field_metadata')
    if not metadata:
        return []
    elif isinstance(metadata, dict):
        metadata = [metadata]

    headers = [
        {'field': 'name', 'name': 'Column Name', 'type': 'str'},
        {'field': 'reference', 'name': 'Reference', 'type': 'url'},
        # {'field': 'description', 'name': meta['labels']['description']},
        # {'field': 'format', 'name': meta['labels']['format']},
        {'field': 'type', 'name': 'Data Type', 'type': 'str'},
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

    dataframe_field_metadata = []
    for meta in metadata:
        dataframe_headers = headers.copy()
        if dataframe_type == 'Matrix':
            # Remove 'reference' line
            dataframe_headers.pop(1)

        field_metadata = {
            'fields': get_field_metadata_rows(meta, headers),
            'previewbytes': meta.get('previewbytes')
        }
        dataframe_field_metadata.append(field_metadata)
    return dataframe_field_metadata


def get_field_metadata_rows(metadata, headers):
    field_data = []
    for row in headers:
        row_data = [{'field': row['field'], 'value': row['name']}]
        for column in metadata['field_definitions']:
            row_data.append({
                'field': row['field'],
                'value': column.get(row.get('field', '')),
                'type': row.get('type')
            })
        field_data.append(row_data)
    return field_data
