from django.conf import settings
from globus_portal_framework.gclients import load_search_client
from mdf_forge.forge import Forge


def get_mdf_forge_client(index=None, user=None):
    if index is None:
        index = 'mdf-test' if settings.MDF_TEST else 'mdf'
    return Forge(index, search_client=load_search_client(user))
