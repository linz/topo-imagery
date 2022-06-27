import argparse
import json
import os
import tempfile
from typing import List

from aws_helper import get_bucket, parse_path


def list_objects(path: str, limit: int = None) -> List[str]:
    bucket_name, files_path = parse_path(path)
    bucket = get_bucket(bucket_name)
    if files_path:
        return bucket.objects.filter(
            Prefix=files_path,
        ).limit(limit)
    else:
        return bucket.objects.all().limit(limit)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", dest="uri", required=True)
    parser.add_argument("--output", dest="output", required=True)
    arguments = parser.parse_args()
    uri = arguments.uri
    output = arguments.output

    output_bucket_name, output_file_name = parse_path(output)

    objects = list_objects(uri)

    # output_bucket = get_bucket(output_bucket_name)
    # output_bucket.upload_file(os.path.join(tmp_dir, "output.json"), output_file_name)


if __name__ == "__main__":
    main()
