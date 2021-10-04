from django.conf import settings
from urllib.parse import quote_plus


def globals(request):
    return {
        'portal_tagline': settings.PORTAL_TAGLINE,
        'ramses_search_categories':
            {k: quote_plus(k) for k in settings.RAMSES_SEARCH_CATEGORIES},
        'ramses_active_search_category':
            quote_plus(request.GET.get('filter.perfdata.category.value', '')),
        'kasthuri_contrast_default': 95,
        'kasthuri_brightness_default': 1600,
    }
