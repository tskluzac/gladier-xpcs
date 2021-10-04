from unittest.mock import Mock
import pytest
from concierge_app.search import SearchCollector
from concierge_app.models import SearchCollection


def test_collector_get_manifest(mock_search_collector):
    man = mock_search_collector.get_manifest()
    assert len(man) == 5


def test_collector_sanity_gmeta(mock_search_collector):
    assert len(mock_search_collector.search_data['gmeta']) == 3


def test_search_collector_insufficient_data(mock_get_index):
    sc = SearchCollector(index='foo', query=None)
    assert sc.search_data == {'gmeta': [], 'count': 0}


def test_search_collector_post_search(mock_search_collector,
                                      mock_globus_sdk_search, mock_get_index):
    user = Mock(is_authenticated=False)
    sc = SearchCollector('index', name='mysearch', query='*', filters=[],
                         project='fooproject', search_data=None, user=user,
                         search_kwargs={}, metadata={}
                         )
    assert sc.search_data
    assert len(sc.get_manifest()) == 5


@pytest.mark.django_db
def test_search_col_to_model(raw_search_data, test_user):
    sc = SearchCollector(
        'index', name='mysearch', query='*', filters=[{'myfil': 'filter'}],
        project='fooproject', search_data=raw_search_data, user=test_user,
        search_kwargs={}, metadata={'foo': 'bar'}
    )
    sc_mod = SearchCollection.create(test_user, sc)
    esc = sc_mod.get_search_collector()
    assert esc.index == 'index'
    assert esc.name == 'mysearch'
    assert esc.query == '*'
    assert esc.filters == [{'myfil': 'filter'}]
    assert esc.project == 'fooproject'
    assert esc.metadata == {'foo': 'bar'}
