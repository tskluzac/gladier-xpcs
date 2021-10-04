from django.http import JsonResponse
from django.views.generic.base import ContextMixin
from django.forms.models import model_to_dict


class JSONResponseMixin:
    """
    A mixin that can be used to render a JSON response.
    """
    def render_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return JsonResponse(self.get_json_data(context), **response_kwargs)

    def get_json_data(self, context):
        """
        Override to provide a JSON Serializable response
        """
        if context.get('object_list'):
            return {'object_list': [self.object_json(o)
                                    for o in context['object_list']]}
        return context

    def object_json(self, object):
        return model_to_dict(object)


class HybridJSONView(JSONResponseMixin, ContextMixin):
    """
    A mixin that can be used to render a JSON response.
    """
    @property
    def json_request(self):
        return (
            self.request.META.get('CONTENT_TYPE') == 'application/json' or
            self.request.GET.get('format') == 'json'
        )

    def render_to_response(self, context, **response_kwargs):
        if not context:
            response_kwargs['status'] = 404
        if self.json_request:
            return self.render_json_response(context, **response_kwargs)
        else:
            return super().render_to_response(context, **response_kwargs)
