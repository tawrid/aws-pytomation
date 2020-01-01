import boto3
import click

session = boto3.Session(profile_name='python_automation')
s3 = session.resource('s3')


@click.group()
def cli():
    """Webolog deploys websites to AWS"""
    pass

@cli.command("list-buckets-objects")
def list_buckets_objects():
    "List all S3 bucket objects"
    # bucket_list = list_buckets()
    # for bucket in bucket_list:
    #     obj = bucket.objects.all()
    for obj in s3.Bucket('tawrid-test-website').objects.all():
        print(obj)

@cli.command("list-buckets")
def list_buckets():
    "List all S3 buckets"
    bucket_list = []
    for bucket in s3.buckets.all():
        print(bucket)
        bucket_list.append(bucket)
    return bucket_list


if __name__ == '__main__':
    cli()
