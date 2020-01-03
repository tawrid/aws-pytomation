from setuptools import setup

setup(
    name="webolog",
    version="0.1",
    author="Tawrid Hyder",
    author_email="tawridnz@hotmail.com",
    description="Webolog is a tool to deploy static webpages to S3",
    license="GPLv3+",
    packages=['webolog'],
    url='https://github.com/tawrid/aws-pytomation',
    install_requires=[
        'boto3',
        'click'
    ],
    entry_points='''
        [console_scripts]
        webolog=webolog.webolog:cli
    '''
)
