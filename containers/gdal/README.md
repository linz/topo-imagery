# GDAL Container

The purpose of this Docker container is to run Python scripts which use the [GDAL library](https://gdal.org/). It is based on [`osgeo/gdal:ubuntu-small-latest` Docker image](https://hub.docker.com/r/osgeo/gdal/).

## Python scripts

Python version is set to `3.8.10` as it is the current version used by `osgeo/gdal`.

### `create_polygons.py`

#### Usage

##### Local

1. Build the Docker image:
   `docker build .`
2. Log into AWS with `AWS-CLI` on your account
3. Run the following command

```bash
docker run -v ${HOME}/.aws/credentials:/root/.aws/credentials:ro -e AWS_PROFILE='your-aws-profile' 'image-id'  python create_polygons.py --uri 's3://path-to-the-tiff/image.tif' --destination 'destination-bucket'
```
