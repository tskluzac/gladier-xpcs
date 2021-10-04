from django.urls import path
from django.conf import settings
from globus_portal_framework.urls import register_custom_index
from concierge_app.views.generic import (
    ManifestListView, ManifestDetailView, ManifestTransferDetail,
    ManifestTransferView, ManifestCheckoutView, ManifestTransferCancel,
    MDFConnectSubmissionView, MDFConnectRequestAccess,
)
from concierge_app.views.manifest_limiter import ManifestLimiterCheckoutView

# Allows Django URL Namespacing
app_name = 'concierge-app'


CONCIERGE_INDEXES = getattr(settings, 'CONCIERGE_INDEXES',
                            settings.SEARCH_INDEXES.keys())
register_custom_index('concierge_index', list(CONCIERGE_INDEXES))


urlpatterns = [
    path('<concierge_index:index>/mdf-connect-submission/',
         MDFConnectSubmissionView.as_view(), name='mdf-connect-submission'),
    path('<concierge_index:index>/mdf-connect-submission/<project>/',
         MDFConnectSubmissionView.as_view(), name='mdf-connect-submission'),
    path('<concierge_index:index>/mdf-connect-submission/<pk>/',
         MDFConnectSubmissionView.as_view(), name='mdf-connect-submission'),
    path('<concierge_index:index>/mdf-connect-access-request/',
         MDFConnectRequestAccess.as_view(), name='mdf-connect-request-access'),
    path('<concierge_index:index>/manifest-checkout/<project>/',
         ManifestCheckoutView.as_view(), name='manifest-project-checkout'),
    path('<concierge_index:index>/manifest-checkout/', ManifestCheckoutView.as_view(),
         name='manifest-checkout'),
    path('<concierge_index:index>/manifest-limiter-checkout/',
         ManifestLimiterCheckoutView.as_view(), name='manifest-limiter-checkout'),
    path('<concierge_index:index>/manifest-limiter-checkout/<project>/',
         ManifestLimiterCheckoutView.as_view(), name='manifest-limiter-checkout'),
    # Stage Manifest Detail View
    path('<concierge_index:index>/manifest-transfer/<int:manifest_id>/cancel/',
         ManifestTransferCancel.as_view(), name='manifest-transfer-cancel'),
    path('<concierge_index:index>/manifest-transfer/<int:manifest_id>/',
         ManifestTransferDetail.as_view(), name='manifest-transfer-detail'),
    path('<concierge_index:index>/manifest-transfer/',
         ManifestTransferDetail.as_view(), name='manifest-transfer-detail'),
    # Stage Manifest List View
    path('<concierge_index:index>/manifest-transfers/',
         ManifestTransferView.as_view(), name='manifest-transfers'),
    # Manifest Detail View
    path('<concierge_index:index>/manifest/<int:manifest_id>/', ManifestDetailView.as_view(),
         name='manifest-detail'),
    path('<concierge_index:index>/manifest/', ManifestDetailView.as_view(),
         name='manifest-detail'),
    # Manifest List View
    path('<concierge_index:index>/manifests/<int:manifest_id>/', ManifestListView.as_view(),
         name='manifest-list'),
    path('<concierge_index:index>/manifests/', ManifestListView.as_view(),
         name='manifest-list'),
]
