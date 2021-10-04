

def search_results(result):

    top_level_fields = [
        ('dlhub', [
            {'field': 'visible_to', 'name': 'Visibility', 'type': 'list'},
            {'field': 'version',  'name': 'Version'},
        ]),
        ('servable', [
            {'field': 'shim', 'name': 'Shim'},
            {'field': 'model_type', 'name': 'Model Type'},
         ])
    ]
    populated_fields = []
    for top_fname, field_list in top_level_fields:
        result_dict = result[0].get(top_fname, [])
        for field in field_list:
            if result_dict.get(field['field']):
                field['value'] = result_dict.get(field['field'])
                populated_fields.append(field)
    return populated_fields


def detailed_info(result):

    top_level_fields = [
        ('datacite', [
            {'field': 'description', 'name': 'Visibility', 'type': 'list'},
        ]),
        ('dlhub', [
            {'field': 'build_location', 'name': 'Build Location'},
            {'field': 'ecr_arn', 'name': 'ERC ARN'},
            {'field': 'ecr_uri', 'name': 'ERC URI'},
        ])
    ]
    populated_fields = []
    for top_fname, field_list in top_level_fields:
        result_dict = result[0].get(top_fname, [])
        for field in field_list:
            if result_dict.get(field['field']):
                field['value'] = result_dict.get(field['field'])
                populated_fields.append(field)
    return populated_fields
