import argparse
import json
from typing import Any

import boto3
from linz_logger import get_log

from scripts.datetimes import format_rfc_3339_datetime_string
from scripts.files.fs import read
from scripts.files.fs_s3 import bucket_name_from_path, prefix_from_path


def load_versions(path: str) -> dict[str, any]:
    s3_client = boto3.client("s3")
    versions = s3_client.list_object_versions(Bucket=bucket_name_from_path(path), Prefix=prefix_from_path(path))
    return sorted(versions.get("Versions", []), key=lambda v: v["LastModified"])


def get_object_version_modified_dates(versions: dict[str, Any]) -> list[str]:
    modified_dates = []
    for version in versions:
        modified_dates.append(format_rfc_3339_datetime_string(version["LastModified"]))

    return modified_dates


def get_latest_version_modified_date(versions: dict[str, Any]) -> str:
    for version in versions:
        if version["IsLatest"]:
            return version["LastModified"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("collection_path")
    arguments = parser.parse_args()
    collection_path = arguments.collection_path

    # Retrieve Collection modified dates
    collection_versions = load_versions(collection_path)
    collection_modified_dates = get_object_version_modified_dates(collection_versions)
    collection_updated_date = get_latest_version_modified_date(collection_versions)
    get_log().info("Versions", count=len(collection_modified_dates))
    # Load Collection object
    collection = json.loads(read(collection_path))
    collection["links"] = {}
    get_log().info("Load Collection", collection=collection)

    collection["created"] = collection_modified_dates[0]
    collection["updated"] = format_rfc_3339_datetime_string(collection_updated_date)

    get_log().info("Updated Collection", collection=collection)


if __name__ == "__main__":
    main()
