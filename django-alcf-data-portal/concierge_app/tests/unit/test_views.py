
import pytest

from django.urls import reverse


def test_bag_list(admin_client):
    url = reverse('concierge-app:bag-list', kwargs={'index': 'testindex'})
    response = admin_client.get(url)
    assert response.status_code == 200


def test_bag_checkout(admin_client):
    url = reverse('concierge-app:bag-project-checkout',
                  kwargs={'index': 'testindex', 'project': 'test'})
    response = admin_client.get(url)
    assert response.status_code == 200


def test_bag_checkout_project(admin_client):
    url = reverse('concierge-app:bag-project-checkout',
                  kwargs={'index': 'testindex', 'project': 'test'})
    response = admin_client.get(url)
    assert response.status_code == 200


def test_post_checkout_project_bag_without_args(admin_client):
    url = reverse('concierge-app:bag-project-checkout',
                  kwargs={'index': 'testindex', 'project': 'test'})
    response = admin_client.post(url)
    assert response.status_code == 200


@pytest.mark.xfail
def test_post_checkout_project_bag(admin_client):
    """POST valid args to create a bag"""
    url = reverse('concierge-app:bag-project-checkout',
                  kwargs={'index': 'testindex', 'project': 'test'})
    response = admin_client.post(url, data={'validargs'})
    assert response.status_code == 200


def test_mdf_connect_client_submit_bag_args(admin_client):
    url = reverse('concierge-app:mdf-connect-submission',
                  kwargs={'index': 'testindex'})
    data = {'title': 'my_publication'}
    response = admin_client.post(url, data=data)
    assert response.status_code == 302


@pytest.mark.django_db
@pytest.mark.xfail
def test_mdf_connect_client_submit(admin_client, mock_search_collection,
                                   mock_mdf_connect_client_submit):
    """# TODO: Mock auth so we're not attempting to grab an MDF token"""
    url = reverse('concierge-app:mdf-connect-submission',
                  kwargs={'index': 'testindex'})
    data = {'title': 'My Fancy Publication',
            'search_collection': mock_search_collection.id}
    response = admin_client.post(url, data=data)
    assert response.status_code == 200
    print(mock_mdf_connect_client_submit.call_args)
    assert mock_mdf_connect_client_submit.called
