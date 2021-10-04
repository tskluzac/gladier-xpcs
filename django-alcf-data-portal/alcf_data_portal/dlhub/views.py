from alcf_data_portal.views import CustomSearch


class SortedPubDateSearch(CustomSearch):

    def post_search(self, search_client, index_uuid, data):
        data['sort'] = [
            {
                "field_name": "dlhub.publication_date",
                "order": "desc"
            }
        ]
        return super().post_search(search_client, index_uuid, data)
