import os
import copy
from urllib.parse import urlsplit, urlunsplit, urlencode

EXALEARN_EP = 'b8826a7a-676a-11e9-b7f5-0a37f382de32'

COSMO = [
    {'field': 'par', 'name': 'Par'},
    {'field': 'universe_id', 'name': 'Universe', 'type': 'int'},
    {'field': 'omega_m_phys', 'name': 'Omega M', 'type': 'float'},
    {'field': 'sigma_8_phys', 'name': 'Sigma 8', 'type': 'float'},
    {'field': 'nspec_phys', 'name': 'N Spec', 'type': 'float'},
    {'field': 'h0_phys', 'name': 'H0', 'type': 'float'},
]

# Extended normalized fields -- only show these on the detail page
COSMO_EXT = [
    {'field': 'omega_m_unit', 'name': 'Omega M Normalized', 'type': 'float'},
    {'field': 'sigma_8_unit', 'name': 'Sigma 8 Normalized', 'type': 'float'},
    {'field': 'nspec_unit', 'name': 'N Spec Normalized', 'type': 'float'},
    {'field': 'h0_unit', 'name': 'H0 Normalized', 'type': 'float'},
]

TOMOGAN_FIELDS = [
    {'field': 'algorithm', 'name': 'Algorithm'},
    {'field': 'sample', 'name': 'Sample'},
    {'field': 'projections', 'name': 'Projections', 'type': 'int'},
]


INVERSE_SEARCH_FIELDS = [
    {'field': 'instrument', 'name': 'Instrument'},
    {'field': 'material', 'name': 'Material'},
    {'field': 'symmetry', 'name': 'Symmetry'}
]

INVERSE_DETAIL_FIELDS = [
    {'field': 'alphamin', 'name': 'Alphamin'},
    {'field': 'alphamax', 'name': 'Alphamax'},
    {'field': 'betamin', 'name': 'Betamin'},
    {'field': 'betamax', 'name': 'Betamax'},
    {'field': 'gammamin', 'name': 'Gammamin'},
    {'field': 'gammamax', 'name': 'Gammamax'},
    {'field': 'amin', 'name': 'Amin'},
    {'field': 'amax', 'name': 'Amax'},
    {'field': 'bmin', 'name': 'Bmin'},
    {'field': 'bmax', 'name': 'Bmax'},
    {'field': 'cmin', 'name': 'Cmin'},
    {'field': 'cmax', 'name': 'Cmax'},
]


def search_results(result):
    pm = result[0].get('project_metadata', {})
    return (
            get_fields(COSMO, pm) +
            get_fields(TOMOGAN_FIELDS, pm) +
            get_fields(INVERSE_SEARCH_FIELDS, pm)
            )


def detail_results(result):
    return (
            get_fields(COSMO, result[0].get('project_metadata', {})) +
            get_fields(COSMO_EXT, result[0].get('project_metadata', {})) +
            get_fields(TOMOGAN_FIELDS, result[0].get('project_metadata', {})) +

            get_fields(INVERSE_SEARCH_FIELDS, result[0].get('project_metadata',
                                                            {})) +
            get_fields(INVERSE_DETAIL_FIELDS,
                       result[0].get('project_metadata', {}).get('ranges', {}))
    )


def get_fields(fields, result):
    """Takes a list of dictionaries describing data to fetch, and searches
    for matches in the given result (can be any dict). If a result is not found
    no entry is placed in the return data."""
    populated_fields = []
    for field in fields:
        if result.get(field['field']):
            new_field = copy.deepcopy(field)
            new_field['value'] = result.get(field['field'])
            populated_fields.append(new_field)

    return populated_fields


def get_first_hdf(result):
    hdf = [f for f in result[0]['files']
           if f['filename'].endswith('.hdf') or
           f['filename'].endswith('.hdf5')]
    if hdf:
        return hdf[0]
    return {}


def file_size(result):
    return get_first_hdf(result).get('length', 0)


def file_path(result):
    dataset = get_first_hdf(result).get('url')
    if dataset:
        return urlsplit(dataset).path


def https_url(result):
    return urlunsplit(
        ('https',
         '{}.e.globus.org'.format(EXALEARN_EP),
         file_path(result),
         '', '')
        )


def globus_app_link(result):
    query_params = {'origin_id': EXALEARN_EP,
                    'origin_path': os.path.dirname(file_path(result))}
    return urlunsplit(('https', 'app.globus.org', 'file-manager',
                       urlencode(query_params), ''))


def detail_preview_images(result):
    pm = result[0].get('project_metadata', {})
    if pm.get('redshift_images'):
        return pm.get('redshift_images')

    preview_data = [pm.get('tomogan_previews', {}).get(td)
                    for td in ['preview-ns', 'preview-gt']]
    if any(preview_data):
        return preview_data

    # Super hacky hack to mark inverse preview images as different
    # Cosmoflow images display in a public carousel, whereas carousel
    # doesn't support authenticated fetches (yes maybe?).
    img_data = get_inverse_preview_images(result)
    for im in img_data:
        im['inverse_preview'] = True
    return img_data


def is_inverse_preview(result):
    return any(dpi.get('inverse_preview') for dpi in detail_preview_images(result))


def search_preview_image(result):
    dpi = detail_preview_images(result)
    if dpi:
        dpi = dpi[0]
        # Remove caption for search preview
        if dpi.get('caption'):
            del dpi['caption']
        return dpi


def get_inverse_preview_images(result):
    files = [f for f in result[0]['files'] if f['filename'].endswith('.png')]

    previews = [
        {
            'caption': f['filename'],
            'basename': f['filename'],
            'url': f['url']
        }
        for f in files]
    return previews


def title(result):
    return result[0]['dc']['titles'][0]['title']


def remote_file_manifest(result):
    rfm = copy.deepcopy(result[0].get('files', []))
    for record in rfm:
        url = urlsplit(record['url'])
        record['url'] = urlunsplit(
            ('globus', url.netloc.replace('.e.globus.org', '',), url.path,
             '', ''))
    return rfm
