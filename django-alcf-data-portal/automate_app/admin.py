

from django.contrib import admin
from automate_app.models import Flow, Action, FlowInstanceAuthorizer

admin.site.register(Flow)
admin.site.register(Action)
admin.site.register(FlowInstanceAuthorizer)
