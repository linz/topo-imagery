import argparse
import os

import boto3
from linz_logger import get_log

import aws_helper as aws_helper

logger = get_log()

parser = argparse.ArgumentParser()
parser.add_argument('--survey', dest='survey', required=True)
parser.add_argument('--destination', dest='destination', required=True)
arguments = parser.parse_args()
survey_path = arguments.survey
dest_bucket = arguments.destination

# From the survey s3 path, iterate through the 'subdirectories' (or prefix)
# Get bucket name
bucket_name = aws_helper.bucket_name_from_path(survey_path)
credentials = aws_helper.get_credentials(bucket_name)
s3 = boto3.client(
                "s3",
                aws_access_key_id=credentials.access_key,
                aws_secret_access_key=credentials.secret_key,
                aws_session_token=credentials.token,
            )
paginator = s3.get_paginator("list_objects_v2")
response_iterator = paginator.paginate(Bucket=bucket_name)
for response in response_iterator:
    print(response['Contents'])

# for each survey dissolve the extent polygons as dissolved_clip_extent.shp
for subdir, extent_polys in subdir_extent_polys:
    # A123.gpkg
    # A123.shp
    # A124.gpkg
    # A124.shp
    # A254.gpkg
    # A254.shp

    # OR
    # survey1/A123/file.gpkg
    # survey1/A123/file.shp
    # survey1/A124/file.gpkg
    # survey1/A124/file.shp
    # survey1/A254/file.gpkg
    # survey1/A254/file.shp

    survey_name = os.path.split(subdir)[-1]
    extent_dir = os.path.join(subdir, "dissolved_clip_extent")
    extent_1_file = os.path.join(extent_dir, f"{survey_name}_extent_1.gpkg")
    extent_file = os.path.join(extent_dir, f"{survey_name}_extent.shp")
    temp_file = os.path.join(subdir, "temp", "temp_dissolved_extent.shp")
    temp_filename = "temp_dissolved_extent"
    if not extent_polys:
        self.log(f"no extent in {subdir}")
        # TODO probably handle as a survey should contain extent polys
        raise Exception("No extent polys found - create_dissolved_poly function.")
    else:
        for i in range(0, len(extent_polys)):
            if os.path.isfile(temp_file):
                ogr2ogr_gdal_command = f'ogr2ogr -f "ESRI Shapefile" -update -append "{temp_file}" "{extent_polys[i]}"'
                os.system(ogr2ogr_gdal_command)
            else:
                ogr2ogr_gdal_command = f'ogr2ogr -f "ESRI Shapefile" "{temp_file}" "{extent_polys[i]}"'
                os.system(ogr2ogr_gdal_command)
        first_tif = self.subdirs_list[0][1][0]
        raster_origin_x, raster_origin_y, raster_pixel_width, raster_pixel_height = self.get_raster_pixel_size(first_tif)
        decimal_places = self.decimal_places_as_float(raster_pixel_width)
        ogr2ogr_gdal_command = (
            f"ogr2ogr "
            f'-f "GPKG" "{extent_1_file}" "{temp_file}" '
            f"-dialect sqlite "
            f'-sql "SELECT ST_Union(ST_SnapToGrid('
            f"ST_SnapToGrid(geometry,{decimal_places}),"
            f"{raster_origin_x},"
            f"{raster_origin_y},"
            f"{raster_pixel_width},"
            f"{raster_pixel_height})) AS geometry FROM '{temp_filename}'\""
        )
        os.system(ogr2ogr_gdal_command)
        self.log(f"Location of extent produced before explode collections is run: {extent_1_file}")
        explode_command = f'ogr2ogr -f "ESRI Shapefile" "{extent_file}" "{extent_1_file}" -explodecollections'
        os.system(explode_command)
