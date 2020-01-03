#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Webolog Deploys websites to AWS automatically.

The script manages AWS S3:
  - Creates Buckets.
  - Lists Bucket.
  - Lists Bucket objects.
  - Syncs the website files from local directory.
"""
import boto3
import click

from webolog.bucket import BucketManager

SESSION = None
BUCKET_MANAGER = None


@click.group()
@click.option("--profile", default=None,
              help="Use a given AWS profile")
def cli(profile):
    """Webolog deploy website to AWS S3."""
    global SESSION, BUCKET_MANAGER

    session_cfg = {}
    if profile:
        session_cfg['profile_name'] = profile
    SESSION = boto3.Session(**session_cfg)
    BUCKET_MANAGER = BucketManager(SESSION)


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
    s3_bucket = BUCKET_MANAGER.init_bucket(bucket_name)
    BUCKET_MANAGER.create_policy(s3_bucket)
    BUCKET_MANAGER.create_website(s3_bucket)
    # return


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket_name')
def sync(pathname, bucket_name):
    """Sync contents of PATHNAME to BUCKET."""
    BUCKET_MANAGER.sync_file(pathname, bucket_name)
    bucket_url = BUCKET_MANAGER.get_bucket_url(
        BUCKET_MANAGER.s3.Bucket(bucket_name))
    print(bucket_url)
    # return


if __name__ == '__main__':
    cli()
