from django.urls import path
from globus_portal_framework.urls import register_custom_index
from alcf_data_portal.dlhub.views import SortedPubDateSearch

register_custom_index('dlhub_index', ['dlhub'])

urlpatterns = [
    path('<dlhub_index:index>/', SortedPubDateSearch.as_view(), name='search'),
]
