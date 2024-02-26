from shapely.geometry import Polygon

from scripts.stac.imagery.capture_area import generate_capture_area, merge_polygons, to_feature

# In the following tests, the expected and result GeoJSON documents are printed if the test fails.
# This allows to visualize the geometry for debugging purpose.


def test_merge_polygons() -> None:
    polygons = []
    polygons.append(Polygon([(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0), (0.0, 1.0)]))
    polygons.append(Polygon([(1.0, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0), (1.0, 1.0)]))
    expected_merged_polygon = Polygon([(0.0, 1.0), (2.0, 1.0), (2.0, 0.0), (0.0, 0.0), (0.0, 1.0)])
    merged_polygons = merge_polygons(polygons, 0)

    print(f"Polygon A: {to_feature(polygons[0])}")
    print(f"Polygon B: {to_feature(polygons[1])}")
    print(f"GeoJSON expected: {to_feature(expected_merged_polygon)}")
    print(f"GeoJSON result: {to_feature(merged_polygons)}")

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

    print(f"Polygon A: {to_feature(polygons[0])}")
    print(f"Polygon B: {to_feature(polygons[1])}")
    print(f"GeoJSON expected: {to_feature(expected_merged_polygon)}")
    print(f"GeoJSON result: {to_feature(merged_polygons)}")

    assert merged_polygons.equals(expected_merged_polygon)


def test_merge_polygons_with_rounding_margin_too_big() -> None:
    polygons = []
    polygons.append(Polygon([(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0), (0.0, 1.0)]))
    # The following polygon is off by 0.1 to the "right" from the previous one
    polygons.append(Polygon([(1.1, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0), (1.1, 1.0)]))
    # We chose a margin of error of 0.01 (< 0.1),
    # so the merged polygon won't be rounded enough to close the gap
    merged_polygons = merge_polygons(polygons, 0.01)
    expected_merged_polygon = Polygon(
        [
            (1.0, 1.0),
            (1.0, 0.15093536161009757),
            (1.015018629811984, 0.1501862981198402),
            (1.1, 1.0),
            (1.9999999999999998, 1.0),
            (1.9999999999999998, 0.0),
            (0.0, 0.0),
            (0.0, 1.0),
            (1.0, 1.0),
        ]
    )

    print(f"Polygon A: {to_feature(polygons[0])}")
    print(f"Polygon B: {to_feature(polygons[1])}")
    print(f"GeoJSON expected: {to_feature(expected_merged_polygon)}")
    print(f"GeoJSON result: {to_feature(merged_polygons)}")

    assert merged_polygons.equals(expected_merged_polygon)


def test_generate_capture_area_rounded() -> None:
    polygons_no_gap = []
    polygons_no_gap.append(Polygon([(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]))
    polygons_no_gap.append(Polygon([(1, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0)]))
    polygon_with_gap = []
    polygon_with_gap.append(Polygon([(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]))
    # The top left corner of the following polygon is off by 0.000001 (~0.11m) to the "right" from the previous one
    polygon_with_gap.append(Polygon([(1.000001, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0)]))

    # Using GSD of 0.2m
    # Generate the capture area of the polygons that don't have a gap between each other
    capture_area_expected = generate_capture_area(polygons_no_gap, 0.2)
    # Generate the capture area of the polygons that have a gap between each other
    capture_area_result = generate_capture_area(polygon_with_gap, 0.2)

    print(f"Polygon no gap A: {to_feature(polygons_no_gap[0])}")
    print(f"Polygon no gap B: {to_feature(polygons_no_gap[1])}")
    print(f"Polygon with gap A: {to_feature(polygon_with_gap[0])}")
    print(f"Polygon with gap B: {to_feature(polygon_with_gap[1])}")
    print(f"Capture area expected: {capture_area_expected}")
    print(f"Capture area result: {capture_area_result}")

    # This gap should not be visible but covered in the capture-area
    # as the GSD is 0.2m * 2 > 0.1m
    assert capture_area_expected == capture_area_result


def test_generate_capture_area_not_rounded() -> None:
    polygons_no_gap = []
    polygons_no_gap.append(Polygon([(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]))
    polygons_no_gap.append(Polygon([(1, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0)]))
    polygon_with_gap = []
    polygon_with_gap.append(Polygon([(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]))
    # The top left corner of the following polygon is off by 0.000008 (~0.88m) to the "right" from the previous one
    polygon_with_gap.append(Polygon([(1.000008, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0)]))

    # Using GSD of 0.2m
    # Generate the capture area of the polygons that don't have a gap between each other
    capture_area_expected = generate_capture_area(polygons_no_gap, 0.2)
    # Generate the capture area of the polygons that have a gap between each other
    capture_area_result = generate_capture_area(polygon_with_gap, 0.2)

    print(f"Polygon no gap A: {to_feature(polygons_no_gap[0])}")
    print(f"Polygon no gap B: {to_feature(polygons_no_gap[1])}")
    print(f"Polygon with gap A: {to_feature(polygon_with_gap[0])}")
    print(f"Polygon with gap B: {to_feature(polygon_with_gap[1])}")
    print(f"Capture area expected: {capture_area_expected}")
    print(f"Capture area result: {capture_area_result}")
    # This gap should not be covered in the capture-area
    # as the GSD is 0.2m * a buffer of 2 * 2 < 0.88m
    assert capture_area_expected != capture_area_result
