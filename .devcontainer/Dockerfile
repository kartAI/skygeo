FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    unzip \
    ca-certificates \
    libgdal-dev \
    gdal-bin \
    libspatialindex-dev 

# Upgrade pip
RUN pip install --upgrade pip

# Install Jupyter, DuckDB, Kepler.gl and related packages
RUN pip install --no-cache-dir \
    jupyter \
    jupyterlab \
    notebook \
    duckdb \
    pandas \
    geopandas \
    keplergl \
    ipywidgets \
    shapely \
    pyarrow \
    matplotlib \
    python-dotenv \
    seaborn

# Install DuckDB CLI
RUN wget https://github.com/duckdb/duckdb/releases/download/v1.4.1/duckdb_cli-linux-amd64.zip && \
    unzip duckdb_cli-linux-amd64.zip && \
    mv duckdb /usr/local/bin/ && \
    rm duckdb_cli-linux-amd64.zip && \
    chmod +x /usr/local/bin/duckdb

# Set working directory
WORKDIR /workspace

# Expose Jupyter port
EXPOSE 8888

# Default command
CMD ["bash"]

