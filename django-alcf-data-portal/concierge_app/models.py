import json
import requests
import logging
import globus_sdk
from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from django.urls import reverse
from globus_portal_framework.gclients import (load_globus_access_token,
                                              load_transfer_client)
# The Concierge client should be replaced with a Manifest API
# from concierge.api import manifest_create, manifest_info, manifest_stage
# MDF Tooling is used for publishing, but is disabled at the moment
# This doesn't really belong in the Concierge/Manifest app anyway.
# from mdf_connect_client import MDFConnectClient
# from mdf_toolbox import KNOWN_TOKEN_KEYS
from concierge_app import search, exc, CONCIERGE_RESOURCE_SERVER

try:
    from minid import MinidClient
except ImportError:
    MinidClient = None

BASE_CONCIERGE_URL = 'https://develop.concierge.nick.globuscs.info/api'

log = logging.getLogger(__name__)


class Manifest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    manifest_id = models.UUIDField()
    index = models.CharField(max_length=128)
    date_created = models.DateTimeField(auto_now_add=True)
    cache = models.TextField(default='{}')
    search_collection = models.ForeignKey('SearchCollection',
                                          on_delete=models.CASCADE,
                                          null=True)

    @property
    def metadata(self):
        return json.loads(self.cache or '{}')

    @property
    def minid_hdl(self):
        try:
            return MinidClient.to_identifier(self.minid, identifier_type='hdl')
        except Exception:
            return self.minid

    @metadata.setter
    def metadata(self, value):
        self.cache = json.dumps(value or {})

    @property
    def mdf_submission(self):
        mcs = MDFCollectionSubmission.get_user_submission(
            self.user, self.search_collection)
        if mcs and mcs.is_active():
            log.debug(f'MDF Submission active! '
                      f'Fetching results for {mcs}...')
            mcs.check_status()
        return mcs

    @classmethod
    def create(cls, user, search_collector):
        ctoken = load_globus_access_token(user, CONCIERGE_RESOURCE_SERVER)
        index = search_collector.index
        metadata = search_collector.get_manifest_metadata()
        manifest = search_collector.get_manifest()
        log.debug(f'Publishing Manifest from {search_collector} with {len(manifest)} '
                  f'entries')
        # minid = manifest_create(
        #     manifest,
        #     ctoken,
        #     minid_test=settings.MINID_TEST,
        #     minid_metadata=metadata,
        #     manifest_metadata=metadata,
        #     manifest_name=search_collector.name
        # )
        # cached_meta = copy.deepcopy(metadata)
        # cached_meta['minid_test'] = minid['minid_test']
        # location = manifest_info([minid['minid']])[0]['location'][0]
        # cached_meta['location'] = location
        # cached_meta['total_size'] = sum([m['length'] for m in manifest])
        search_col = SearchCollection.create(user, search_collector)

        headers = {'Authorization': f'Bearer {ctoken}'}
        gm = search_collector.remote_file_manifest_to_globus_manifest(manifest)
        url = f'{BASE_CONCIERGE_URL}/manifest/globus_manifest/'
        result = requests.post(url, headers=headers, json={'manifest_items': gm})
        try:
            result.raise_for_status()
            rjson = result.json()
            manifest = Manifest(user=user, index=index, manifest_id=rjson['manifest_id'],
                                metadata=metadata, search_collection=search_col)
            manifest.save()
            return manifest
        except requests.exceptions.HTTPError as he:
            raise exc.ConciergeError(he)


    @classmethod
    def get_user_manifest(cls, user, manifest_id):
        manifest = Manifest.objects.filter(id=manifest_id, user=user).first()
        return manifest or None

    def delete(self):
        ctoken = load_globus_access_token(self.user, CONCIERGE_RESOURCE_SERVER)
        headers = {'Authorization': f'Bearer {ctoken}'}
        url = f'{BASE_CONCIERGE_URL}/manifest/{self.manifest_id}/'
        r = requests.delete(url, headers=headers)
        log.debug(f'User Deletion of Manifest: {r}')
        return super().delete()

    def __str__(self):
        return f'Manifest {self.id} - {self.date_created}'


class ManifestTransfer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    manifest = models.ForeignKey(Manifest, on_delete=models.CASCADE)
    manifest_transfer_id = models.UUIDField()
    index = models.CharField(max_length=32)
    # concierge_id = models.IntegerField()
    date_created = models.DateTimeField(auto_now_add=True)
    cache = models.TextField(default='{}')

    def update_task(self):
        # if self.is_active() is False:
        #     return
        log.debug('Updating Stage Manifest: {} ({})'.format(self, self.user))
        ctoken = load_globus_access_token(self.user, CONCIERGE_RESOURCE_SERVER)
        headers = {'Authorization': f'Bearer {ctoken}'}
        turl = (f'{BASE_CONCIERGE_URL}'
                f'/manifest/{self.manifest.manifest_id}'
                f'/transfer/{self.manifest_transfer_id}/')
        r = requests.get(turl, headers=headers)
        r.raise_for_status()
        self.metadata = r.json()
        self.save()

    @property
    def metadata(self):
        return json.loads(self.cache or '{}')

    @metadata.setter
    def metadata(self, value):
        self.cache = json.dumps(value or {})

    @property
    def status(self):
        return self.metadata.get('status')

    @property
    def bytes_transferred(self):
        return sum(t['bytes_transferred'] for t in self.metadata['transfers'])

    @property
    def files_transferred(self):
        return sum(t['files'] for t in self.metadata['transfers'])

    def is_active(self):
        return self.status == 'ACTIVE'

    def cancel_transfer(self):
        tc = load_transfer_client(self.user)
        for transfer in self.metadata['transfers']:
            try:
                log.debug('Canceling Transfer task on manifest {} for user {} '
                          '(task_id: {})'.format(self, self.user,
                                                 transfer['task_id']))
                tc.cancel_task(transfer['task_id'])
            except Exception as e:
                log.exception(e)
        log.info('Canceled Stage for {} (user: {})'.format(self, self.user))

    def remove(self):
        if self.is_active():
            self.cancel_transfer()
        log.info('Removed manifest: {} ({})'.format(self, self.user))
        ManifestTransfer.delete(self.id)

    @classmethod
    def manifest_transfer(cls, user, index, manifest_id, endpoint, path, label):
        ctoken = load_globus_access_token(user, CONCIERGE_RESOURCE_SERVER)
        manifest = Manifest.get_user_manifest(user, manifest_id)
        if manifest is None:
            return
        if not index:
            raise ValueError('Index is invalid!')
        if not endpoint:
            raise ValueError('Endpoint is invalid!')

        headers = {'Authorization': f'Bearer {ctoken}'}
        url = f'{BASE_CONCIERGE_URL}/manifest/{manifest.manifest_id}/transfer/'
        dest = f'globus://{endpoint}{path}'
        result = requests.post(url, headers=headers, json={'destination': dest})
        try:
            result.raise_for_status()
            rjson = result.json()
            mt = ManifestTransfer(user=user, index=index, manifest=manifest,
                                  manifest_transfer_id=rjson['manifest_transfer_id'],
                                  metadata=rjson)
            mt.save()
            log.debug(f'User {user}: Transfer submission successful.')
            return mt
        except requests.exceptions.HTTPError as he:
            log.error(he.response.text)
            raise exc.ConciergeError(he)

    @classmethod
    def get_user_manifest(cls, user, manifest_id):
        manifest = ManifestTransfer.objects.filter(id=manifest_id, user=user).first()
        if manifest and manifest.is_active():
            manifest.update_task()
            manifest = ManifestTransfer.objects.get(id=manifest.id)
        return manifest or None


class SearchCollection(models.Model):
    """A search collection is simply a list of subjects, but it also ties the
    search to a user, captures the index, and contains functionality to
    resolve search data when needed."""
    index = models.CharField(max_length=128)
    project = models.CharField(default='', max_length=128)
    name = models.CharField(default='', max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=1024)
    subjects_data = models.TextField(default='[]')
    filters_data = models.TextField(default='[]')
    cached_search_data = models.TextField(default='{}')
    metadata_data = models.TextField(default='{}')
    date_created = models.DateTimeField(auto_now_add=True)

    @property
    def subjects(self):
        return json.loads(self.subjects_data or '[]')

    @property
    def search_data(self):
        return json.loads(self.cached_search_data or '{}')

    @property
    def metadata(self):
        return json.loads(self.metadata_data or '{}')

    @property
    def filters(self):
        return json.loads(self.filters_data or '[]')

    @classmethod
    def create(cls, user, search_collection):
        search_data = search_collection.search_data
        subjects = json.dumps([e['subject'] for e in search_data['gmeta']])

        scol = cls(index=search_collection.index,
                   name=search_collection.name,
                   project=search_collection.project,
                   filters_data=json.dumps(search_collection.filters),
                   user=user,
                   query=search_collection.query,
                   subjects_data=subjects,
                   metadata_data=json.dumps(search_collection.metadata),
                   cached_search_data=json.dumps(search_data))
        scol.save()
        return scol

    def get_search_collector(self, custom_class=None):
        cls = custom_class or search.SearchCollector
        return cls(index=self.index, name=self.name, query=self.query,
                   filters=self.filters, project=self.project,
                   search_data=self.search_data, user=self.user,
                   metadata=self.metadata)

    def __str__(self):
        return f'{super().__str__()}-{self.user}-{self.name}'


class MDFCollectionSubmission(models.Model):
    METADATA_STATUS = 'mdf_status_check'
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=256, default='')
    source_id = models.CharField(max_length=256)
    doi = models.CharField(max_length=256, default='')
    search_collection = models.ForeignKey(SearchCollection,
                                          on_delete=models.CASCADE)
    cache = models.TextField(default='{}')

    def get_absolute_url(self):
        return reverse('concierge-app:manifest-list',
                       kwargs={'index': self.search_collection.index})

    @property
    def metadata(self):
        return json.loads(self.cache or '{}')

    @metadata.setter
    def metadata(self, value):
        self.cache = json.dumps(value or {})

    @property
    def status(self):
        return self.metadata.get(self.METADATA_STATUS, {}).get('status', {})

    def is_active(self):
        return self.status.get('active', False)

    @classmethod
    def get_client(cls, user):
        try:
            token = load_globus_access_token(user,
                                             KNOWN_TOKEN_KEYS['mdf_connect'])
        except ValueError as ve:
            if 'Attempted to load mdf_dataset_submission' in str(ve):
                raise exc.MDFTokenAbsent()
        # This is a hack to get the MDF Client working. It doesn't currently
        # accept access tokens, so we need to hack it in there by creating a
        # fake refresh token authorizer. The GlobusSDK won't attempt to refresh
        # a token that is still valid, so setting the expiration time to now
        # plus a day works. If the token ever DOES expire, it will be auto-
        # refreshed by a subsequent login via load_globus_access_token() above.
        setattr(MDFConnectClient, '_MDFConnectClient__allowed_authorizers',
                [globus_sdk.AccessTokenAuthorizer])
        ata = globus_sdk.AccessTokenAuthorizer(token)
        return MDFConnectClient(authorizer=ata)

    @classmethod
    def get_related_dois_by_subject(cls, subjects):
        subsset = set(subjects)
        dois = [
            o.doi for o in cls.objects.all()
            if (o.doi and
                set(o.search_collection.get_search_collector().get_subjects())
                .intersection(subsset)
                )
        ]
        return dois

    @classmethod
    def get_source_name(self, title, index, project=None):
        test_prefix = '_test_' if settings.MDF_TEST else ''
        project = f'_{project}' if project is not None else ''
        if not title or not index:
            raise ValueError('Index and title are required fields.')
        new_title = f'{test_prefix}{title}_{index}{project}'.replace('-', '_')
        new_title.replace('-', '_').replace(' ', '_')
        return new_title

    def submit(self):

        sc = self.search_collection.get_search_collector()
        log.info(f'User {sc.user} creating MDF Publish submission using {sc} '
                 f'with {len(sc.get_subjects())} subjects '
                 f'and {len(sc.get_manifest())} files.')
        mdfcc = self.get_client(sc.user)
        dc = sc.get_dc_block()
        mdfcc.create_dc_block(
            title=self.title,
            authors=[c['creatorName'] for c in dc['creators']],
            subjects=[s['subject'] for s in dc['subjects']],
            related_dois=self.get_related_dois_by_subject(sc.get_subjects())
        )
        sources = sc.get_sources()
        for source in sources:
            mdfcc.add_data_source(source)

        # Add This organization and comment out the mdf_publish line below,
        # when we're ready for curation.
        # mdfcc.add_organization('XPCS 8-ID')
        mdfcc.add_service("mdf_publish")
        mdfcc.set_test(settings.MDF_TEST)
        source_name = self.get_source_name(self.title, sc.index, sc.project)
        mdfcc.set_source_name(source_name)

        submission_result = mdfcc.submit_dataset(update=False)
        if submission_result['success'] is not True:
            error = submission_result.get('error')
            if 'This dataset has already been submitted' in error:
                raise exc.MDFPreviousSubmission()
            elif 'You cannot access this service or organization' in error:
                raise exc.MDFAccessDenied()
            raise exc.MDFSubmissionError(submission_result.get('error'))

        self.source_id = submission_result['source_id']
        self.metadata = {self.METADATA_STATUS: {'status': {'active': True}}}
        self.save()
        return self

    def check_status(self):
        if self.is_active():
            metadata = self.metadata
            cli = self.get_client(self.user)
            metadata[self.METADATA_STATUS] = cli.check_status(
                source_id=self.source_id, raw=True)
            self.metadata = metadata
            self.save()

    def __str__(self):
        return self.source_id

    @classmethod
    def get_user_submission(cls, user, search_collection):
        return cls.objects.filter(
            user=user, search_collection=search_collection).first() or None
