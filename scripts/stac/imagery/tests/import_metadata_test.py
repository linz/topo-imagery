from scripts.stac.imagery.import_metadata import get_cloud_percent


def test_get_cloud_coverage() -> None:
    metadata_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><MetaData TimeZone="+0800">
    <ProductInfo><CloudPercent>0</CloudPercent></ProductInfo></MetaData>"""
    cloud_percent = get_cloud_percent(metadata_xml)
    assert cloud_percent == 0


def test_get_cloud_coverage_missing_cloud_percent() -> None:
    metadata_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><MetaData TimeZone="+0800">
    <ProductInfo>ff</ProductInfo></MetaData>"""
    cloud_percent = get_cloud_percent(metadata_xml)
    assert cloud_percent is None
