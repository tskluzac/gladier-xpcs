
import globus_sdk
from fair_research_login import NativeClient


def globus_native_auth_login():
    client = NativeClient(client_id='7414f0b4-7d05-4bb6-bb00-076fa3f17cf5')
    tokens = client.login(
        requested_scopes=['https://auth.globus.org/scopes/56ceac29-e98a-440a-a594-b41e7a084b62/all',
                          'urn:globus:auth:scope:transfer.api.globus.org:all',
                          "https://auth.globus.org/scopes/facd7ccc-c5f4-42aa-916b-a0e270e2c2a9/all",
                          "urn:globus:auth:scope:data.materialsdatafacility.org:all",
                          'email', 'openid', 'urn:globus:auth:scope:search.api.globus.org:all'],
        no_local_server=True,
        no_browser=True, force=False)

    return tokens

''' FROM INDEX CREATION
{
  "@datatype": "GSearchIndex",
  "@version": "2017-09-01",
  "creation_date": "2021-08-30 18:05:20",
  "description": "xtract-xpcs-entry",
  "display_name": "xtract-xpcs",
  "id": "344688c6-cff6-49c7-9bc5-e2fa3c5fedd2",
  "is_trial": true,
  "max_size_in_mb": 1,
  "num_entries": 0,
  "num_subjects": 0,
  "size_in_mb": 0,
  "status": "open",
  "subscription_id": null
}
'''
index_id = "344688c6-cff6-49c7-9bc5-e2fa3c5fedd2"
tokens = globus_native_auth_login()
search_ac = tokens['search.api.globus.org']['access_token']

# exit()
sc = globus_sdk.SearchClient(authorizer=globus_sdk.authorizers.AccessTokenAuthorizer(access_token=search_ac))

# sc.create_entry(index_id=index_id,
#                 data={
#                     "subject": "hello",
#                     "visible_to": ["public"],
#                     "content": {
#                         "foo/bar": "some val"
#                     }
#                 })

entry_data = sc.get_entry(index_id=index_id, subject='hello')
print(entry_data)