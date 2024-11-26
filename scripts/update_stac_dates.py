import argparse
import json
import sys
from argparse import Namespace
from datetime import datetime
from functools import partial
from multiprocessing import Pool
from typing import Any

import boto3
import git
from linz_logger import get_log

from scripts.datetimes import format_rfc_3339_datetime_string, parse_rfc_3339_date
from scripts.files.files_helper import ContentType
from scripts.files.fs import read, write
from scripts.files.fs_s3 import bucket_name_from_path, prefix_from_path
from scripts.json_codec import dict_to_json_bytes
from scripts.logging.time_helper import time_in_ms
from scripts.stac.util import checksum


def load_versions(path: str) -> list[dict[str, Any]]:
    s3_client = boto3.client("s3")
    versions = s3_client.list_object_versions(Bucket=bucket_name_from_path(path), Prefix=prefix_from_path(path))
    return sorted(versions.get("Versions", []), key=lambda v: v["LastModified"])


def get_latest_version_modified_date(versions: list[dict[str, Any]]) -> datetime:
    for version in versions:
        if version["IsLatest"]:
            last_modified: datetime = version["LastModified"]
            return last_modified
    raise Exception("No latest version found")


def get_closest_date(input_date: datetime, date_list: list[datetime]) -> datetime:
    return min(date_list, key=lambda date: abs(date - input_date))


def run_update_item_dates(
    links_to_update: list[dict[str, Any]],
    dataset_path: str,
    output_path: str,
    items_dates: dict[str, Any],
    collection_commit_dates: list[datetime],
) -> list[dict[str, Any]]:
    """Run `update_item_dates()` in parallel"""
    # pylint: disable-msg=too-many-arguments

    with Pool(20) as p:
        updated_links = [
            entry
            for entry in p.map(
                partial(
                    update_item_dates,
                    dataset_path=dataset_path,
                    output_path=output_path,
                    items_dates=items_dates,
                    collection_commit_dates=collection_commit_dates,
                ),
                links_to_update,
            )
            if entry is not None
        ]
        p.close()
        p.join()

    return updated_links


def update_item_dates(
    link: dict[str, Any],
    dataset_path: str,
    output_path: str,
    items_dates: dict[str, datetime],
    collection_commit_dates: list[datetime],
) -> dict[str, Any]:
    if link["rel"] != "item":
        return link
    item_filename = link["href"].lstrip("./")
    item_path = f"{dataset_path}{item_filename}"
    item_published = json.loads(read(item_path))

    asset_filename = item_published["assets"]["visual"]["href"].lstrip("./")
    asset_path = f"{dataset_path}{asset_filename}"

    item_published["properties"]["created"] = format_rfc_3339_datetime_string(items_dates[link["href"]])
    item_published["properties"]["updated"] = format_rfc_3339_datetime_string(
        get_closest_date(
            get_latest_version_modified_date(load_versions(item_path)),
            collection_commit_dates,
        )
    )

    item_published["assets"]["visual"]["created"] = format_rfc_3339_datetime_string(items_dates[link["href"]])
    item_published["assets"]["visual"]["updated"] = format_rfc_3339_datetime_string(
        get_closest_date(
            get_latest_version_modified_date(load_versions(asset_path)),
            collection_commit_dates,
        )
    )
    item_content = dict_to_json_bytes(item_published)

    updated_link = link.copy()
    # TODO: discuss about should we add the checksum before doing this created and updated dates backfilling?
    updated_link["file:checksum"] = checksum.multihash_as_hex(item_content)
    write(f"{output_path}{item_filename}", item_content, content_type=ContentType.GEOJSON.value)

    return updated_link


def parse_args(args: list[str] | None) -> Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", dest="output", help="Output directory", required=True)
    parser.add_argument(
        "--collection-path",
        dest="collection_path",
        help="Path to published Collection of the dataset to backfill",
        required=False,
    )
    return parser.parse_args(args)


# pylint: disable-msg=too-many-locals
# pylint: disable-msg=too-many-statements
# pylint: disable-msg=too-many-branches
def main(args: list[str] | None = None) -> None:
    start_time = time_in_ms()
    arguments = parse_args(args)
    collection_published_path = arguments.collection_path
    clone_path = "/tmp/repo/"
    bucket_name = bucket_name_from_path(collection_published_path)

    if bucket_name == "nz-elevation":
        initial_date = parse_rfc_3339_date("2024-03-14")  # https://github.com/awslabs/open-data-registry/pull/2142
        git_repo = "https://github.com/linz/elevation.git"
    elif bucket_name == "nz-imagery":
        initial_date = parse_rfc_3339_date("2023-09-09")  # https://github.com/awslabs/open-data-registry/pull/1986
        git_repo = "https://github.com/linz/imagery.git"
    else:
        raise Exception(f"Bucket {bucket_name} is not a valid ODR bucket.")

    repo = git.Repo.clone_from(git_repo, clone_path)
    repo.git.checkout("master")

    collection_path_in_repo = collection_published_path.replace(f"s3://{bucket_name}/", "stac/")

    items_dates: dict[str, datetime] = {}
    collection_commit_dates = []
    # Add publishing date
    collection_commit_dates.append(initial_date)
    commits = list(repo.iter_commits("master", paths=collection_path_in_repo))

    if len(commits) == 0:
        get_log().debug(f"There is no commit for collection {collection_published_path}")
        sys.exit(1)

    collection_published = json.loads(read(collection_published_path))
    collection_id = collection_published["id"]

    import_dates = []
    for commit in reversed(commits):  # start from oldest commit
        get_log().debug(
            f"Fetching commit: {commit.hexsha} - {str(commit.message)} by "
            f"{commit.author.name} at {format_rfc_3339_datetime_string(commit.committed_datetime)}"
        )

        try:
            collection_content = (commit.tree / collection_path_in_repo).data_stream.read().decode("utf-8")
        except KeyError:
            get_log().debug(f"File {collection_path_in_repo} not found in commit {commit.hexsha}")
            continue

        collection = json.loads(collection_content)
        if collection["id"] != collection_id:
            continue

        if str(commit.message).startswith("feat: import"):
            import_dates.append(format_rfc_3339_datetime_string(commit.committed_datetime))

        if commit.committed_datetime >= initial_date:
            collection_commit_dates.append(commit.committed_datetime)

        for item_link in collection["links"]:
            if item_link["rel"] != "item":
                continue

            if item_link["href"] not in items_dates:
                item_created = max(commit.committed_datetime, initial_date)
                items_dates[item_link["href"]] = item_created

    dataset_path = collection_published_path.rstrip("collection.json")
    output_path = f"{arguments.output}{collection_path_in_repo.replace("stac/", "").rstrip("collection.json")}"

    # Update Items
    updated_links = run_update_item_dates(
        collection_published["links"],
        dataset_path,
        output_path,
        items_dates,
        collection_commit_dates,
    )

    # Update Collection
    collection_published["links"] = updated_links
    collection_created = max(commits[-1].committed_datetime, initial_date)
    collection_published["created"] = format_rfc_3339_datetime_string(collection_created)
    collection_published["updated"] = format_rfc_3339_datetime_string(max(collection_commit_dates))
    write(f"{output_path}collection.json", dict_to_json_bytes(collection_published), content_type=ContentType.JSON.value)

    get_log().info(
        "STAC updated",
        dataset=collection_published_path,
        published_dates=import_dates,
        duration=time_in_ms() - start_time,
    )


if __name__ == "__main__":
    main()
