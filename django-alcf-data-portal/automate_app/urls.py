from django.urls import path, include

from automate_app.views.action import (
    ActionCreate, ActionList, ActionDetail, ActionDelete
)
from automate_app.views.dashboard import Dashboard

# Allows Django URL Namespacing
app_name = 'automate-app'

actions = [
    path('<pk>/', ActionDetail.as_view(), name='action-detail'),
    path('<pk>/delete/', ActionDelete.as_view(), name='action-delete'),
    path('create/', ActionCreate.as_view(), name='action-create'),
    path('', ActionList.as_view(), name='action-list'),
]

flows = [
    path('<pk>/', ActionDetail.as_view(), name='flow-detail'),
    path('', ActionList.as_view(), name='flow-list'),
]

urlpatterns = [
    path('', Dashboard.as_view(), name='dashboard'),
    path('actions/', include(actions)),
    path('flows/', include(flows)),
]
