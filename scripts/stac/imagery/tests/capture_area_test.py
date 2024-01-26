from shapely.geometry import Polygon

from scripts.stac.imagery.capture_aera import generate_capture_area, merge_polygons, to_feature

# In the following tests, the expected and result GeoJSON documents are printed if the test fails.
# This allows to visualize the geometry for debugging purpose.


def test_merge_polygons() -> None:
    polygons = []
    polygons.append(Polygon([(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0), (0.0, 1.0)]))
    polygons.append(Polygon([(1.0, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0), (1.0, 1.0)]))
    expected_merged_polygon = Polygon([(0.0, 1.0), (2.0, 1.0), (2.0, 0.0), (0.0, 0.0), (0.0, 1.0)])
    print(f"GeoJSON expected: {to_feature(expected_merged_polygon)}")

    merged_polygons = merge_polygons(polygons, 0)
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
    print(f"GeoJSON expected: {to_feature(expected_merged_polygon)}")

    # By giving a buffer distance of 0.1, we want to correct this margin of error and have the two polygons being merged
    merged_polygons = merge_polygons(polygons, 0.1)
    print(f"GeoJSON result: {to_feature(merged_polygons)}")

    assert merged_polygons.equals(expected_merged_polygon)


def test_merge_polygons_with_rounding_margin_too_big() -> None:
    polygons = []
    polygons.append(Polygon([(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0), (0.0, 1.0)]))
    # The following polygon is off by 0.1 to the "right" from the previous one
    polygons.append(Polygon([(1.1, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0), (1.1, 1.0)]))
    expected_merged_polygon = Polygon([(0.0, 1.0), (2.0, 1.0), (2.0, 0.0), (0.0, 0.0), (0.0, 1.0)])
    print(f"GeoJSON expected: {to_feature(expected_merged_polygon)}")

    # Here, the allowed margin of error is 0.01 < 0.1
    merged_polygons = merge_polygons(polygons, 0.01)
    print(f"GeoJSON result: {to_feature(merged_polygons)}")

    assert not merged_polygons.equals(expected_merged_polygon)


def test_generate_capture_area_rounded() -> None:
    polygons = []
    polygons.append(
        Polygon(
            [
                (178.254184985672936, -38.40856551170436),
                (178.254654234749751, -38.41502700730107),
                (178.260129304159022, -38.41478071250544),
                (178.259657, -38.408319273592511),
                (178.254184985672936, -38.40856551170436),
            ]
        )
    )
    polygons.append(
        Polygon(
            [
                (178.259659571653003, -38.408319273592511),
                (178.260129304159022, -38.41478071250544),
                (178.265604306681723, -38.414534163261521),
                (178.265134090769521, -38.408072781090567),
                (178.259659571653003, -38.408319273592511),
            ]
        )
    )
    # There is a gap of ~0.2m between the top right corner of the first polygon and the top left corner of the second one
    # This gap should not be visible but covered in the capture-area
    expected_merged_polygon = Polygon(
        [
            (178.25965700000006, -38.40831927359251),
            (178.26513409076952, -38.40807278109057),
            (178.26560430668172, -38.41453416326152),
            (178.25465423474975, -38.41502700730107),
            (178.25418498567294, -38.40856551170436),
            (178.25965700000006, -38.40831927359251),
        ]
    )
    print(f"GeoJSON expected: {to_feature(expected_merged_polygon)}")

    # Using GSD of 0.2m
    capture_area = generate_capture_area(polygons, 0.2)
    print(f"GeoJSON result: {capture_area}")

    assert capture_area == to_feature(expected_merged_polygon)


def test_generate_capture_area_not_rounded() -> None:
    polygons = []
    polygons.append(
        Polygon(
            [
                (178.254184985672936, -38.40856551170436),
                (178.254654234749751, -38.41502700730107),
                (178.260129304159022, -38.41478071250544),
                (178.259654, -38.408319273592511),
                (178.254184985672936, -38.40856551170436),
            ]
        )
    )
    polygons.append(
        Polygon(
            [
                (178.259659571653003, -38.408319273592511),
                (178.260129304159022, -38.41478071250544),
                (178.265604306681723, -38.414534163261521),
                (178.265134090769521, -38.408072781090567),
                (178.259659571653003, -38.408319273592511),
            ]
        )
    )
    # There is a gap of  > 0.4m between the top right corner of the first polygon and the top left corner of the second one.
    # This gap should remain in the capture area as too big to be a rounding issue that we want to covered up.
    expected_merged_polygon = Polygon(
        [
            (178.259654, -38.40831927359251),
            (178.259787907001, -38.41013964879939),
            (178.25979188779417, -38.410139357688166),
            (178.259659571653, -38.40831927359251),
            (178.26513409076952, -38.40807278109057),
            (178.26560430668172, -38.41453416326152),
            (178.25465423474975, -38.41502700730107),
            (178.25418498567294, -38.40856551170436),
            (178.259654, -38.40831927359251),
        ]
    )
    print(f"GeoJSON expected: {to_feature(expected_merged_polygon)}")

    # Using GSD of 0.2m
    capture_area = generate_capture_area(polygons, 0.2)
    print(f"GeoJSON result: {capture_area}")

    assert capture_area == to_feature(expected_merged_polygon)
