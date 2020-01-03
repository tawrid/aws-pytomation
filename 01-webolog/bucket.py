# -*- coding: utf-8 -*-

"""Classes for S3 Bucket."""
import json

import mimetypes
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from hashlib import md5

from functools import reduce

import util


class BucketManager:
    """Manage an S3 Bucket."""
    CHUNK_SIZE = 8388608
    def __init__(self, session):
        """Create BucketManager Object."""
        self.session = session
        self.s3 = self.session.resource('s3')
        self.manifest = {}
        self.transfer_config = boto3.s3.transfer.TransferConfig(
            multipart_chunksize = self.CHUNK_SIZE,
            multipart_threshold = self.CHUNK_SIZE
        )



    def get_region_name(self, bucket):
        """Get the bucket's region name."""
        bucket_location = self.s3.meta.client.get_bucket_location(
            Bucket=bucket.name)
        return bucket_location["LocationConstraint"] or "us-east-1"

    def get_bucket_url(self, bucket):
        """Get the website URL for the bucket."""
        return "http://{0}.{1}".format(
            bucket.name,
            util.get_endpoint(self.get_region_name(bucket)).host)

    def get_all_buckets(self):
        """List all S3 buckets."""
        return self.s3.buckets.all()

    def get_all_buckets_objects(self, bucket_name):
        """List all S3 buckets Objects."""
        return self.s3.Bucket(bucket_name).objects.all()

    def load_manifest(self, bucket):
        """Load manifest for caching purposes."""
        paginator = self.s3.meta.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket.name):
            # print("Page is {}".format(page))
            for obj in page.get('Contents', []):
                self.manifest[obj['Key']] = obj['ETag']



    def init_bucket(self, bucket_name):
        """Initialize the S3 Bucket."""
        s3_bucket = None
        region = self.session.region_name
        try:
            if region == 'us-east-1':
                s3_bucket = self.s3.create_bucket(Bucket=bucket_name)
            else:
                s3_bucket = self.s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={
                        'LocationConstraint': region})
        except ClientError as error:
            if error.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                s3_bucket = self.s3.Bucket(bucket_name)
            else:
                print("Unexpected error: %s" % error)

        print("Bucket name {0} is created.".format(s3_bucket.name))
        return s3_bucket

    # pylint: disable=R0201
    def create_policy(self, s3_bucket):
        """Create S3 policy."""
        policy = {
            'Version': '2012-10-17',
            'Statement': [{
                'Sid': 'AddPerm',
                'Effect': 'Allow',
                'Principal': '*',
                'Action': ['s3:GetObject'],
                'Resource': f'arn:aws:s3:::{s3_bucket.name}/*'
            }]
        }

        bucket_policy = json.dumps(policy)
        pol = s3_bucket.Policy()
        try:
            pol.put(Policy=bucket_policy)
        except ClientError as error:
            if error.response['Error']['Code'] == 'BucketAlreadyExists':
                print("Error occured while creating policy")
            else:
                print("Unexpected error: %s" % error)
        # return

    # pylint: disable=R0201
    def create_website(self, s3_bucket):
        """Create the Website."""
        ws = s3_bucket.Website()
        try:
            ws.put(
                WebsiteConfiguration={
                    'ErrorDocument': {
                        'Key': 'error.html'
                    },
                    'IndexDocument': {
                        'Suffix': 'index.html'
                    }
                })
        except ClientError as error:
            if error.response['Error']['Code'] == 'Error':
                print("Error occured while creating website")
            else:
                print("Unexpected error: %s" % error)
        # return

    @staticmethod
    def has_data(data):
        """Generate Hash."""
        hash = md5()
        hash.update(data)
        return hash

    def gen_etag(self, path):
        """Generate ETag."""
        hashes = []
        with open(path, 'rb') as file:
            while True:
                data = file.read(self.CHUNK_SIZE)
                if not data:
                    break
                hashes.append(self.has_data(data))
        if not hashes:
            return
        elif len(hashes) == 1:
            return '"{}"'.format(hashes[0].hexdigest())
        else:
            hash = self.has_data(reduce(lambda x, y: x + y, (h.digest() for h in hashes)))
            return '"{}-{}"'.format(hash.hexdigest(), len(hashes))

    @staticmethod
    def upload_file(self, s3_bucket, path, key_path):
        """Upload file to the bucket."""
        content_type = mimetypes.guess_type(key_path)[0] or 'text/plain'
        etag = self.gen_etag(path)
        if self.manifest.get(key_path, '') == etag:
            print("Skipping {}, ETAG chunk.....".format(key_path))
            return

        try:
            s3_bucket.upload_file(
                path,
                key_path,
                ExtraArgs={
                    'ContentType': content_type
                },
                Config = self.transfer_config
            )
        except ClientError as error:
            if error.response['Error']['Code'] == 'ParamValidationError':
                print("Error occured while creating website {0}".format(error))
            else:
                print("Unexpected error: %s" % error)
        # return

    def sync_file(self, pathname, bucket_name):
        """Sync the file between local and S3 bucket."""
        s3_bucket = self.s3.Bucket(bucket_name)
        self.load_manifest(s3_bucket)
        root = Path(pathname).expanduser().resolve()

        def handle_directory(target):
            """Handle directory or files."""
            for path in target.iterdir():
                if path.is_dir():
                    handle_directory(path)
                if path.is_file():
                     self.upload_file(
                        self,
                        s3_bucket,
                        str(path),
                        str(path.relative_to(root)))
        handle_directory(root)
        print("The file(s) and folder(s) are synced to S3")
        # return
