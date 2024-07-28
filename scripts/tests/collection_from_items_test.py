from boto3 import client, resource
from moto import mock_aws
from moto.s3.responses import DEFAULT_REGION_NAME

from scripts.collection_from_items import main
from scripts.datetimes import utc_now
from scripts.files.fs_s3 import write
from scripts.json_codec import dict_to_json_bytes
from scripts.stac.imagery.item import ImageryItem


@mock_aws
def test_should_create_collection_file() -> None:
    # Mock AWS S3
    s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
    boto3_client = client("s3", region_name=DEFAULT_REGION_NAME)
    s3.create_bucket(Bucket="stacfiles")
    # Create mocked STAC Item
    item = ImageryItem("123", "./scripts/tests/data/empty.tiff", utc_now)
    geometry = {
        "type": "Polygon",
        "coordinates": [[1799667.5, 5815977.0], [1800422.5, 5815977.0], [1800422.5, 5814986.0], [1799667.5, 5814986.0]],
    }
    bbox = (1799667.5, 5815977.0, 1800422.5, 5814986.0)
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-27T00:00:00Z"
    item.update_spatial(geometry, bbox)
    item.update_datetime(start_datetime, end_datetime)
    item.add_collection("abc")
    write("s3://stacfiles/item.json", dict_to_json_bytes(item.stac))
    # CLI arguments
    args = [
        "--uri",
        "s3://stacfiles/",
        "--collection-id",
        "abc",
        "--category",
        "urban-aerial-photos",
        "--region",
        "hawkes-bay",
        "--gsd",
        "1m",
        "--start-date",
        "2023-09-20",
        "--end-date",
        "2023-09-20",
        "--lifecycle",
        "ongoing",
        "--producer",
        "Placeholder",
        "--licensor",
        "Placeholder",
        "--concurrency",
        "25",
    ]
    # Call script's main function
    main(args)
    # Verify collection.json has been created
    resp = boto3_client.get_object(Bucket="stacfiles", Key="collection.json")
    assert '"type": "Collection"' in resp["Body"].read().decode("utf-8")
