import logging

from django.http import JsonResponse
from django.conf import settings
from globus_portal_framework.gclients import load_globus_access_token

log = logging.getLogger(__name__)


def get_access_token(request):
    if request.user.is_anonymous:
        return JsonResponse({'error': 'Not Authorized'}, status=401)

    resource_server = request.GET.get('resource_server')
    if resource_server not in settings.ALLOWED_FRONTEND_TOKENS:
        log.debug(('Resource server "{}" is disallowed. '
                   'Check "settings.ALLOWED_FRONTEND_TOKENS"'
                   '').format(resource_server))
        return JsonResponse({'error': 'Only these tokens are allowed: {}'
                             .format(list(settings.ALLOWED_FRONTEND_TOKENS))},
                            status=400)

    token = load_globus_access_token(request.user, resource_server)
    return JsonResponse({'token': token})
