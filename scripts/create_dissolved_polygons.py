import argparse
import os
import tempfile
from distutils.sysconfig import PREFIX

import boto3
from linz_logger import get_log
from osgeo import gdal

import aws_helper as aws_helper

logger = get_log()

parser = argparse.ArgumentParser()
parser.add_argument('--survey', dest='survey', required=True)
parser.add_argument('--destination', dest='destination', required=True)
arguments = parser.parse_args()
survey_path = arguments.survey
dest_bucket = arguments.destination


def get_raster_pixel_size(filepath):
        raster = gdal.Open(filepath)
        geo_transform = raster.GetGeoTransform()
        raster_origin_x = geo_transform[0]
        raster_origin_y = geo_transform[3]
        raster_pixel_width = geo_transform[1]
        raster_pixel_height = geo_transform[5]
        raster = None
        return raster_origin_x, raster_origin_y, raster_pixel_width, raster_pixel_height

def decimal_places_as_float(number):
        return 10 / 10 ** (len(str(float(number)).split(".")[1]) + 1)
# Step 1
# Loop over the '.shz' files in the survey path
# ONLY first element - set the raster_origin_x, raster_origin_y, raster_pixel_width, raster_pixel_height values

# Step 2
# If temp file is  created, use --update and --append in gdal command
# Run the gdal command








# From the survey s3 path, iterate through the 'subdirectories' (or prefix)
# Get bucket name
bucket_name = aws_helper.bucket_name_from_path(survey_path)
prefix = survey_path.replace("s3://", "").replace(f"{bucket_name}/", "")
credentials = aws_helper.get_credentials(bucket_name)
s3 = boto3.client(
                "s3",
                aws_access_key_id=credentials.access_key,
                aws_secret_access_key=credentials.secret_key,
                aws_session_token=credentials.token,
            )
paginator = s3.get_paginator("list_objects_v2")
response_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

with tempfile.TemporaryDirectory() as tmp_dir:
    is_first = True
    for response in response_iterator:
        if "Contents" in response:
            for key in response[ "Contents" ]:
                value = key[ "Key" ]
                print(value)
            # for each survey dissolve the extent polygons as dissolved_clip_extent.shp

                # survey1/A123.shz
                # survey1/A124.shz
                # survey1/A254.shz
                survey_name = os.path.split(subdir)[-1]
                extent_dir = os.path.join(subdir, "dissolved_clip_extent")
                extent_1_file = os.path.join(extent_dir, f"{survey_name}_extent_1.gpkg")
                extent_file = os.path.join(extent_dir, f"{survey_name}_extent.shp")
                temp_file = os.path.join(tmp_dir, "temp_dissolved_extent.shp")
                temp_filename = "temp_dissolved_extent"
                if not extent_polys:
                    get_log().log(f"no extent in {subdir}")
                    # TODO probably handle as a survey should contain extent polys
                    raise Exception("No extent polys found - create_dissolved_poly function.")
                else:
                    ogr2ogr_gdal_command = 'ogr2ogr -f "ESRI Shapefile"'
                    # First element
                    if is_first:
                        ogr2ogr_gdal_command = ogr2ogr_gdal_command + " -update -append"
                        raster_origin_x, raster_origin_y, raster_pixel_width, raster_pixel_height = get_raster_pixel_size("FILE")
                        is_first = False

                    for i in range(0, len(extent_polys)):
                        if os.path.isfile(temp_file):
                            ogr2ogr_gdal_command = f'ogr2ogr -f "ESRI Shapefile" -update -append "{temp_file}" "{extent_polys[i]}"'
                            os.system(ogr2ogr_gdal_command)
                        else:
                            ogr2ogr_gdal_command = f'ogr2ogr -f "ESRI Shapefile" "{temp_file}" "{extent_polys[i]}"'
                            os.system(ogr2ogr_gdal_command)
                    # TODO Why first tif?
                    """ first_tif = self.subdirs_list[0][1][0] """



                    decimal_places = decimal_places_as_float(raster_pixel_width)
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
                    get_log().log(f"Location of extent produced before explode collections is run: {extent_1_file}")
                    explode_command = f'ogr2ogr -f "ESRI Shapefile" "{extent_file}" "{extent_1_file}" -explodecollections'
                    os.system(explode_command)
