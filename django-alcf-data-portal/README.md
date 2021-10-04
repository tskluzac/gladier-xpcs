# ALCF Data Portal


This is a portal which provides a very thin wrapper around [Django Globus
Portal Framework](https://github.com/globusonline/django-globus-portal-framework).
You will need Github access to the core library for the installation
steps below to work, ping nick@globus.org for read access, then the steps below
will get you started with a locally running portal.

## Installation

### Locally
Clone and install the App locally:

```
    $ git clone https://github.com/globusonline/django-alcf-data-portal.git
    $ cd django-alcf-data-portal.git
    $ pip install -r requirements.txt
```

Create a Globus App at [developers.globus.org](https://developers.globus.org),
and make sure `http://localhost:8000/complete/globus/` is included in
'Redirect URLs'.

Add the keys to your local config file below:

alcf_data_portal/local_settings.py
```
from django.conf import settings
DEBUG = True
ALLOWED_HOSTS = ['*']
SECRET_KEY = 'thing you generate with `openssl rand -hex 32`'
SOCIAL_AUTH_GLOBUS_KEY = 'Add your App Client ID here, from developers.globus.org'
SOCIAL_AUTH_GLOBUS_SECRET = 'Add your App Client Secret here, from developers.globus.org'
settings.LOGGING['handlers']['stream']['level'] = 'DEBUG'
```

Now just run migrations, and start the server

```
    $ python manage.py migrate
    $ python manage.py runserver
```

The app will be running locally at `http://localhost:8000`

### On a server

This app is intended to be run through WSGI. Static files can be copied
to a location your favorite webserver can serve them through:

    $ python manage.py collectstatic

Configure the filesystem location where files should be collected with
`settings.STATIC_ROOT` and the URL this webapp should expect them with
`settings.STATIC_URL`.
