from django.urls import path
from globus_portal_framework.urls import register_custom_index
from alcf_data_portal.views import ProjectsView
from alcf_data_portal.kasthuri.views import search_debug_detail

register_custom_index('kasthuri_index', ['kasthuri'])

urlpatterns = [
    path('<kasthuri_index:index>/search-debug-detail/<subject>/',
         search_debug_detail, name='tp-search-debug-detail'),
    path('<kasthuri_index:index>/',
         ProjectsView.as_view(), name='tp-landing-page'),
]
