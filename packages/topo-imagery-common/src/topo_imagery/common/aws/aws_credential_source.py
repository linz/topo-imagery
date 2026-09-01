from dataclasses import dataclass


# pylint: disable=too-many-instance-attributes
@dataclass
class CredentialSource:
    bucket: str
    """Base bucket location may be a subset of bucket"""
    type: str
    """Type of role assumption generally "s3"""
    prefix: str
    """
    Prefix for what the role is valid, generally starts with s3://
    """
    accountId: str
    """
    AWS Account id of the bucket owner
    """
    roleArn: str
    """
    Role arn to use
    """
    externalId: str | None = None
    """
    Role external ID if it exists
    """
    roleSessionDuration: int | None = 1 * 60 * 60
    """
    Max duration of the assumed session in seconds, default 1 hours
    """
    flags: str | None = None
    """
    flags that the role can use either "r" for read-only or "rw" for read-write
    """
