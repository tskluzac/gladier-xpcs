"""
This module contains functions for parsing automate responses.
"""
import logging
import json
import datetime
import isodate
from django.utils import timezone

try:
    import gladier
except ImportError:
    gladier = None

log = logging.getLogger(__name__)


def parse_automate_response(status):
    if gladier is None:
        raise ImportError('Gladier is not installed (pip install gladier)')
    try:
        return gladier.automate.get_details(status)
    except (KeyError, AttributeError):
        return status


def parse_date(date_string):
    if date_string and date_string != 'None':
        return isodate.parse_datetime(date_string)


def format_output_by_state(automate_response):
    output = automate_response.get('details', {}).get('output')
    if not output:
        return []
    bare_names = {n.replace('Input', '').replace('Result', '')
                  for n in output.keys() if n != '_context'}
    action_details = []
    for bn in bare_names:
        ad = {}
        for an in output.keys():
            if an.startswith(bn):
                if an.endswith('Input'):
                    ad['input'] = output[an]
                else:
                    ad['output'] = output[an]
        action_details.append({
            'name': bn,
            'data': ad,
        })
    return action_details


def parse_active_or_completed_state_metadata(automate_state_output):
    metadata = {k: v for k, v in automate_state_output.items()
                if k != 'details'}
    metadata['start_time'] = parse_date(metadata.get('start_time'))
    metadata['completion_time'] = parse_date(metadata.get('completion_time'))
    return metadata


def parse_state_output(automate_state_output):
    if not automate_state_output:
        return {}
    if automate_state_output.get('status') in ['ACTIVE', 'FAILED']:
        data = parse_active_or_completed_state_metadata(automate_state_output)
        output = json.dumps(automate_state_output.get('details', {}),
                            indent=2)
        data['general_output_pre'] = output
    else:
        output = automate_state_output.get('output', {})
        data = parse_active_or_completed_state_metadata(output)
        data['output_pre'] = json.dumps(output.get('details', {}), indent=2)
        data['input_pre'] = json.dumps(automate_state_output.get('input', {}),
                                       indent=2)
    return data


def parse_details(automate_response):
    if automate_response.get('status') in ['ACTIVE', 'FAILED']:
        states = [dict(name='state', **parse_state_output(automate_response))]
        return states
    states = format_output_by_state(automate_response)
    for state in states:
        state_output = state['data']
        state.update(parse_state_output(state_output))
    states.sort(key=lambda s: s.get('start_time') or timezone.now())
    return states
