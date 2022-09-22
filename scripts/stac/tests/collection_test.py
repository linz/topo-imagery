from scripts.stac.imagery.collection import ImageryCollection


def test_imagery_stac_collection_initialise() -> None:
    title = "Test Urban Imagery"
    description = "Test Urban Imagery Description"
    collection = ImageryCollection(title, description)

    assert collection.stac["title"] == title
    assert collection.stac["description"] == description
