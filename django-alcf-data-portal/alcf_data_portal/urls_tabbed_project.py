from django.urls import path, include
from django.conf import settings
from globus_portal_framework.views import (
    search, detail, search_debug, search_debug_detail
)
from globus_portal_framework.urls import register_custom_index
from alcf_data_portal.views import (tabbed_project_landing_page,
                                    ProjectsView, ProjectSearch,
                                    ProjectDetail)

register_custom_index('tp_index', settings.TABBED_PROJECT_INDEXES)


urlpatterns = [
    path('<tp_index:index>/', tabbed_project_landing_page,
         name='tp-landing-page'),
    path('<tp_index:index>/projects/', ProjectsView.as_view(),
         name='tp-projects-page'),
    path('<tp_index:index>/projects/<project>/', ProjectSearch.as_view(),
         name='tp-project-search'),
    path('<tp_index:index>/projects/<project>/<path:subject>/',
         ProjectDetail.as_view(), name='tp-project-detail'),
    path('<tp_index:index>/data/', search, name='tp-search'),
    path('<tp_index:index>/detail/<path:subject>/', detail, name='tp-detail'),
    path('', include('concierge_app.urls')),
    path('automate/', include('automate_app.urls')),
]
if settings.DEBUG:
    urlpatterns += [
        path('<tp_index:index>/debug/', search_debug, name='tp-search-debug'),
        path('<tp_index:index>/debug/<subject>/', search_debug_detail,
             name='tp-search-debug-detail'),
    ]
