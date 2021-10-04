from django.urls import path
from globus_portal_framework.urls import register_custom_index
from exalearn_index.views import (
    SliderFacetsSearch, LandingPage, TransferAwareDetailOverview,
    SubmitTransfer
)

register_custom_index('exalearn_index', ['exalearn'])

urlpatterns = [
    path('<exalearn_index:index>/',
         LandingPage.as_view(), name='tp-landing-page'),
    path('<exalearn_index:index>/projects/<project>/',
         SliderFacetsSearch.as_view(), name='tp-project-search'),
    path('<exalearn_index:index>/projects/<project>/<subject>/',
         TransferAwareDetailOverview.as_view(), name='tp-project-detail'),
    path('<exalearn_index:index>/projects/<project>/<subject>/transfer/',
         SubmitTransfer.as_view(), name='tp-submit-transfer'),
    path('<exalearn_index:index>/data/',
         SliderFacetsSearch.as_view(), name='tp-search'),
]
