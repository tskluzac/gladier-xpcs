import pytest
import os
import json
from unittest.mock import Mock
from django.contrib.auth.models import User
import globus_sdk
from globus_portal_framework import gsearch as dgpf_search
import mdf_connect_client
from concierge_app.models import SearchCollection
from concierge_app.search import SearchCollector

FILES_DIR = os.path.join(os.path.dirname(__file__), 'files')
RAW_SEARCH_DATA = os.path.join(FILES_DIR, 'search_test_data.json')


@pytest.fixture
def test_pass():
    return 'test_pass'


@pytest.fixture
@pytest.mark.django_db
def test_user(test_pass):
    u = User(username='bob', password=test_pass)
    u.save()
    return u


@pytest.fixture
@pytest.mark.django_db
def auth_client(client, test_user, test_pass):
    client.login(
       username=test_user.username, password=test_pass
    )
    return client


@pytest.fixture
def raw_search_data():
    with open(RAW_SEARCH_DATA) as f:
        return json.load(f)


@pytest.fixture
@pytest.mark.django_db
def mock_search_collection(raw_search_data, admin_user):
    subjects = [r['subject'] for r in raw_search_data['gmeta']]
    sdata = json.dumps(subjects)
    scol = SearchCollection(
        index='xpcs', user=admin_user, query='*', subjects_data=sdata,
        filters_data='[]', cached_search_data=json.dumps(raw_search_data))
    scol.save()
    return scol


@pytest.fixture
def mock_search_collector(raw_search_data):
    scol = SearchCollector(
        index='xpcs', query='*', filters=[], search_data=raw_search_data
    )
    return scol


@pytest.fixture
def mock_get_index(monkeypatch):
    gi = Mock(return_value={'uuid': 'globus-search-index'})
    monkeypatch.setattr(dgpf_search, 'get_index', gi)
    return gi


@pytest.fixture
def mock_globus_sdk_response():
    class MockGlobusSDKResponse:
        data = {}
    return MockGlobusSDKResponse()


@pytest.fixture
def mock_globus_sdk_search(monkeypatch, raw_search_data,
                           mock_globus_sdk_response):
    sc_instance = Mock()
    sc = Mock(return_value=sc_instance)
    monkeypatch.setattr(globus_sdk, 'SearchClient', sc)
    mock_globus_sdk_response.data = raw_search_data
    sc_instance.post_search.return_value = mock_globus_sdk_response
    return sc


@pytest.fixture
def mock_mdf_connect_client_submit(monkeypatch):
    mock_submit = Mock()
    monkeypatch.setattr(mdf_connect_client.MDFConnectClient, 'submit_dataset',
                        mock_submit)
    return mock_submit
