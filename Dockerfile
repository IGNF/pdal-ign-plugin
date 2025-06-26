FROM mambaorg/micromamba:bullseye-slim AS build

COPY environment_docker.yml /environment_docker.yml

USER root
RUN micromamba env create -f /environment_docker.yml
SHELL ["micromamba", "run", "-n", "pdal_ign_plugin", "/bin/bash", "-c"]
RUN apt-get update && apt-get install --no-install-recommends -y cmake make build-essential g++ && rm -rf /var/lib/apt/lists/*

COPY src src
COPY CMakeLists.txt CMakeLists.txt
RUN cmake -G"Unix Makefiles" -DCONDA_PREFIX=$CONDA_PREFIX -DCMAKE_BUILD_TYPE=Release
RUN make -j4 install

FROM debian:bullseye-slim

COPY --from=build /opt/conda/envs/pdal_ign_plugin /opt/conda/envs/pdal_ign_plugin
RUN mkdir -p /pdal_ign_plugin
COPY --from=build /tmp/install/lib /pdal_ign_plugin/install/lib

ENV PATH=$PATH:/opt/conda/envs/pdal_ign_plugin/bin/
ENV PROJ_LIB=/opt/conda/envs/pdal_ign_plugin/share/proj/
ENV PDAL_DRIVER_PATH=/pdal_ign_plugin/install/lib

# Install python macro module
COPY pdal_ign_macro /pdal_ign_plugin/pdal_ign_macro
COPY pyproject.toml /pdal_ign_plugin/pyproject.toml
WORKDIR /pdal_ign_plugin
RUN pip install .

# Add example scripts + test data (to be able to test inside the docker image)
COPY test /pdal_ign_plugin/test
