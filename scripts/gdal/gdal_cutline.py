
from typing import Optional
from osgeo import gdal
from osgeo import ogr


def optimize_cutline(tiff_path: str, cutline_path: str, optimize = False) -> Optional[str] :
    """Determine if a cutline needs to be applied to a tiff

    Args:
        tiff_path: the tiff to check the cutline against
        cutline_path: cutline to use
        optimize: Reduce the scope of the cutline to bounds of the imagery

    Returns:
        Location to a new optimised cutline or None if no cutline is required
    """

    gdal_tiff = gdal.Open(tiff_path, gdal.GA_ReadOnly)
    gdal_cutline = ogr.Open(cutline_path, gdal.GA_ReadOnly)

    # Convert tiff into polygon
    transform = gdal_tiff.GetGeoTransform()
    pixel_width = transform[1]
    pixel_height = transform[5]
    cols = gdal_tiff.RasterXSize
    rows = gdal_tiff.RasterYSize

    xLeft = transform[0]
    yTop = transform[3]
    xRight = xLeft+cols*pixel_width
    yBottom = yTop+rows*pixel_height

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(xLeft, yTop)
    ring.AddPoint(xLeft, yBottom)
    ring.AddPoint(xRight, yBottom)
    ring.AddPoint(xRight, yTop)
    ring.AddPoint(xLeft, yTop)
    tiff_geom = ogr.Geometry(ogr.wkbPolygon)
    tiff_geom.AddGeometry(ring)

    # Compare cutline against raster
    input_layer = gdal_cutline.GetLayer()
    input_feature = input_layer.GetFeature(0)
    cutline_geom = input_feature.GetGeometryRef()

    # Check the amount of intersection between the cutline and the tiff
    cutline_intersection = tiff_geom.Intersection(cutline_geom)
    intersection_area = cutline_intersection.GetArea()
    raster_area = tiff_geom.GetArea();

    intersection_area = intersection_area / raster_area 

    # 99.99% of the tiff is covered by the cutline, so we likely dont need the cutline
    if intersection_area >= 0.9999:
        return None

    # Not asked to optimize the cutline
    if not optimize:
        return cutline_path

    output_path = cutline_path + ".optimized.geojson"
    
    # Optimize the cutline to the intersection area
    driver = ogr.GetDriverByName("geojson")
    optimized_cutline = driver.CreateDataSource(output_path)
    output_layer = optimized_cutline.CreateLayer('optimized-cutline', input_layer.GetSpatialRef(), input_layer.GetGeomType())

    # Buffer the TIFF by 1M
    tiff_geom_buffer = tiff_geom.Buffer(1.0)
    cutline_buffer_intersection = tiff_geom_buffer.Intersection(tiff_geom)

    # Copying the features
    output_cutline = ogr.Feature(input_layer.GetLayerDefn())
    output_cutline.SetGeometry(cutline_buffer_intersection)
    output_layer.CreateFeature(output_cutline)

    return output_path
