import boto3
import os
from pathlib import Path
from tempfile import gettempdir
from botocore.client import ClientError
import click

from botocore import credentials
# create an STS client object that represents a live connection to the 
# STS service
sts_client = boto3.client('sts')

def download_s3_obj(sess_name:str, **kwargs) -> Path: 

    role_arn = kwargs["role_arn"]
    bucket = kwargs["bucket"]
    key = kwargs["key"]
  
    s3 = boto3.resource('s3',**creds(sess_name,role_arn))
    
    tmp_dir = Path(gettempdir(),f"tf_migrate-{os.getpid()}", bucket,key)
    
    os.makedirs(str(tmp_dir.parent.absolute()),exist_ok = False)

    s3.meta.client.download_file(bucket, key, str(tmp_dir.absolute()))
    return tmp_dir

def upload_s3_obj(file:Path,sess_name:str,**kwargs): 
    role_arn = kwargs["role_arn"]
    bucket = kwargs["bucket"]
    key = kwargs["key"]
    s3 = boto3.resource('s3',**creds(sess_name,role_arn))
    
    try:
        object = s3.Object(bucket,key)
        object.load()
        if not click.confirm("ops, file exist in s3. Overwrite?"):
            print("aborted.")
            return
    except ClientError as ex:
        pass # This is what we prefer, 404 basically

    s3.meta.client.upload_file(str(file.absolute()), bucket, key )

def creds(sess_name:str, role_arn:str) -> dict:

    assumed_role = sts_client.assume_role( RoleArn=role_arn,
                                               RoleSessionName=sess_name )
    credentials = assumed_role['Credentials']
    return {
        'aws_access_key_id' : credentials['AccessKeyId'],
        'aws_secret_access_key' : credentials['SecretAccessKey'],
        'aws_session_token' : credentials['SessionToken']
        }

