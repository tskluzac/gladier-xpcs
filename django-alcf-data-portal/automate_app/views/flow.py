import logging
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404

from automate_app.models import Flow

log = logging.getLogger(__name__)


class FlowList(LoginRequiredMixin, ListView):
    model = Flow

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


class FlowDetail(LoginRequiredMixin, DetailView):
    model = Flow

    def get_object(self):
        obj = super().get_object()
        if (not self.request.user.is_superuser and
                obj.user != self.request.user):
            raise Http404()
        # Update the current status of the flow
        obj.update_flow()
        return obj
