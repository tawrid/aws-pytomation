# -*- coding: utf-8 -*-

"""Classes for S3 Bucket."""
import json

import mimetypes
from pathlib import Path
from botocore.exceptions import ClientError


class BucketManager:
    """Manage an S3 Bucket."""

    def __init__(self, session):
        """Create BucketManager Object."""
        self.s3 = session.resource('s3')

    def get_all_buckets(self):
        """List all S3 buckets."""
        return self.s3.buckets.all()

    def get_all_buckets_objects(self, bucket_name):
        """List all S3 buckets Objects."""
        return self.s3.Bucket(bucket_name).objects.all()

    def init_bucket(self, session, bucket_name):
        """Initialize the S3 Bucket."""
        s3_bucket = None
        region = session.region_name
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
    def upload_file(s3_bucket, path, key):
        """Upload file to the bucket."""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        try:
            s3_bucket.upload_file(
                path,
                key,
                ExtraArgs={
                    'ContentType': content_type
                }
            )
        except ClientError as error:
            if error.response['Error']['Code'] == 'ParamValidationError':
                print("Error occured while creating website {0}".format(error))
            else:
                print("Unexpected error: %s" % error)
        # return

    def sync_file(self, pathname, bucket_name):
        """Sync the file between local and S3 bucket."""
        root = Path(pathname).expanduser().resolve()
        s3_bucket = self.s3.Bucket(bucket_name)

        def handle_directory(target):
            """Handle directory or files."""
            for path in target.iterdir():
                if path.is_dir():
                    handle_directory(path)
                if path.is_file():
                    self.upload_file(
                        s3_bucket,
                        str(path),
                        str(path.relative_to(root)))
        handle_directory(root)
        print("The file(s) and folder(s) are synced to S3")
        # return
