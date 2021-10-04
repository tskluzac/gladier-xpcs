from globus_portal_framework.urls import register_custom_index
from django.urls import path
from globus_tutorial_index.views import (
    landing_page, tutorial_detail, tutorial_detail_preview,
    TutorialSearch,
)

app_name = 'globus-tutorial'
register_custom_index('globus_tutorial_index', ['globus-tutorial'])

# # Use this if you want to customize any of the views.
urlpatterns = [
    # path('<globus_tutorial_index:index>/', tabbed_project_landing_page, name='landing-page'),
    # Make Subjects "Paths" so they don't need to be quoted
    path('<globus_tutorial_index:index>/', landing_page, name='landing-page'),
    path('<globus_tutorial_index:index>/<index_uuid>/detail/<path:subject>/',
         tutorial_detail, name='detail'),
    path('<globus_tutorial_index:index>/<index_uuid>/detail/<path:subject>/',
         tutorial_detail, name='detail'),
    path('<index:index>/<index_uuid>/detail-preview/<subject>/',
         tutorial_detail_preview, name='detail-preview'),
    path('<index:index>/<index_uuid>/detail-preview/<subject>/<endpoint>/<path:url_path>/',
         tutorial_detail_preview, name='detail-preview'),
    path('<globus_tutorial_index:index>/<index_uuid>/', TutorialSearch.as_view(), name='search'),
]
