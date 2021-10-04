import os
from urllib.parse import urlsplit, urlencode, urlunsplit

LISTING_PREVIEW = 'scattering_pattern_log.png'


def search_results(result):
    dc_fields = [
        {'field': 'publicationYear', 'name': 'Publication Year'},
    ]
    project_metadata_fields = [
        {'field': 'measurement.instrument.acquisition.parent_folder',
         'name': 'Parent Folder'},
        {'field': 'measurement.sample.experimenter_name',
         'name': 'Experimenter'},
        {'field': 'measurement.sample.file_path', 'name': 'file_path'},
        {'field': 'exchange.data_dark', 'name': 'Data Dark'},
        {'field': 'exchange.data_white', 'name': 'Data White'},

    ]
    # project_metadata_fields = [{
    #     'field': k,
    #     'name': ' '.join([n.capitalize() for n in k.split('_')])}
    #     for k in result[0]['project_metadata'].keys()
    #     if k not in ['project-slug', 'preview']
    # ]
    rfm_size = [
        {'field': 'length', 'name': 'Size', 'type': 'filesize'}
    ]
    populated_fields = (
        get_fields(project_metadata_fields, result[0]['project_metadata']) +
        get_fields(dc_fields, result[0]['dc']) +
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


def get_field_title(field_name, prefix):
    parts = field_name.replace(prefix, '').split('.')
    parts = [p.split('_') for p in parts]
    # Flatten the list, from attempting to split into lists twice.
    parts = [item for sublist in parts for item in sublist]
    return ' '.join([p.capitalize() for p in parts])


def detail_field_groups(result):
    groups = [
        ('Exchange', 'exchange.'),
        ('Process Acquisition', 'process.acquisition'),
        ('Instrument Acquisition Measurements',
         'measurement.instrument.acquisition.'),
        ('Instrument Detector Measurements',
         'measurement.instrument.detector.'),
        ('Insturment General', 'measurement.instrument'),
        ('Measurement Sample', 'measurement.sample'),
        ('Instrument Source Begin Measurements',
         'measurement.instrument.source_begin.'),
    ]
    # Track used fields, we should display them in the first possible group,
    # but not repeat them in other groups.
    used_fields = []
    field_groups = []
    for name, group in groups:
        fields = [{
                'field': f,
                'type': 'float',
                'name': get_field_title(f, group),
                'value': v
            }
            for f, v in result[0]['project_metadata'].items()
            if f.startswith(group) and f not in used_fields
        ]
        used_fields += [f['field'] for f in fields]
        if fields:
            field_groups.append({'name': name, 'fields': fields})
    # not_used = [f for f in result[0]['project_metadata']
    #             if f not in used_fields]
    # from pprint import pprint
    # pprint(not_used)
    return field_groups


def cherry_picked_detail(result):
    selected = ['Measurement Sample']
    field_groups = detail_field_groups(result)
    cherries = [g for g in field_groups if g['name'] in selected]

    # Stupid way to break long values that contain lots of underscores
    # EX: Elasmobranch_vertebrae__3D_microarchitecture _and_mineral_density_...
    for field_dicts in cherries:
        for field in field_dicts['fields']:
            if len(field['value']) > 40 and field['value'].count('_') > 3:
                fs = field['value'].split('_')
                middle = int(len(fs)/2)
                fs[middle] = f'{fs[middle]}\n'
                field['value'] = '_'.join(fs)
    return cherries


def selected_field_groups(result):
    selected = [
        'Exchange',
        'Process Acquisition',
        'Instrument Detector Measurements',
        'Instrument General',
        # Will be shown at the top of the page instead
        # 'Measurement Sample',
    ]
    field_groups = detail_field_groups(result)
    return [g for g in field_groups if g['name'] in selected]
