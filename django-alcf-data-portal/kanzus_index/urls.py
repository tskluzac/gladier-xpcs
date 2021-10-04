from django.urls import path
from globus_portal_framework.urls import register_custom_index
from alcf_data_portal.views import ProjectsView
from kanzus_index.views.search import (
    KanzusExtendedMetadataSearch, KanzusDetail
)
from kanzus_index.views.automate import (
    ReprocessingTaskCreate, AutomateDashboard, KanzusActionDetail
)

app_name = 'kanzus-index'
register_custom_index('kanzus_index', ['kanzus'])

urlpatterns = [
    path('<kanzus_index:index>/projects/<project>/<path:subject>/reprocess/',
         ReprocessingTaskCreate.as_view(), name='sample-reprocess'),
    path('<kanzus_index:index>/automate/',
         AutomateDashboard.as_view(), name='automate-dashboard'),
    path('<kanzus_index:index>/automate/actions/<pk>/',
         KanzusActionDetail.as_view(), name='automate-action-detail'),
    path('<kanzus_index:index>/',
         ProjectsView.as_view(), name='tp-landing-page'),
    path('<kanzus_index:index>/projects/<project>/',
         KanzusExtendedMetadataSearch.as_view(),
         name='tp-project-search'),
    path('<kanzus_index:index>/projects/<project>/<path:subject>/',
         KanzusDetail.as_view(), name='tp-project-detail'),
]
