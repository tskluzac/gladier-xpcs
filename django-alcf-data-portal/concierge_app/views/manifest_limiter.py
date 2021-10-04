import logging
from concierge_app.views.generic import ManifestCheckoutView
from concierge_app.forms import ManifestLimiterCheckoutForm

log = logging.getLogger(__name__)


class ManifestLimiterCheckoutView(ManifestCheckoutView):
    """Manifest Limiter limits the number of results recorded by a user-provided
    number. The actual results gathered are arbitrary."""
    form_class = ManifestLimiterCheckoutForm
    template_name = 'concierge-app/tabbed-project/manifest-limiter-checkout.html'
