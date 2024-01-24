from shapely.geometry import Polygon

from scripts.stac.imagery.capture_aera import merge_polygons


def test_merge_polygons() -> None:
    polygons = []
    polygons.append(Polygon([(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0), (0.0, 1.0)]))
    polygons.append(Polygon([(1.0, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0), (1.0, 1.0)]))
    expected_merged_polygon = Polygon([(0.0, 1.0), (2.0, 1.0), (2.0, 0.0), (0.0, 0.0), (0.0, 1.0)])

    merged_polygons = merge_polygons(polygons, 0)

    # Using `Polygon.equals()` as merge_polygons might return a different set of coordinates for the same geometry
    # In this example: `Polygon([(2.0, 1.0), (2.0, 0.0), (0.0, 0.0), (0.0, 1.0), (2.0, 1.0)])`
    assert merged_polygons.equals(expected_merged_polygon)


def test_merge_polygons_with_rounding() -> None:
    polygons = []
    polygons.append(Polygon([(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0), (0.0, 1.0)]))
    # The following polygon is off by 0.1 to the "right" from the previous one
    polygons.append(Polygon([(1.1, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0), (1.1, 1.0)]))
    expected_merged_polygon = Polygon([(0.0, 1.0), (2.0, 1.0), (2.0, 0.0), (0.0, 0.0), (0.0, 1.0)])

    # By giving a buffer distance of 0.1, we want to correct this margin of error and have the two polygons being merged
    merged_polygons = merge_polygons(polygons, 0.1)

    assert merged_polygons.equals(expected_merged_polygon)


def test_merge_polygons_with_rounding_margin_too_big() -> None:
    polygons = []
    polygons.append(Polygon([(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0), (0.0, 1.0)]))
    # The following polygon is off by 0.1 to the "right" from the previous one
    polygons.append(Polygon([(1.1, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0), (1.1, 1.0)]))
    expected_merged_polygon = Polygon([(0.0, 1.0), (2.0, 1.0), (2.0, 0.0), (0.0, 0.0), (0.0, 1.0)])

    # Here, the allowed margin of error is 0.01 < 0.1
    merged_polygons = merge_polygons(polygons, 0.01)

    assert not merged_polygons.equals(expected_merged_polygon)
