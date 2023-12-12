#!/bin/sh

FILE=~/anaconda3/etc/profile.d/conda.sh
if [ -e ~/anaconda3/etc/profile.d/conda.sh ] 
then
    source ~/anaconda3/etc/profile.d/conda.sh
elif [ -e ~/miniconda3/etc/profile.d/conda.sh ]
then
    source ~/miniconda3/etc/profile.d/conda.sh
elif [ -e ~/miniforge3/etc/profile.d/conda.sh ] 
then    
     source ~/miniforge3/etc/profile.d/conda.sh
elif [[ -z "${CONDASH}" ]]; then
    echo ERROR: Failed to load conda.sh : ~/anaconda3/etc/profile.d/conda.sh or ~/miniforge3/etc/profile.d/conda.sh or env CONDASH
    exit 1 # terminate and indicate error
else
    echo DEBUG "$FILE does not exist, using env CONDASH."
    source $CONDASH
fi

conda activate pdal_ign_plugin

export CONDA_PREFIX=$CONDA_PREFIX

mkdir build
cd build
cmake -G"Unix Makefiles" -DCONDA_PREFIX=$CONDA_PREFIX -DCMAKE_BUILD_TYPE=Release ../ 
make $1 install

conda deactivate

cd ..
rm -rf build 