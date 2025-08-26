from decimal import Decimal
from sys import float_info
from typing import cast

from pytest_subtests import SubTests
from shapely import get_exterior_ring, is_ccw
from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.predicates import is_valid

from scripts.stac.imagery.capture_area import generate_capture_area, merge_polygons, to_feature

# In the following tests, the expected and result GeoJSON documents are printed if the test fails.
# This allows to visualize the geometry for debugging purpose.


def test_merge_polygons() -> None:
    polygons = []
    polygons.append(Polygon([(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0), (0.0, 1.0)]))
    polygons.append(Polygon([(1.0, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0), (1.0, 1.0)]))
    expected_merged_polygon = Polygon([(1.0, 1.0), (0.0, 1.0), (0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (1.0, 1.0)])
    merged_polygons = merge_polygons(polygons, 0)

    print(f"Polygon A: {to_feature(polygons[0])}")
    print(f"Polygon B: {to_feature(polygons[1])}")
    print(f"GeoJSON expected: {to_feature(expected_merged_polygon)}")
    print(f"GeoJSON result: {to_feature(merged_polygons)}")

    # Using `Polygon.equals_exact()` as merge_polygons might return a different set of coordinates for the same geometry
    # In this example: `Polygon([(2.0, 1.0), (2.0, 0.0), (0.0, 0.0), (0.0, 1.0), (2.0, 1.0)])`
    assert merged_polygons.equals_exact(expected_merged_polygon, tolerance=0.0)


def test_merge_polygons_with_rounding() -> None:
    polygons = []
    polygons.append(Polygon([(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0), (0.0, 1.0)]))
    # The following polygon is off by 0.1 to the "right" from the previous one
    polygons.append(Polygon([(1.1, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0), (1.1, 1.0)]))
    expected_merged_polygon = Polygon([(2.0, 1.0), (0.0, 1.0), (0.0, 0.0), (2.0, 0.0), (2.0, 1.0)])
    # By giving a buffer distance of 0.1, we want to correct this margin of error and have the two polygons being merged
    merged_polygons = merge_polygons(polygons, 0.1)

    print(f"Polygon A: {to_feature(polygons[0])}")
    print(f"Polygon B: {to_feature(polygons[1])}")
    print(f"GeoJSON expected: {to_feature(expected_merged_polygon)}")
    print(f"GeoJSON result: {to_feature(merged_polygons)}")

    assert merged_polygons.equals_exact(expected_merged_polygon, tolerance=0.0)


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
            (0.0, 1.0),
            (0.0, 0.0),
            (2.0, 0.0),
            (2.0, 1.0),
            (1.1, 1.0),
            (1.01501863, 0.1501863),
            (1.0, 0.15093536),
            (1.0, 1.0),
        ]
    )

    print(f"Polygon A: {to_feature(polygons[0])}")
    print(f"Polygon B: {to_feature(polygons[1])}")
    print(f"GeoJSON expected: {to_feature(expected_merged_polygon)}")
    print(f"GeoJSON result: {to_feature(merged_polygons)}")

    assert merged_polygons.equals_exact(expected_merged_polygon, tolerance=float_info.epsilon)


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
    capture_area_expected = generate_capture_area(polygons_no_gap, Decimal("0.2"))
    # Generate the capture area of the polygons that have a gap between each other
    capture_area_result = generate_capture_area(polygon_with_gap, Decimal("0.2"))
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
    capture_area_expected = generate_capture_area(polygons_no_gap, Decimal("0.2"))
    # Generate the capture area of the polygons that have a gap between each other
    capture_area_result = generate_capture_area(polygon_with_gap, Decimal("0.2"))

    print(f"Polygon no gap A: {to_feature(polygons_no_gap[0])}")
    print(f"Polygon no gap B: {to_feature(polygons_no_gap[1])}")
    print(f"Polygon with gap A: {to_feature(polygon_with_gap[0])}")
    print(f"Polygon with gap B: {to_feature(polygon_with_gap[1])}")
    print(f"Capture area expected: {capture_area_expected}")
    print(f"Capture area result: {capture_area_result}")
    # This gap should not be covered in the capture-area
    # as the GSD is 0.2m * a buffer of 2 * 2 < 0.88m
    assert capture_area_expected != capture_area_result


def test_capture_area_orientation_polygon(subtests: SubTests) -> None:
    # Test the orientation of the capture area
    # The polygon capture area should be the same as the polygon and not reversed
    polygons = []
    polygons.append(
        shape(
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [174.673418475601466, -37.051277768264598],
                            [174.673425023818197, -37.051550327851878],
                            [174.673479832051271, -37.051280958541774],
                            [174.673418475601466, -37.051277768264598],
                        ]
                    ]
                ],
            }
        )
    )
    capture_area = generate_capture_area(polygons, Decimal("0.05"))

    with subtests.test(msg="Is counterclockwise"):
        assert is_ccw(get_exterior_ring(shape(capture_area["geometry"])))

    with subtests.test(msg="Valid geometry"):
        assert is_valid((shape(capture_area["geometry"])))


def test_capture_area_orientation_multipolygon(subtests: SubTests) -> None:
    # Test the orientation of the capture area
    # The multipolygon capture area polygons should be the same as the polygon and not reversed
    polygons = []
    polygons.append(
        shape(
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [175.01786467173446, -36.80914409510033],
                            [175.0154395531313, -36.80918523526587],
                            [175.01524959114974, -36.80950706997984],
                            [175.01312143626905, -36.81369683085496],
                            [175.01801611134528, -36.81491172712502],
                            [175.01786467173446, -36.80914409510033],
                        ]
                    ],
                    [
                        [
                            [174.99635270693256, -36.809507300287486],
                            [174.99160937900407, -36.80958686195598],
                            [174.9916815185804, -36.80966722253352],
                            [174.9909875028488, -36.810093453911804],
                            [174.99113976763834, -36.815970642382126],
                            [174.99336131537976, -36.81582975812777],
                            [174.99645096077896, -36.81328982536313],
                            [174.99635270693256, -36.809507300287486],
                        ]
                    ],
                ],
            }
        )
    )
    capture_area = generate_capture_area(polygons, Decimal("0.05"))
    mp_geom = cast(MultiPolygon, shape(capture_area["geometry"]))

    with subtests.test(msg="Valid geometry"):
        assert is_ccw(get_exterior_ring(mp_geom.geoms[0]))

    with subtests.test(msg="Valid geometry"):
        assert is_valid((shape(capture_area["geometry"])))


def test_capture_area_rounding_decimal_places() -> None:
    # Test that the capture area is rounded to 8 decimal places
    polygons = []
    polygons.append(
        shape(
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [174.673418475601466, -37.051277768264598],
                            [174.673425023818197, -37.051550327851878],
                            [174.673479898051271, -37.051280958541774],
                            [174.673418475601466, -37.051277768264598],
                        ]
                    ]
                ],
            }
        )
    )
    capture_area_expected = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [174.67342502, -37.05155033],
                    [174.6734799, -37.05128096],
                    [174.67341848, -37.05127777],
                    [174.67342502, -37.05155033],
                ]
            ],
        },
        "type": "Feature",
        "properties": {},
    }
    capture_area = generate_capture_area(polygons, Decimal("1"))
    assert capture_area == capture_area_expected


def test_should_make_compliant_capture_area(subtests: SubTests) -> None:
    # Given two touching triangles
    polygons = [
        shape(
            {
                "type": "MultiPolygon",
                "coordinates": [[[[0, 0], [0, 1], [1, 1], [0, 0]]]],
            }
        ),
        shape(
            {
                "type": "MultiPolygon",
                "coordinates": [[[[1, 0], [2, 2], [1, 2], [1, 0]]]],
            }
        ),
    ]

    merged_polygons = merge_polygons(polygons, 0.1)
    # print(type(merged_polygons))
    mp_geom = cast(MultiPolygon, merged_polygons)
    # print(type(mp_geom))

    with subtests.test(msg="Valid geometry"):
        assert is_valid(merged_polygons)

    with subtests.test(msg="Is counterclockwise"):
        assert is_ccw(get_exterior_ring(mp_geom.geoms[0]))
