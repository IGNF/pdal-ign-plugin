#!/bin/bash
# Bash script to run a local python script in the pdal_ign_plugin docker image

while [[ $# -gt 0 ]]; do
  case $1 in
    -i|--input_file)
      input_dir=$(realpath $(dirname "$2"))
      input_filename=$(basename "$2")
      shift # past argument
      shift # past value
      ;;
    -o|--output_dir)
      output_dir=$(realpath "$2")
      shift # past argument
      shift # past value
      ;;
    -s|--script)
      script_dir=$(realpath $(dirname "$2"))
      script_filename=$(basename "$2")
      shift # past argument
      shift # past value
      ;;
    *)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

echo "Run script:"
echo "* dir=${script_dir}"
echo "* name=${script_filename}"
echo "on file:"
echo "* dir=${input_dir}"
echo "* name=${input_filename}"
echo "save output to:"
echo "* dir=${output_dir}"
echo "* name=${input_filename}"
echo "--------"


docker run --rm --userns=host \
-v ${input_dir}:/input \
-v ${output_dir}:/output \
-v ${script_dir}:/script \
ghcr.io/ignf/pdal-ign-plugin:latest \
python /script/${script_filename} \
    -i /input/${input_filename} \
    -o /output/${input_filename}