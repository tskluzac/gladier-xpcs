import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from automate_app.models import Flow, Action
from django.views.generic import TemplateView
from globus_portal_framework.gsearch import get_template

log = logging.getLogger(__name__)


class Dashboard(LoginRequiredMixin, TemplateView):

    template_name = 'automate_app/../templates/automate_app/dashboard.html'

    def get_template_names(self):
        if self.kwargs.get('index'):
            return get_template(self.kwargs['index'], self.template_name)
        return self.template_name

    def get_actions(self):
        """Can be overridden to filter on only actions for a given index"""
        return Action.objects.all()

    def user_filter(self, queryset):
        if not self.request.user.is_superuser:
            return queryset.filter(user=self.request.user)
        return queryset

    def get_context_data(self, *args, **kwargs):
        actions = self.user_filter(self.get_actions()).order_by('-date_created')
        flows = Flow.objects.filter(pk__in=[a.flow.id for a in actions])

        utype = 'Superuser' if self.request.user.is_superuser else 'User'
        log.debug(f'{utype} {self.request.user} fetched {len(flows)} flows and '
                  f'{len(actions)} actions')
        return {'flows': flows, 'actions': actions}
