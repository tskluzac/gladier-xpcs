import json
import logging
from django import forms

from concierge_app import models

log = logging.getLogger(__name__)


class AutomateResubmissionForm(forms.ModelForm):

    class Meta:
        model = models.MDFCollectionSubmission
        fields = ['flow', 'user', 'payload_data']

    def clean_payload_data(self):
        try:
            return json.dumps(json.loads(self.cleaned_data['payload_data']))
        except Exception as e:
            log.exception(e)
            raise forms.ValidationError(str(e))
