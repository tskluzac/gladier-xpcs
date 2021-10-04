import logging
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, DeleteView
from django.urls import reverse_lazy
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

import globus_sdk.exc


from automate_app.models import Action

log = logging.getLogger(__name__)


class ActionList(LoginRequiredMixin, ListView):
    model = Action

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


class ActionDetail(LoginRequiredMixin, DetailView):
    model = Action

    def get_object(self):
        obj = super().get_object()
        if (not self.request.user.is_superuser and
                obj.user != self.request.user):
            raise Http404()
        # Update the current status of the flow
        try:
            obj.update_flow()
        except globus_sdk.exc.GlobusAPIError as gapie:
            log.exception(gapie)
            messages.error(self.request, 'The Globus Automate API returned '
                           'an error, the task could not be updated.')
        return obj


class ActionCreate(CreateView):
    model = Action
    fields = ['flow', 'payload_data']
    success_url = reverse_lazy('automate-app:action-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        resp = super().form_valid(form)
        # Start the Globus Automate Flow
        form.instance.start_flow()
        return resp


class ActionDelete(DeleteView):
    model = Action
    success_url = reverse_lazy('automate-app:action-list')
