import logging
from django.views.generic.edit import CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from automate_app.views import action, dashboard
from automate_app.models import Action
from kanzus_index import models, forms
from kanzus_index.views.search import KanzusDetail

log = logging.getLogger(__name__)


class AutomateDashboard(dashboard.Dashboard):

    def get_actions(self):
        pk_ids = [sr.action.id for sr in models.SampleReprocess.objects.all()]
        return Action.objects.filter(pk__in=pk_ids)


class ReprocessingTaskCreate(CreateView, KanzusDetail):
    model = models.SampleReprocess
    template_name = 'kanzus/detail-overview.html'
    form_class = forms.ReprocessingTaskForm

    def get_success_url(self):
        return reverse_lazy('kanzus-index:automate-dashboard',
                            kwargs={'index': self.kwargs['index']})

    def get_context_data(self, *args, **kwargs):
        ctx = super(CreateView, self).get_context_data()
        kanzus_ctx = super(KanzusDetail, self).get_context_data(
            self.kwargs['index'], self.kwargs['project'],
            self.kwargs['subject']
        )
        ctx.update(kanzus_ctx)
        ctx['can_reprocess'] = self.can_reprocess()
        return ctx

    def form_valid(self, form):
        user = self.request.user
        form.instance.user = user
        form.instance.action = models.SampleReprocess.new_action(user)
        resp = super().form_valid(form)
        # Start the Globus Automate Flow
        log.debug('Starting flow (Registered {}): {}'.format(
            form.instance.action.flow.date_created,
            form.instance.action
        ))
        form.instance.generate_payload()
        form.instance.action.start_flow()
        messages.success(self.request, 'Flow has been started')
        return resp


class KanzusActionDetail(action.ActionDetail):
    template_name = 'kanzus/automate_app/action_detail.html'

    def get_context_data(self, object):
        context = super().get_context_data()
        task = models.SampleReprocess.objects.get(action__id=object.id)
        context['reprocessing_task'] = task
        return context
