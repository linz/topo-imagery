from scripts.stac.imagery.collection import ImageryCollection


def test_imagery_stac_collection_initialise() -> None:
    title = "Test Urban Imagery"
    description = "Test Urban Imagery Description"
    collection = ImageryCollection(title, description)

    assert collection.stac["title"] == title
    assert collection.stac["description"] == description


def test_imagery_stac_collection_update() -> None:
    title = "Test Urban Imagery"
    description = "Test Urban Imagery Description"
    bbox = [1799667.5, 5815977.0, 1800422.5, 5814986.0]
    start_datetime = "2021-01-27T00:00:00Z"
    end_datetime = "2021-01-27T00:00:00Z"
    collection = ImageryCollection(title, description)
    collection.update_spatial_extent(bbox)
    collection.update_temporal_extent(start_datetime, end_datetime)
    assert collection.stac["extent"]["temporal"]["interval"] == [start_datetime, end_datetime]


def test_imagery_stac_collction_update_twice() -> None:
    title = "Test Urban Imagery"
    description = "Test Urban Imagery Description"
    collection = ImageryCollection(title, description)

    bbox_one = [174.889641, -41.217532, 174.902344, -41.203521]
    start_datetime_one = "2021-01-27T00:00:00Z"
    end_datetime_one = "2021-01-27T00:00:00Z"
    collection.update_spatial_extent(bbox_one)
    collection.update_temporal_extent(start_datetime_one, end_datetime_one)

    bbox_two = [174.917643, -41.211157, 174.922965, -41.205490]
    start_datetime_two = "2021-02-01T00:00:00Z"
    end_datetime_two = "2021-02-20T00:00:00Z"
    collection.update_spatial_extent(bbox_two)
    collection.update_temporal_extent(start_datetime_two, end_datetime_two)

    assert collection.stac["extent"]["temporal"]["interval"] == [start_datetime_one, end_datetime_two]
    assert collection.stac["extent"]["spatial"]["bbox"] == [174.889641, -41.217532, 174.922965, -41.203521]