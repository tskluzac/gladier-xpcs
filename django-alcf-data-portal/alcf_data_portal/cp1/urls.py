from django.urls import path
from globus_portal_framework.urls import register_custom_index
from alcf_data_portal.views import ProjectsView, ProjectSearch, ProjectDetail

register_custom_index('cp1_index', ['nci-pilot1', 'nci-pilot1-test'])


class PilotConfig:
    PROJECT_MANIFEST_INDEX = 'nci-pilot1'
    # Commenting out this switches it to the default defined for this index.
    # PROJECT_MANIFEST_SUBJECT = (
    # 'globus://pilot1-tools-project-manifest-v2.json'
    # )


class PilotProjects(PilotConfig, ProjectsView):
    pass


class PilotSearch(PilotConfig, ProjectSearch):
    pass


class PilotDetail(PilotConfig, ProjectDetail):
    pass


urlpatterns = [
    path('<cp1_index:index>/projects/',
         PilotProjects.as_view(), name='tp-projects-page'),
    path('<cp1_index:index>/projects/<project>/',
         PilotSearch.as_view(), name='tp-project-search'),
    path('<cp1_index:index>/projects/<project>/<subject>/',
         PilotDetail.as_view(), name='tp-project-detail'),
]
