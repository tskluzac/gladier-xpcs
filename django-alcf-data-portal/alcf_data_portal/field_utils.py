

def get_previews(result, result_key='files', filter_func=None):
    """Gather previews to use for displaying things with the general preview
    javascript module. Previews are sorted by url, and assigned ids in that
    order, so previews should generally load top to bottom.
    ** Parameters **
     ``result`` (list) content of gmeta entry, as given by DGPF
     ``result_key`` key in result where remote file manifest is located.
       Assumes 'result[0]['files']
     ``filter_func`` (str) -- optional boolean function to run on each entry
       to determine if it should be included. Example:
       filter_func=lambda p: p['mime_type'] == 'image/png'
    You can filter by mimetypes with mimetype_contains."""
    # Gather base previews from the remote file manifest
    filter_func = filter_func or (lambda x: bool(x))
    base_previews = {
        entry['url']: entry for entry in result[0][result_key]
        if entry and entry.get('url')}
    # If the user provided 'preview' info, overwrite the manifest entry with
    # the 'preview' entry
    base_previews.update(
        {entry['url']: entry
         for entry in result[0]['project_metadata'].get('preview', {})})
    # Add a preview id. The preview id is used by a javascript library to
    # determine how the data should be fetched/displayed.
    previews = sorted(list(base_previews.values()), key=lambda p: p['url'])
    for idx, preview in enumerate(previews):
        preview['id'] = idx
    return list(filter(filter_func, previews))
