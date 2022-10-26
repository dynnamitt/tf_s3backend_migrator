import boto3
from pathlib import Path
from tempfile import gettempdir
# create an STS client object that represents a live connection to the 
# STS service
sts_client = boto3.client('sts')

def download_s3_obj(sess_name:str, **kwargs) -> Path: 

    role_arn = kwargs["role_arn"]
    bucket = kwargs["bucket"]
    key = kwargs["key"]

    assumed_role_object=sts_client.assume_role( RoleArn=role_arn,
                                               RoleSessionName=sess_name )

    credentials = assumed_role_object['Credentials']
    
    s3 = boto3.resource('s3',
        aws_access_key_id = credentials['AccessKeyId'],
        aws_secret_access_key = credentials['SecretAccessKey'],
        aws_session_token = credentials['SessionToken'])

    tmp_dir = Path(gettempdir(),bucket,key)

    s3.download_file(bucket, key, tmp_dir.absolute())
    return tmp_dir
