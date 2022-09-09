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
