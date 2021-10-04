import os
import pytz
from django.conf import settings
import datetime
from copy import deepcopy
from urllib.parse import urlsplit, urlencode, urlunsplit

LISTING_PREVIEW = 'composite.png'
INTS_FILE = '_ints.txt'
PETREL_HTTP_SUFFIX = '.e.globus.org'  # Old petrel suffix
archive_mime_types = ['application/x-tar', 'application/zip']

BATCH_FIELDS = [
        {'field': 'batch_number', 'name': 'Batch Number'},
        {'field': 'cbf_files', 'name': 'CBFs Processed'},
        {'field': 'cbf_file_range', 'name': 'CBF Range', 'type': 'range'},
        {'field': 'total_number_of_int_files', 'name': 'Ints'},
        {'field': 'hit_rate', 'name': 'Hit Rate', 'type': 'percentage'},
        {'field': 'image', 'type': 'image', 'name': 'batch_run'}
    ]


def search_results(result):
    rfm_size = [
        # {'field': 'length', 'name': 'Size', 'type': 'filesize'}
    ]
    # beam_input = result[0]['project_metadata'].get('beamline_input', {})
    # xsteps, ysteps = beam_input.get('x_n_steps'), beam_input.get('y_n_steps')
    # shape = (xsteps, ysteps)
    project_fields = [
        {'field': 'chip', 'name': 'Chip'},
        {'field': 'protein', 'name': 'Protein'},
        {'field': 'protein_hash', 'name': 'Protein Hash'}
    ]
    populated_fields = (
        # get_fields(project_metadata_fields, result[0]['project_metadata']) +
        get_fields(rfm_size, get_file(result)) +
        # [{'field': 'beamline_input', 'name': 'Input Shape',
        #   'value': shape}] +
        get_fields(project_fields, result[0].get('project_metadata'))
        )
    return populated_fields + batch_info(result)


def latest_date(result):
    # dc.dates.date
    latest = result[0]['dc']['dates'][-1]
    date_str = latest['date']
    dt = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    user_tz = pytz.timezone(settings.TIME_ZONE)
    latest['date'] = user_tz.fromutc(dt)
    return latest


def batch_info(result):
    batches = deepcopy(result[0]['project_metadata'].get('batch_info', {}))
    fields = [
        {'field': 'cbf_files', 'name': 'CBFs Processed'},
        {'field': 'cbf_file_range', 'name': 'CBF Range', 'type': 'range'},
        {'field': 'total_number_of_int_files', 'name': 'Ints'},
        {'field': 'hit_rate', 'name': 'Hit Rate', 'type': 'percentage'}
        ]
    return get_fields(fields, batches)


def detail_results(result):
    user_input = result[0]['project_metadata'].get('user_input', {})
    shape = (user_input.get('x_num_steps', user_input.get('y_num_steps')))

    detail_fields = [
        {'field': 'beamline_input', 'name': 'Input Shape', 'value': shape},
    ]
    crystal_fields = [
        {'field': 'targetAnnotation', 'name': 'Annotation'},
        {'field': 'crystallographer', 'name': 'Crystallographer'}
    ]
    crystal_record = result[0]['project_metadata'].get('crystal_record', [{}])
    return (search_results(result) +
            detail_fields +
            get_fields(crystal_fields, crystal_record[0])
            )


def get_fields(fields, result):
    """Takes a list of dictionaries describing data to fetch, and searches
    for matches in the given result (can be any dict). If a result is not found
    no entry is placed in the return data."""
    populated_fields = []
    field_list = deepcopy(fields)
    for field in field_list:
        if result.get(field['field']):
            field['value'] = result.get(field['field'])
            populated_fields.append(field)
    return populated_fields


def project_metadata(result):
    return result[0].get('project_metadata', {})


def get_batch_run_info(result):
    return []
    # batches = deepcopy(result[0]['project_metadata']['batches'])
    # files = {os.path.basename(f['url']): f for f in other_previews(result)}
    # for b in batches:
    #     b['hit_rate'] = b['total_number_of_int_files'] / b['cbf_files'] * 100
    #     b['image'] = files[b['filename']]['id']
    # return [get_fields(BATCH_FIELDS, vals) for vals in batches]


def get_xpcs_field_title(field_name, prefix):
    parts = field_name.replace(prefix, '').split('.')
    parts = [p.split('_') for p in parts]
    # Flatten the list, from attempting to split into lists twice.
    parts = [item for sublist in parts for item in sublist]
    return ' '.join([p.capitalize() for p in parts])


def listing_preview(result):
    for entry in fetch_all_previews(result):
        if entry['url'].endswith(LISTING_PREVIEW):
            return entry


def ints_preview(result):
    for entry in fetch_all_previews(result):
        if entry['url'].endswith(INTS_FILE):
            return entry


def get_archives(result):
    return [e for e in fetch_all_previews(result) if e['mime_type'] in archive_mime_types]


def other_previews(result):
    """Batches are everything except the listing preview
    (and also not the listing image). """
    other_prevs = (
        [listing_preview(result)] +
        non_composite_batch_previews(result) +
        [ints_preview(result)] +
        get_archives(result)
    )
    other_urls = [p['url'] for p in other_prevs if p]
    previews = [entry for entry in fetch_all_previews(result)
                if entry['url'] not in other_urls]
    return previews


def non_composite_batch_previews(result):
    return [
        entry for entry in fetch_all_previews(result)
        if os.path.basename(entry.get('url', '')).startswith('1int-sinc-')
    ]


def latest_non_composite_batch_previews(result):
    non_composites = non_composite_batch_previews(result)
    non_composites.sort(reverse=True, key=lambda x: x['url'])
    return non_composites[0:2]


def fetch_all_previews(result):
    # Gather base previews from the remote file manifest
    base_previews = {
        entry['url']: {
            'caption': get_xpcs_field_title(entry['filename'].rstrip('png'),
                                            ''),
            'name': get_xpcs_field_title(entry['filename'], ''),
            'url': entry['url'],
            'mime_type': entry.get('mime_type')
        } for entry in result[0]['files']}
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
    for z in get_archives(result):
        if z['mime_type'] in archive_mime_types:
            return z['url']

    ints = ints_preview(result) or {}
    return ints.get('url')


def https_url_filename(result):
    url = https_url(result)
    if url:
        return os.path.basename(url)


def listing_preview_filename(result):
    return os.path.basename(listing_preview(result)['url'])


def globus_app_link(result):
    rfm = get_file(result)
    if rfm and rfm.get('url'):
        gurl = urlsplit(os.path.dirname(rfm.get('url')))
        if PETREL_HTTP_SUFFIX in gurl.netloc:
            origin_id = gurl.netloc.replace(PETREL_HTTP_SUFFIX, '')
        else:
            origin_id = 'c7683485-3c3f-454a-94c0-74310c80b32a'
        query_params = {'origin_id': origin_id, 'origin_path': gurl.path}
        return urlunsplit(('https', 'app.globus.org', 'file-manager',
                           urlencode(query_params), ''))


def title(result):
    return result[0]['dc']['titles'][0]['title']
