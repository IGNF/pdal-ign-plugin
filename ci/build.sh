#!/bin/bash

set -e

FILE=${HOME}/anaconda3/etc/profile.d/conda.sh
if [ -e ${HOME}/anaconda3/etc/profile.d/conda.sh ]
then
    source ${HOME}/anaconda3/etc/profile.d/conda.sh
elif [ -e ~/miniconda3/etc/profile.d/conda.sh ]
then
    source ${HOME}/miniconda3/etc/profile.d/conda.sh
elif [ -e /usr/share/miniconda/etc/profile.d/conda.sh ]
then
    source /usr/share/miniconda/etc/profile.d/conda.sh
elif [ -e ${HOME}/miniforge3/etc/profile.d/conda.sh ]
then
     source ${HOME}/miniforge3/etc/profile.d/conda.sh
elif [[ -z "${CONDASH}" ]]; then
    echo ERROR: Failed to load conda.sh : ~/anaconda3/etc/profile.d/conda.sh or ~/miniforge3/etc/profile.d/conda.sh or env CONDASH
    exit 1 # terminate and indicate error
else
    echo DEBUG "$FILE does not exist, using env CONDASH."
    source $CONDASH
fi

conda activate pdal_ign_plugin

export CONDA_PREFIX=$CONDA_PREFIX
echo conda is $CONDA_PREFIX

mkdir -p build
cd build
cmake -G"Unix Makefiles" -DCONDA_PREFIX=$CONDA_PREFIX -DCMAKE_BUILD_TYPE=Release ../
make install

conda deactivate

cd ..
rm -rf build