FROM ubuntu:latest

# Update package registries
RUN apt-get update && apt-get upgrade -y

# Use bash shell
SHELL ["/bin/bash", "-c"]

WORKDIR /app

# Install gdal
RUN apt-get install -y libgdal-dev gdal-bin

# Install tippecanoe
RUN apt-get install git make build-essential libsqlite3-dev zlib1g-dev -y
RUN git clone https://github.com/mapbox/tippecanoe.git
WORKDIR tippecanoe
RUN make -j
RUN make install

# Install pmtiles
WORKDIR /app/pmtiles
RUN apt-get install wget
RUN wget https://github.com/protomaps/go-pmtiles/releases/download/v1.28.0/go-pmtiles_1.28.0_Linux_x86_64.tar.gz
RUN tar -xvzf go-pmtiles_1.28.0_Linux_x86_64.tar.gz
RUN mv pmtiles /bin/pmtiles

# Copy conversion script
WORKDIR /app
COPY vector/gdb_to_pmtiles.sh .
COPY vector/all_layers_gdb_to_pmtiles.sh .
RUN chmod +x gdb_to_pmtiles.sh
RUN chmod +x all_layers_gdb_to_pmtiles.sh

# Keep the container runnning
CMD ["tail", "-f", "/dev/null"]
