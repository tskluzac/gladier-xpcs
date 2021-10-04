# Concierge App

This is a Django App intended to bring the [Concierge Service](https://github.com/fair-research/concierge) to Globus Portal Framework
(and in turn the ALCF Data Portal). It adds capabilities for shopping cart-like functionality,
creating bags from user collected search results, and additional capabilites such as
submitting those collections to MDF for publication.

The Concierge App was built to be separate from the ALCF project, kept here only for a minor
convenience. It will likely be moved into it's own project at some point.

## Installation


Add to INSTALLED_APPS in `settings.py` and call `python manage.py migrate`
```
INSTALLED_APPS = [
    'concierge_app',
]
```

Add your index to the concierge service:
```
# Adding only select indices can be done here. Default enables all indices.
# CONCIERGE_INDEXES = ['my-index']
```

Link to the concierge service:
```
<a href="{% url 'concierge-app:bag-list' globus_portal_framework.index %}">My Bags</a>
```