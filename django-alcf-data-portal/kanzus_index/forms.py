import json
import logging
from django import forms
from urllib.parse import unquote_plus
from kanzus_index import models

log = logging.getLogger(__name__)


class ReprocessingTaskForm(forms.ModelForm):
    options_data = forms.CharField(max_length=512, initial='{}')

    class Meta:
        model = models.SampleReprocess
        fields = ['subject', 'project', 'remote_path', 'nproc',
                  'beamx', 'beamy', 'run_name', 'aps_data_root',
                  'options_data']

    def clean(self):
        # Disallow setting 'theta_root' until we get this working for
        # all users
        op_data = {
            # 'theta_root': self.data['theta_root'],
        }
        # if not op_data['theta_root'].endswith('/'):
        #     op_data['theta_root'] = f"{op_data['theta_root']}/"
        data = self.data.copy()
        data['options_data'] = json.dumps(op_data)
        data['subject'] = self.clean_subject()
        return data

    def clean_subject(self):
        sub = self.cleaned_data.get('subject')
        if not sub:
            raise forms.ValidationError('No Subject Provided!')
        # It's possible for subjects to be double encoded in some cases
        unquoted_sub = unquote_plus(unquote_plus(sub))
        log.debug(unquoted_sub)
        return unquoted_sub
