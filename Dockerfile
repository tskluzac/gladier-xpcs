FROM python:3.8

COPY . /src

# RUN pip install git+https://github.com/globus/django-globus-portal-framework#egg=django-globus-portal-framework
RUN pip install -r /src/requirements-portal.txt
RUN cd src && python3 setup.py develop
RUN cd src/django-alcf-data-portal && pip install .
RUN pip install isodate
RUN cd /src/xpcs_portal && python3 manage.py migrate
# RUN cd /src/xpcs_portal && python manage.py runserver localhost:8000

COPY xpcs_portal/xpcs_index/templates/xpcs/global/tabbed-project/landing-page.html /src
COPY django-alcf-data-portal/alcf_data_portal/static /static
COPY django-alcf-data-portal/alcf_data_portal/static /src/static

EXPOSE 5000
EXPOSE 8000

WORKDIR /src
RUN pip install flask
RUN pip uninstall globus_sdk -y
RUN pip install globus_sdk==2.0.1

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
