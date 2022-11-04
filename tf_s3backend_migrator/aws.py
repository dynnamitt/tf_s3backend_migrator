from dataclasses import dataclass
import boto3
import os
from pathlib import Path
import click
from botocore.client import ClientError
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
    try:
        s3object = s3.Object(bucket, key)
        s3object.load()
        if not click.confirm("ops, file exist in s3. Overwrite?"):
            print("aborted.")
            return
    except ClientError as ex:
        pass  # This is what we prefer, 404 basically

    s3.meta.client.upload_file(str(file.absolute()), bucket, key)


class AwsArn:
    def __init__(self, arn: str):

        # http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
        elements = arn.split(":")
        result = {
            "arn": elements[0],
            "partition": elements[1],
            "service": elements[2],
            "region": elements[3],
            "account": elements[4],
        }
        if len(elements) == 7:
            result["resourcetype"], result["resource"] = elements[5:]
        elif "/" not in elements[5]:
            result["resource"] = elements[5]
            result["resourcetype"] = None
        else:
            result["resourcetype"], result["resource"] = elements[5].split("/")

        self.__dict__ = result
