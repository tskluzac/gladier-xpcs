import os
from datetime import datetime
from urllib.parse import urlsplit, urlencode, urlunsplit
from alcf_data_portal.field_utils import get_previews


def title(record):
    try:
        rec_title = record[0]['dc']['titles'][0]['title']
        rec_title = 'Sample {}'.format(
            rec_title.split('_')[0],
        )
    except Exception:
        rec_title = record[0]['dc']['titles'][0]['title']
    return rec_title


def globus_app_link(result):
    rfm = remote_file_manifest(result)
    if rfm and rfm[0].get('url'):
        gurl = urlsplit(os.path.dirname(rfm[0].get('url')))
        endpoint = gurl.netloc.replace('.e.globus.org', '')
        query_params = {'origin_id': endpoint, 'origin_path': gurl.path}
        return urlunsplit(('https', 'app.globus.org', 'file-manager',
                           urlencode(query_params), ''))


def https_url(result):
    return result[0]['project_metadata']['beamline']['https_url']['value']


def remote_file_manifest(result):
    return result[0].get('files')


def search_results(result):
    fields = [
        {'field': 'creator', 'name': 'Creator',
         'value': result[0]['dc']['creators'][0]['creatorName']},
        {'field': 'acquisitionDate', 'name': 'Acquisition Date',
         'value': datetime.strptime(result[0]['dc']['dates'][0]['date'],
                                    '%Y-%m-%dT%H:%M:%S'),
         'type': 'date'},
        {'field': 'experiment',  'name': 'Experiment'},
        {'field': 'center_pos', 'name': 'Center Position'},
        {'field': 'prj', 'name': 'Project'},
        {'field': 'recon_type', 'name': 'Recon Type'},
    ]
    populated_fields = []
    beamline = result[0]['project_metadata']['beamline']
    for field in fields:
        if beamline.get(field['field']):
            field['value'] = beamline.get(field['field']).get('value')
        if field.get('value'):
            populated_fields.append(field)

    return populated_fields


def beamline_detail(result):
    # List of detail items. Order matters. Items not listed will be auto-added
    # with a capitalized name.
    fields = [
        {'field': 'name'},
        {'field': 'rcon_type', 'name': 'Rcon Type'},
        {'field': 'sample'},
        {'field': 'beamline'},
        {'field': 'center_pos', 'name': 'Center Position'},
        {'field': 'created_at', 'name': 'Created At', 'type': 'date'},
        {'field': 'category', 'name': 'Category'},
        {'field': 'dimension_x', 'name': 'Dimension X', 'type': 'int'},
        {'field': 'dimension_y', 'name': 'Dimension Y', 'type': 'int'},
        {'field': 'exposure_time', 'name': 'Exposure Time'},
        {'field': 'https_url', 'name': 'URL', 'type': 'url'},
    ]
    beamline = result[0]['project_metadata']['beamline']
    fnames = [f['field'] for f in fields]
    # Add fields not present
    fields += [{'field': f} for f in beamline if f not in fnames]

    populated_fields = []
    for field in fields:
        if beamline.get(field['field']):
            field['value'] = beamline[field['field']]['value']
        if not field.get('name'):
            field['name'] = field['field'].capitalize()
        if field.get('value'):
            if field.get('type') == 'date':
                field['value'] = datetime.strptime(field['value'],
                                                   '%Y-%m-%d %H:%M:%S')
            populated_fields.append(field)
    return populated_fields


def get_pngs(result):
    return get_previews(result,
                        filter_func=lambda p: 'image/png' in p['mime_type'])


def get_center_png(result):
    """Get center png or return None"""
    return next(filter(lambda p: 'center' in p['url'], get_pngs(result)), None)


def get_project_image(result):
    """Get project image or return None"""
    return next(filter(lambda p: 'proj_' in p['filename'], get_pngs(result)),
                None)


def get_listing_detail_preview_pngs(result):
    images = [
        get_center_png(result),
        get_project_image(result)
    ]
    # Remove nulls
    return list(filter(None, images))


def get_detail_preview_pngs(result):
    return get_pngs(result)


def other_previews(result):
    detail_prevs = get_listing_detail_preview_pngs(result)
    prevs = get_previews(
        result,
        filter_func=lambda x: (
            x['mime_type'] == 'image/png' and x not in detail_prevs
        )
    )
    return prevs
