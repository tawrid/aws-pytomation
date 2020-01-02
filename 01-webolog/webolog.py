import boto3
import click
from botocore.exceptions import ClientError
import json
from pathlib import Path
import mimetypes

session = boto3.Session(profile_name='python_automation')
s3 = session.resource('s3')


@click.group()
def cli():
    """Webolog deploys websites to AWS"""
    pass

@cli.command("list-buckets-objects")
@click.argument('bucket')
def list_buckets_objects(bucket):
    "List all S3 bucket objects"
    # bucket_list = list_buckets()
    # for bucket in bucket_list:
    #     obj = bucket.objects.all()
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)

@cli.command("list-buckets")
def list_buckets():
    "List all S3 buckets"
    bucket_list = []
    for bucket in s3.buckets.all():
        print(bucket)
        bucket_list.append(bucket)
    return bucket_list


@cli.command("setup-bucket")
@click.argument('bucket')
def setup_bucket(bucket):
    "Create and configure S3 bucket"
    s3_bucket = None
    region = session.region_name
    try:
        if region == 'us-east-1':
            s3_bucket = s3.create_bucket(
            Bucket=bucket
            )
        else:
            s3_bucket = s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={'LocationConstraint': region}
            )
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            s3_bucket = s3.Bucket(bucket)
        else:
            print("Unexpected error: %s" % e)

    print("Bucket name is {0}".format(s3_bucket.name))
    bucket_name = s3_bucket.name

    policy= {
        'Version': '2012-10-17',
        'Statement': [{
            'Sid': 'AddPerm',
            'Effect': 'Allow',
            'Principal': '*',
            'Action': ['s3:GetObject'],
            'Resource': f'arn:aws:s3:::{bucket_name}/*'
        }]
    }

    bucket_policy = json.dumps(policy)
    # policy.strip()

    pol = s3_bucket.Policy()
    try:
        pol.put(Policy=bucket_policy)
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'BucketAlreadyExists':
            print("Error occured while creating policy")
        else:
            print("Unexpected error: %s" % ce)

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
    except ClientError as ce:
          if ce.response['Error']['Code'] == 'Error':
              print("Error occured while creating website")
          else:
               print("Unexpected error: %s" % ce)

    # try:
    #     s3.Bucket(bucket).upload_file('index.html', 'index.html')
    # except ClientError as ce:
    #     if ce.response['Error']['Code'] == 'FileNotFoundError':
    #         print("Error occured while uploading file")
    #     else:
    #         print("Unexpected error: %s" % ce)
    return

def upload_file(s3_bucket, path, key):
    content_type = mimetypes.guess_type(key)[0] or 'text/plain'
    try:
        s3_bucket.upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': content_type
            }
        )
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'ParamValidationError':
            print("Error occured while creating website {0}".format(ce))
        else:
             print("Unexpected error: %s" % ce)
    return

@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    "Sync contents of PATHNAME to BUCKET"
    root = Path(pathname).expanduser().resolve()
    s3_bucket = s3.Bucket(bucket)

    def handle_directory(target):
        for p in target.iterdir():
            if p.is_dir(): handle_directory(p)
            if p.is_file(): upload_file(s3_bucket, str(p), str(p.relative_to(root)))
            # if p.is_file(): print("Path: {}\n Key: {}\n".format(p, p.relative_to(root)))
    handle_directory(root)

if __name__ == '__main__':
    cli()
