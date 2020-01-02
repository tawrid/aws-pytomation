#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Webolog Deploys websites to AWS automatically.

The script manages AWS S3:
  - Creates Buckets.
  - Lists Bucket.
  - Lists Bucket objects.
  - Syncs the website files from local directory.
"""

import click

import boto3
from bucket import BucketManager

SESSION = boto3.Session(profile_name='python_automation')
BUCKET_MANAGER = BucketManager(SESSION)


@click.group()
def cli():
    """Webolog deploy website to AWS S3."""
    # pass


@cli.command("list-buckets-objects")
@click.argument('bucket_name')
def list_buckets_objects(bucket_name):
    """List all S3 bucket objects."""
    for obj in BUCKET_MANAGER.get_all_buckets_objects(bucket_name):
        print(obj)


@cli.command("list-buckets")
def list_buckets():
    """List all S3 buckets."""
    bucket_list = []
    for bucket in BUCKET_MANAGER.get_all_buckets():
        print(bucket)
        bucket_list.append(bucket)
    return bucket_list


@cli.command("setup-bucket")
@click.argument('bucket_name')
def setup_bucket(bucket_name):
    """Create and configure S3 bucket."""
    s3_bucket = BUCKET_MANAGER.init_bucket(SESSION, bucket_name)
    BUCKET_MANAGER.create_policy(s3_bucket)
    BUCKET_MANAGER.create_website(s3_bucket)
    # return


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket_name')
def sync(pathname, bucket_name):
    """Sync contents of PATHNAME to BUCKET."""
    BUCKET_MANAGER.sync_file(pathname, bucket_name)
    # return


if __name__ == '__main__':
    cli()
