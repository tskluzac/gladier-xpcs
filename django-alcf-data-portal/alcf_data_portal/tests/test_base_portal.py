import pytest
from django.test import Client


@pytest.mark.django_db
def test_sanity():
    """This is a SUPER basic test to ensure everything in the portal loaded
    properly"""
    client = Client()
    response = client.get('/')
    assert response.status_code == 200
