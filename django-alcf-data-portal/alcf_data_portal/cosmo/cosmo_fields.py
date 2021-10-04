

def remote_file_manifest(result):
    if result[0].get('remote_file_manifest'):
        return [result[0]['remote_file_manifest']]
