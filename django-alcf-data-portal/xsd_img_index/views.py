from django.shortcuts import render
from alcf_data_portal.views import ProjectSearch
from globus_portal_framework.gsearch import get_template

PROJECT = 'xsd-img'


def landing_page(request, index):
    context = {'index': index, 'project': PROJECT}
    template = get_template(index, 'global/tabbed-project/landing-page.html')
    return render(request, template, context)


class XsdImgProjectSearch(ProjectSearch):

    def get_context_data(self, *args, **kwargs):
        self.kwargs['project'] = PROJECT
        ctx = super().get_context_data(*args, **kwargs)
        ctx['project'] = PROJECT
        ctx['index'] = 'xsd-img'
        return ctx
