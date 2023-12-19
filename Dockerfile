FROM mambaorg/micromamba:latest as build_ign_pdal_plugin
COPY environment.yml /environment.yml

USER root
RUN micromamba env create -f /environment.yml
SHELL ["micromamba", "run", "-n", "pdal_ign_plugin", "/bin/bash", "-c"]

COPY . .

RUN apt-get update && apt-get install --no-install-recommends -y cmake make build-essential g++ && rm -rf /var/lib/apt/lists/*

RUN cmake -G"Unix Makefiles" -DCONDA_PREFIX=$CONDA_PREFIX -DCMAKE_BUILD_TYPE=Release  
RUN make -j4 install

ENV PATH=$PATH:/opt/conda/envs/pdal_ign_plugin/bin/
ENV PROJ_LIB=/opt/conda/envs/pdal_ign_plugin/share/proj/
ENV PDAL_DRIVER_PATH=/tmp/install/lib
