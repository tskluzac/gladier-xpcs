import logging
from automate_app.flow_payload import FlowPayload

# import sys
# sys.path.insert(0, '/Users/nick/globus/aps/globus-automation')
from kanzus_index import apps

log = logging.getLogger(__name__)
# try:
#     from Kanzus.tools.automate_flows import flow_definition as kanzus_flow_def
#     from Kanzus.tools.client import KanzusClient
# except ImportError:
#     log.error('kanzus_index: please install the globus-automation package.')
#     kanzus_flow_def = {}


class SampleReprocessPayload(FlowPayload):

    # Core Automate Payload Fields
    FLOW_DEFINITION = {}
    FLOW_GROUP = apps.REPROCESSING_TASK_GROUP

    # Functions to run before starting the flow
    RUNTIME_CHECKS = [
    ]

    # FuncX endpoint to use
    FUNCX_LOGIN = '3b490c00-43f1-438c-aeeb-aa33f25bef1c'  # Theta login
    FUNCX_WORKER = '77798b09-31d3-4856-8e1c-641fbf31a97e'  # Theta Worker

    def __init__(self, model):
        self.model = model
        self.kanzus_client = KanzusClient()
        super().__init__()

    def generate_ranges(self, base_path):
        try:
            base_paths = []
            step = 256
            path_components = base_path.split('_')
            trigger_val = path_components[-1].replace('.cbf', '')
            trigger_num = int(trigger_val)
            ranges = list(range(step, trigger_num, step))
            if ranges[-1] < trigger_num:
                ranges.append(trigger_num)
            base_path_components = path_components[0:-1]
            for r in ranges:
                path_range = str(r).zfill(len(trigger_val))
                path = '_'.join(base_path_components + [f'{path_range}.cbf'])
                base_paths.append(path)
            return base_paths
        except Exception as e:
            log.exception(e)

    def get_payload_inputs(self):
        base_paths = self.generate_ranges(self.model.remote_path)
        payload = self.kanzus_client.create_funcx_payload(
            base_paths,
            run_name=self.model.run_name,
            nproc=self.model.nproc,
            beamx=self.model.beamx,
            beamy=self.model.beamy,
            aps_data_root=self.model.aps_data_root,
            theta_root='/projects/APSDataAnalysis/nick/SSX/',
            # # pilot={'dry_run': True}
        )
        flow_payload = self.kanzus_client.create_flow_tasks(payload,
                                                            self.FUNCX_WORKER,
                                                            self.FUNCX_LOGIN)
        if self.FUNCX_WORKER == self.FUNCX_LOGIN:
            log.warning('Funcx worker endpoint is the same as login! Remember '
                        'to only run simple jobs on login nodes, big tasks '
                        'will destroy them!')
        return flow_payload
