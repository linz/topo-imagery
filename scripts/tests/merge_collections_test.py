from scripts.merge_collections import merge_links
from scripts.stac.imagery.collection import ImageryCollection


def test_merge_links() -> None:
    collection_one = ImageryCollection("Test Urban Imagery", "Test Urban Imagery Description", "ulid")
    collection_one.add_link(rel="item", href="./BR34_5000_0304.json", file_type="application/json")
    collection_two = ImageryCollection("Test Urban Imagery", "Test Urban Imagery Description", "ulid")
    collection_two.add_link(rel="item", href="./BR34_5000_0305.json", file_type="application/json")

    collection = merge_links(collection_one, collection_two.stac)

    assert {"rel": "self", "href": "./collection.json", "type": "application/json"} in collection.stac["links"]
    assert {"rel": "item", "href": "./BR34_5000_0304.json", "type": "application/json"} in collection.stac["links"]
    assert {"rel": "item", "href": "./BR34_5000_0305.json", "type": "application/json"} in collection.stac["links"]
    assert collection.stac["links"].count({"rel": "self", "href": "./collection.json", "type": "application/json"}) == 1
