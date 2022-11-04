import boto3
import os
from pathlib import Path
from tempfile import gettempdir

# create an STS client object that represents a live connection to the
# STS service
sts_client = boto3.client("sts")


def assume_role(role_arn, sess_name="tf_migrator") -> dict:
    o = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=sess_name)
    creds = o["Credentials"]
    return {
        "aws_access_key_id": creds["AccessKeyId"],
        "aws_secret_access_key": creds["SecretAccessKey"],
        "aws_session_token": creds["SessionToken"],
    }


def download_s3_obj(role_arn: str, bucket: str, key: str, **_) -> Path:

    s3 = boto3.resource("s3", **assume_role(role_arn))

    tmp_dir = Path(gettempdir(), f"tf_migrate-{os.getpid()}", bucket, key)

    os.makedirs(str(tmp_dir.parent.absolute()), exist_ok=False)

    s3.meta.client.download_file(bucket, key, str(tmp_dir.absolute()))
    return tmp_dir


def upload_to_s3(file: Path, role_arn: str, bucket: str, key: str, **_):

    s3 = boto3.resource("s3", **assume_role(role_arn))
    s3.meta.client.upload_file(str(file.absolute()), bucket, key)
    print("%")
