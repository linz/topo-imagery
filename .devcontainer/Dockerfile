FROM osgeo/gdal:ubuntu-small-3.6.1

RUN apt update && apt install -y python3-pip python3-distutils git
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PYTHONPATH="/lib/python3/dist-packages:/workspaces/topo-imagery:$PYTHONPATH"
ENV PATH=/root/.local/bin:$PATH