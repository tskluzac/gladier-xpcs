import os
import logging
from urllib.parse import urlunparse, urlencode
from django.shortcuts import redirect
from django.contrib import messages, auth
from django.urls import reverse
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import FormView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from globus_portal_framework.gsearch import get_index, get_template
from globus_portal_framework.gclients import (
    load_transfer_client
)
from concierge_app.models import Manifest, ManifestTransfer
from concierge_app import models, exc
from concierge_app.forms import (
    SubjectSelectManifestCheckoutForm, MDFCollectionSubmissionForm
)
from concierge_app.mixins import HybridJSONView

log = logging.getLogger(__name__)


class ManifestCheckoutView(LoginRequiredMixin, FormView):
    """Manifest Checkout View is a user-facing helper page for creating manifests. Manifests
    *should* be able to be created via POSTing to the /manifests/ URL, but the
    checkout page allows for validating user-input via Django forms. Forms
    give the user better feedback if something went wrong, with a hint of how
    to correct it. Comparatively, supporting POST via the manifests/ url should
    also be supported, but possibly only via the API."""
    http_method_names = ['get', 'post']
    template_name = 'concierge-app/tabbed-project/../templates/concierge-app/tabbed-project/manifest-checkout.html'
    form_class = SubjectSelectManifestCheckoutForm
    model_class = Manifest

    @property
    def core_context(self):
        ctx = {'index': self.kwargs['index']}
        if self.kwargs.get('project'):
            ctx['project'] = self.kwargs['project']
        return ctx

    def get_template_names(self):
        return get_template(self.kwargs.get('index'), self.template_name)

    def get_search_reference_url(self):
        """Get the URL users can use to re-search a previous query. The
        queries will be added automatically, but this is required if the
        base search url is non-standard, such as searching in an index
        containing projects."""
        if self.kwargs.get('project'):
            return reverse('tp-project-search', kwargs=self.core_context)
        else:
            return reverse('tp-search', kwargs=self.core_context)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(self.core_context)
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'request': self.request,
            'search_url': self.get_search_reference_url(),
        })
        kwargs.update(self.core_context)
        return kwargs

    def form_valid(self, form):
        log.debug(f'Form valid for {form.__class__}')
        name = form.cleaned_data['name']
        user = self.request.user
        self.model_class.create(user, form.get_search_collector())
        messages.info(self.request, f'{name} has been created!')
        log.info(f'{user} created a new manifest {name}')
        return redirect(reverse('concierge-app:manifest-list',
                        kwargs={'index': self.kwargs['index']}))

    def form_invalid(self, form):
        log.debug(f'Form was INVALID for {self.request.user}: {form.errors}')
        return super().form_invalid(form)


class ManifestListView(LoginRequiredMixin, ListView):
    """Manifest list view. This class is responsible for both listing manifests and
    creating new manifests.

    TODO: Move manifest creation to the 'DetailView' and not the list view. This is
    a holdover from doing all operations in the list view.
    """

    context_object_name = 'concierge_manifests'
    template_name = 'concierge-app/tabbed-project/../templates/concierge-app/tabbed-project/manifests.html'
    helper_page_params = {
        'method': 'GET',
        'filelimit': 0,
        'folderlimit': 1,
        'label': '',
        'action': '',
        'cancelurl': ''
    }
    form = SubjectSelectManifestCheckoutForm

    def get_queryset(self):
        return Manifest.objects.filter(
            user=self.request.user,
            index=self.kwargs['index']
        ).order_by('-date_created')

    def get_checkout_url(self):
        return reverse('concierge-app:manifest-checkout', kwargs=self.kwargs)

    def get_mymanifests_url(self):
        urlparams = {'index': self.kwargs['index']}
        protocol = 'https'
        host = self.request.META.get('HTTP_HOST', 'localhost:8000')
        if host == 'localhost:8000':
            protocol = 'http'
        return urlunparse(
            (protocol, host,
             reverse('concierge-app:manifest-list', kwargs=urlparams), '', '', '')
        )

    def get_choose_manifest_url(self):
        hp_params = self.helper_page_params.copy()
        index = self.kwargs.get('index')
        index_data = get_index(index)
        hp_params.update({'label': f'{index_data["name"]} Concierge Transfer',
                          'cancelurl': self.get_mymanifests_url(), })
        hp_params_enc = urlencode(hp_params)
        action_param = urlencode({'action': self.get_mymanifests_url()})
        hp_params_enc = f'{hp_params_enc}&{action_param}'
        return urlunparse(('https', 'app.globus.org', 'file-manager', '',
                           hp_params_enc, ''))

    def get_transfer_context(self):
        context = dict()
        context['transfer_endpoint'] = self.request.GET.get('endpoint', '')
        if context.get('transfer_endpoint'):
            try:
                tc = load_transfer_client(self.request.user)
                ep_name = context['transfer_endpoint']
                ep = tc.get_endpoint(ep_name).data
                name = ep['display_name'] or ep['canonical_name'] or ep_name
                context['transfer_endpoint_name'] = name
            except Exception as e:
                log.exception(e)
        context['transfer_endpoint_id'] = \
            self.request.GET.get('endpoint_id', '')
        context['transfer_path'] = os.path.join(
            self.request.GET.get('path', ''),
            self.request.GET.get('folder[0]', '')
        )
        context['transfer_label'] = self.request.GET.get('label', '')
        if any(context.values()):
            return context
        return dict()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_transfer_context())
        context['choose_manifest_url'] = self.get_choose_manifest_url()
        manifest = Manifest.get_user_manifest(self.request.user, self.kwargs.get('manifest_id'))
        if manifest is not None:
            context['select_manifest'] = manifest.id
        manifest_transfers = ManifestTransfer.objects.filter(
            user=self.request.user,
            index=self.kwargs['index']
        ).order_by('-date_created')
        for sb in manifest_transfers:
            sb.update_task()
        context['manifest_transfers'] = manifest_transfers
        return context

    def get_template_names(self):
        return [
            get_template(self.kwargs.get('index'), self.template_name),
            self.template_name
        ]

    def post(self, request, index, *args, **kwargs):
        raise NotImplementedError('Please use the checkout page instead')


class ManifestDetailView(LoginRequiredMixin, HybridJSONView, DetailView):
    http_method_names = ['get', 'delete']
    model = Manifest

    def get_object(self):
        return Manifest.get_user_manifest(self.request.user, self.kwargs['manifest_id'])

    def get_context_data(self, **kwargs):
        return self.get_object()

    def get_json_data(self, context):
        return {
            'id': context.id,
            'user': context.user.username,
            'index': context.index,
            # 'concierge_id': context.concierge_id,
            # 'mdf_connect_submission': context.get_user_submission(),
            # 'minid': context.minid,
            'date_created': context.date_created,
            'data': context.metadata,
        }

    def render_to_response(self, context, **response_kwargs):
        if not self.json_request:
            raise NotImplementedError('No standalone templates for these yet!')
        return super().render_to_response(context, **response_kwargs)

    def delete(self, request, index, manifest_id):
        manifest = self.get_context_data()
        manifest.delete()
        return self.render_to_response(manifest)


class ManifestTransferView(LoginRequiredMixin, ListView):
    context_object_name = 'manifest_transfer'

    def get_queryset(self):
        return ManifestTransfer.objects.filter(
            user=self.request.user,
            index=self.kwargs['index']
        ).order_by('-date_created')


class ManifestTransferDetail(LoginRequiredMixin, HybridJSONView, DetailView):
    http_method_names = ['get', 'post', 'delete']
    model = ManifestTransfer

    def get_object(self):
        return ManifestTransfer.get_user_manifest(self.request.user, self.kwargs['manifest_id'])

    def get_context_data(self, **kwargs):
        return self.get_object()

    def get_json_data(self, context):
        if not context:
            return {'error': 'No object exists'}
        return {
            'id': context.id,
            'user': context.user.username,
            'index': context.index,
            'manifest_id': context.manifest_id,
            'date_created': context.date_created,
            'manifest_info': {
                'manifest_id': context.manifest.manifest_id,
                'index': context.manifest.index,
                'date_created': context.manifest.date_created,
            },
            'data': context.metadata,
        }

    def render_to_response(self, context, **response_kwargs):
        if not self.json_request:
            raise NotImplementedError('No standalone templates for these yet!')
        return super().render_to_response(context, **response_kwargs)

    def post(self, request, index, *args, **kwargs):

        endpoint = self.request.POST.get('endpoint')
        path = self.request.POST.get('path')
        label = self.request.POST.get('label')
        smanifest = ManifestTransfer.manifest_transfer(request.user, index, self.kwargs['manifest_id'],
                                  endpoint, path, label)
        if self.json_request:
            return self.render_to_response(smanifest)
        messages.info(request,
                      f'A transfer has been started for the files in '
                      f'{smanifest.manifest.metadata.get("name")}.')
        return redirect(reverse('concierge-app:manifest-list',
                                kwargs={'index': index}))

    def delete(self, request, index, manifest_id):
        manifest = self.get_context_data()
        if manifest:
            manifest.delete()
        return self.render_to_response(manifest)


class ManifestTransferCancel(ManifestTransferDetail):
    http_method_names = ['post']

    def post(self, request, index, manifest_id):
        manifest = self.get_context_data()
        manifest.cancel_transfer()
        return self.render_to_response(manifest)


class MDFConnectSubmissionView(LoginRequiredMixin, HybridJSONView, CreateView):
    http_method_names = ['get', 'post', 'delete']
    template_name = 'concierge-app/tabbed-project/../templates/concierge-app/tabbed-project/manifest-checkout.html'
    model = models.MDFCollectionSubmission
    form_class = MDFCollectionSubmissionForm

    @property
    def core_context(self):
        ctx = {'index': self.kwargs['index']}
        if self.kwargs.get('project'):
            ctx['project'] = self.kwargs['project']
        return ctx

    def get_context_data(self):
        ctx = super().get_context_data()
        ctx.update(self.core_context)
        return ctx

    def get_json_data(self, context):
        raise NotImplementedError('Not implemented yet!')

    def get_template(self):
        return get_template(self.kwargs.get('index'), self.template_name)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs.update(self.core_context)
        return kwargs

    def form_invalid(self, form):
        messages.error(self.request, form.errors)
        return redirect(reverse('concierge-app:manifest-list',
                        kwargs={'index': self.kwargs['index']}))

    def form_valid(self, form):
        submission = form.save(commit=False)
        submission.user = self.request.user
        if submission.search_collection.user != self.request.user:
            log.error(f'User submitting {submission.user} does not '
                      f'match user who collected'
                      f'{submission.search_collection.user}')
            messages.error(self.request, 'You are not allowed to do that.')
            return redirect(submission.get_absolute_url())
        try:
            submission.submit()
            submission.save()
            messages.info(self.request,
                          'Your data has been submitted to the MDF.')
        except exc.MDFAccessDenied:
            url = reverse('concierge-app:mdf-connect-request-access',
                          kwargs={'index': self.kwargs['index']})
            return redirect(url)
        except exc.MDFPreviousSubmission:
            messages.error(self.request, 'This dataset has already been '
                           'submitted, please choose a different title: '
                           f'"{submission.title}"')
        except exc.MDFTokenAbsent:
            log.error('User MDF token absent, poping session to re-login...')
            messages.warning(self.request, 'Your previous session was missing '
                             'the MDF consent, if you have accepted it, you '
                             'should now be able to submit datasets.')
            auth.logout(self.request)
            base_url = reverse('social:begin', kwargs={'backend': 'globus'})
            params = urlencode({'next': submission.get_absolute_url()})
            return redirect('{}?{}'.format(base_url, params))
        except exc.MDFSubmissionError as suberror:
            log.exception(suberror)
            messages.error(
                self.request, 'There was a problem submitting to the MDF, '
                'please contact your maintainer and we will fix this as soon '
                'as possible.')
        return redirect(submission.get_absolute_url())


class MDFConnectRequestAccess(LoginRequiredMixin, TemplateView):

    template_name = ('concierge-app/tabbed-project/mdf-connect-'
                     'request-access.html')

    @property
    def core_context(self):
        ctx = {'index': self.kwargs['index']}
        if self.kwargs.get('project'):
            ctx['project'] = self.kwargs['project']
        return ctx

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data()
        ctx.update(self.core_context)
        return ctx
