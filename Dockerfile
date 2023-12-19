FROM mambaorg/micromamba:latest as build_ign_pdal_plugin
COPY environment.yml /environment.yml

USER root
RUN micromamba env create -f /environment.yml
SHELL ["micromamba", "run", "-n", "pdal_ign_plugin", "/bin/bash", "-c"]

COPY . .

RUN apt-get update && apt-get install -y cmake make build-essential g++ && rm -rf /var/lib/apt/lists/*

RUN cmake -G"Unix Makefiles" -DCONDA_PREFIX=$CONDA_PREFIX -DCMAKE_BUILD_TYPE=Release  
RUN make -j4 install

FROM debian:bullseye-slim

# install the plugIn
COPY --from=build_ign_pdal_plugin tmp/install/lib/* lib

# install PDAL
COPY --from=build_ign_pdal_plugin /opt/conda/envs/pdal_ign_plugin/bin/pdal /opt/conda/envs/pdal_ign_plugin/bin/pdal
COPY --from=build_ign_pdal_plugin /opt/conda/envs/pdal_ign_plugin/bin/python /opt/conda/envs/pdal_ign_plugin/bin/python
COPY --from=build_ign_pdal_plugin /opt/conda/envs/pdal_ign_plugin/lib/ /opt/conda/envs/pdal_ign_plugin/lib/
COPY --from=build_ign_pdal_plugin /opt/conda/envs/pdal_ign_plugin/ssl /opt/conda/envs/pdal_ign_plugin/ssl
COPY --from=build_ign_pdal_plugin /opt/conda/envs/pdal_ign_plugin/share/proj/proj.db /opt/conda/envs/pdal_ign_plugin/share/proj/proj.db

ENV PATH=$PATH:/opt/conda/envs/pdal_ign_plugin/bin/
ENV PROJ_LIB=/opt/conda/envs/pdal_ign_plugin/share/proj/
ENV PDAL_DRIVER_PATH=/lib/
