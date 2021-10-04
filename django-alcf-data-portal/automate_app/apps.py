import logging
from django.apps import AppConfig

log = logging.getLogger(__name__)


class AutomateAppConfig(AppConfig):
    name = 'automate_app'
