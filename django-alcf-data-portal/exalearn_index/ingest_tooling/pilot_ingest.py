import os
import csv
from pilot.client import PilotClient

pc = PilotClient()

metadata = {
    "dc": {
        "creators": [
            {
                "creatorName": "Inverse Team"
            }
        ],
        "publicationYear": "2021",
        "publisher": "ORNL",
        "subjects": [],
    },
}

assert pc.context.current == 'exalearn'
assert pc.project.current == 'inverse'


def get_datasets():
    dirs = [p for p in os.listdir('') if os.path.isdir(p)]
    datasets = [d for d in dirs if
                any([f.endswith('.hdf5') for f in os.listdir(d)])]
    return datasets


def get_inverse_metadata(path):
    csv_filename = [f for f in os.listdir(path) if f.endswith('.csv')][0]
    with open(os.path.join(path, csv_filename)) as f:
        rows = csv.DictReader(f)
        row = [r for r in rows][0]
        string_types = ['instrument', 'material', 'symmetry']
        metadata = {k.lower(): v for k, v in row.items()
                    if k.lower() in string_types}
        ranges = {k.lower(): float(v) if '.' in v else int(v)
                  for k, v in row.items() if k.lower() not in string_types}
        metadata['ranges'] = ranges
        return metadata


if __name__ == '__main__':
    datasets = get_datasets()
    print(f'Ingesting {len(datasets)} datasets.')
    for dataset in datasets:
        print(f'Ingesting {dataset}...', end='')
        meta = pc.gather_metadata(dataset, '/', skip_analysis=True)
        meta['dc'].update(metadata['dc'])
        meta['project_metadata'].update(get_inverse_metadata(dataset))
        # from pprint import pprint
        # pprint(meta)
        pc.ingest(dataset, meta)
        print('Done!')
