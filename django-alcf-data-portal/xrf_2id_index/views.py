import logging
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from automate_app.views.action import ActionDetail
from automate_app.views.dashboard import Dashboard
from automate_app.models import Action

from alcf_data_portal.views import ProjectDetail

from xpcs_index.forms import ReprocessingTaskForm
from concierge_app.views.generic import ManifestListView
from xpcs_index.models import ReprocessingTask, FilenameFilter


log = logging.getLogger(__name__)


class XPCSProjectDetail(ProjectDetail):

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        preview_list = (
            'all_preview',
            'correlation_plot_previews',
            'correlation_plot_with_fit_previews',
            'intensity_plot_previews',
            'structural_analysis_prev'
        )
        try:
            for preview in preview_list:
                for manifest in context.get(preview, []):
                    match = FilenameFilter.match(self.request.user,
                                                 manifest.get('filename'))
                    manifest['show_filename'] = match
        except Exception as e:
            log.exception(e)
        return context


class ReprocessingTaskCreate(LoginRequiredMixin, CreateView):
    model = ReprocessingTask
    form_class = ReprocessingTaskForm
    template_name = 'xpcs/concierge-app/components/manifests-detail-reprocess-form.html'

    def get_absolute_url(self):
        return reverse_lazy('concierge-app:manifest-list', kwargs={'index': 'xpcs'})

    def get_success_url(self):
        return reverse_lazy('xpcs-index:automate-dashboard',
                            kwargs={'index': 'xpcs'})

    def form_valid(self, form):
        user = self.request.user
        manifest = form.cleaned_data['manifest']
        form.instance.user = user
        form.instance.action = self.model.new_action(manifest, user)
        resp = super().form_valid(form)
        # Start the Globus Automate Flow
        form.instance.generate_payload()
        form.instance.action.start_flow()
        messages.success(self.request, 'Flow has been started')
        return resp


class XPCSManifestListView(ManifestListView, ReprocessingTaskCreate):
    pass


class AutomateDashboard(Dashboard):

    def get_actions(self):
        pk_ids = [sr.action.id for sr in ReprocessingTask.objects.all()]
        return Action.objects.filter(pk__in=pk_ids)


class XPCSActionDetail(ActionDetail):
    template_name = 'xpcs/automate_app/action_detail.html'

    def get_context_data(self, object):
        context = super().get_context_data()
        context['reprocessing_task'] = ReprocessingTask.objects.get(
            action__id=object.id
        )
        return context
