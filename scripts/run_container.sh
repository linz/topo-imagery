docker run -v ${HOME}/tmp/:/tmp/:rw -v ${HOME}/.aws/:/home/root/.aws/: topo-imagery python standardise_validate.py --preset webp --source /tmp/file_to_standardise.tiff --collection-id 123 --start-datetime 2023-01-01 --end-datetime 2023-01-01 --target /tmp/output/ --source-epsg 2193 --target-epsg 2193

docker build -t topo-imagery && \
