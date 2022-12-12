from typing import Optional
from osgeo import gdal
from osgeo import ogr, Geometry, Layer


def get_tiff_geom(tiff_path: str) -> Geometry:
    """Load a tiff with gdal and create a geometry for the bounding box"""
    gdal_tiff = gdal.Open(tiff_path, gdal.GA_ReadOnly)

    # Convert tiff into polygon
    transform = gdal_tiff.GetGeoTransform()
    pixel_width = transform[1]
    pixel_height = transform[5]
    cols = gdal_tiff.RasterXSize
    rows = gdal_tiff.RasterYSize

    xLeft = transform[0]
    yTop = transform[3]
    xRight = xLeft + cols * pixel_width
    yBottom = yTop + rows * pixel_height

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(xLeft, yTop)
    ring.AddPoint(xLeft, yBottom)
    ring.AddPoint(xRight, yBottom)
    ring.AddPoint(xRight, yTop)
    ring.AddPoint(xLeft, yTop)
    tiff_geom = ogr.Geometry(ogr.wkbPolygon)
    tiff_geom.AddGeometry(ring)
    return tiff_geom


def clamp_cutline_to_tiff(output_location: str, tiff_geom: Geometry, cutline_geom: Geometry, input_layer: Layer) -> str:
    """Optimize a cutline to a specific tiff_geomemtry

    Args:
        output_location: output location
        tiff_geom: Geometry of the tiff
        cutline_geom: Geometry of the cutline
        input_layer: Cutline input layer

    Returns:
        Location of optimised cutline
    """
    output_path = output_location + ".optimized.geojson"

    # Optimize the cutline to the intersection area
    driver = ogr.GetDriverByName("geojson")
    optimized_cutline = driver.CreateDataSource(output_path)
    output_layer = optimized_cutline.CreateLayer("optimized-cutline", input_layer.GetSpatialRef(), input_layer.GetGeomType())

    # Buffer the TIFF by 1M
    tiff_geom_buffer = tiff_geom.Buffer(1.0)
    cutline_buffer_intersection = tiff_geom_buffer.Intersection(cutline_geom)

    # Copying the features
    output_cutline = ogr.Feature(input_layer.GetLayerDefn())
    output_cutline.SetGeometry(cutline_buffer_intersection)
    output_layer.CreateFeature(output_cutline)

    return output_path


def optimize_cutline(tiff_path: str, cutline_path: str, optimize: bool = False) -> Optional[str]:
    """Determine if a cutline needs to be applied to a tiff

    Args:
        tiff_path: the tiff to check the cutline against
        cutline_path: cutline to use
        optimize: Reduce the scope of the cutline to bounds of the imagery

    Returns:
        Location to a new optimised cutline or None if no cutline is required
    """

    tiff_geom = get_tiff_geom(tiff_path)
    gdal_cutline = ogr.Open(cutline_path, gdal.GA_ReadOnly)

    # Compare cutline against raster
    input_layer = gdal_cutline.GetLayer()
    input_feature = input_layer.GetFeature(0)
    cutline_geom = input_feature.GetGeometryRef()

    # Check the amount of intersection between the cutline and the tiff
    cutline_intersection = tiff_geom.Intersection(cutline_geom)
    intersection_area = cutline_intersection.GetArea()
    raster_area = tiff_geom.GetArea()

    intersection_area = intersection_area / raster_area

    # 99.99% of the tiff is covered by the cutline, so we likely dont need the cutline
    if intersection_area >= 0.9999:
        return None

    # Not asked to optimize the cutline
    if not optimize:
        return cutline_path

    return clamp_cutline_to_tiff(cutline_path, cutline_geom, tiff_geom, input_layer)
