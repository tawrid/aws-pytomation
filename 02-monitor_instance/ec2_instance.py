# coding: utf-8
import boto3
import os, stat

session = boto3.Session(profile_name='python_automation')
ec2 = session.resource('ec2')
key_name = 'python_automation_key'
key_path = key_name + '.pem'
key = ec2.create_key_pair(KeyName=key_name)
key.key_material
with open(key_path, 'w') as key_file:
    key_file.write(key.key_material)

os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)

# get_ipython().run_line_magic('ls', '-l python_automation_key.pem')

img = ec2.Image('ami-00068cd7555f543d5')
img_name = 'amzn2-ami-hvm-2.0.20191116.0-x86_64-gp2'
filters = [{'Name': 'name', 'Values': [img_name]}]
list(ec2.images.filter(Owners=['amazon'], Filters=filters))
img = list(ec2.images.filter(Owners=['amazon'], Filters=filters))[0]
instance = ec2.create_instances(ImageId=img.id, MinCount=1, MaxCount=1, InstanceType='t2.micro', KeyName=key.name)
inst = instance[0]
inst.public_dns_name
inst.wait_until_running()
sg = ec2.SecurityGroup(inst.security_groups[0]['GroupId'])
sg.authorize_ingress(IpPermissions=[{'FromPort': 22, 'ToPort': 22, 'IpProtocol': 'TCP', 'IpRanges': [{'CidrIp': '157.119.61.165/32'}]}])
sg.authorize_ingress(IpPermissions=[{'FromPort': 80, 'ToPort': 80, 'IpProtocol': 'TCP', 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}])
