from collections import OrderedDict
from django.shortcuts import render
from globus_portal_framework import get_subject, get_template


def search_debug_detail(request, index, subject):
    sub = get_subject(index, subject, request.user)
    debug_fields = {name: data for name, data in sub.items()}
    dfields = OrderedDict(debug_fields)
    if dfields.get('all'):
        dfields.move_to_end('all')
    sub['django_portal_framework_debug_fields'] = dfields
    return render(request,
                  get_template(index, 'search-debug-detail.html'), sub)
