import pytest
from concierge_app import forms


@pytest.mark.django_db
def test_search_col_to_model(raw_search_data, admin_client,
                             mock_globus_sdk_search, dgpf_settings):
    mock_globus_sdk_search.post_search.return_value.data = raw_search_data
    subs = ['globus://e55b4eab-6d04-11e5-ba46-22000b92c6ec/'
            'XPCSDATA/test/nick-testing/demotest3']
    data = {'index': 'test_index',
            'name': 'mysearch',
            'query': '*',
            'filters': forms.SubjectSelectBagCheckoutForm.encode_filters(
                [{'myfil': 'filter'}]
            ),
            'project': 'fooproject',
            'user': admin_client,
            'search_kwargs': {},
            'metadata': {'foo': 'bar'},
            'subjects': subs,
            'search_url': 'foo.example.com'
            }

    form = forms.SubjectSelectBagCheckoutForm(data)
    assert not form.errors
    scol = form.get_search_collector()
    assert len(raw_search_data['gmeta']) == 3
    assert len(scol.search_data['gmeta']) == 1
    assert len(scol.get_sources()) == 2
    assert len(scol.get_manifest()) == 2
