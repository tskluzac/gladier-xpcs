from django.urls import path, include


urlpatterns = [
    # Concierge URLSs
    path('', include('concierge_app.urls', namespace='concierge-app')),

    # Dependency URLS

    # The concierge app currently has dependencies on the tabbed project
    # templates, which it needs to provide a consistent page layout for
    # existing ALCF projects. These should only be needed so that URLs
    # can properly be reversed in core views. Ideally, we wouldn't have
    # this dependency.
    path('', include('alcf_data_portal.urls_tabbed_project')),
    # May be needed to reverse the login url.
    # path('', include('social_django.urls', namespace='social')),
    # Needed for logout url.
    path('', include('globus_portal_framework.urls')),
]
