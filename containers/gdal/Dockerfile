FROM osgeo/gdal:ubuntu-small-latest

RUN apt-get update
RUN apt-get install python3-pip -y
RUN pip install boto3 -t /app/
RUN pip install botocore -t /app/
RUN pip install linz-logger -t /app/

WORKDIR /app

ADD ./create_polygons.py /app/create_polygons.py
ADD ./aws_helper.py /app/aws_helper.py
