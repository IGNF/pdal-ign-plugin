# Makefile to manage main tasks
# cf. https://blog.ianpreston.ca/conda/python/bash/2020/05/13/conda_envs.html#makefile

# Oneshell means I can run multiple lines in a recipe in the same shell, so I don't have to
# chain commands together with semicolon
.ONESHELL:
SHELL = /bin/bash


##############################
# Install
##############################
install:
	mamba env update -n pdal_ign_plugin -f environment.yml


##############################
# Dev/Contrib tools
##############################

testing:
	python -m pytest ./test -s --log-cli-level DEBUG

install-precommit:
	pre-commit install


##############################
# Build/deploy pip lib
##############################

deploy: check
	twine upload dist/*

check: dist/pdal_ign_plugin*.tar.gz
	twine check dist/*

dist/pdal_ign_plugin*.tar.gz:
	python -m build

build: clean
	python -m build

clean:
	rm -rf tmp
	rm -rf pdal_ign_plugin.egg-info
	rm -rf dist

##############################
# Build/deploy Docker image
##############################

REGISTRY=ghcr.io
NAMESPACE=ignf
IMAGE_NAME=pdal_ign_plugin
VERSION=`python -m pdal_ign_macro.version`
FULL_IMAGE_NAME=${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${VERSION}

docker-build: clean
	docker build --no-cache -t ${IMAGE_NAME}:${VERSION} -f Dockerfile .

docker-build-pdal: clean
	docker build --build-arg GITHUB_REPOSITORY=alavenant/PDAL --build-arg GITHUB_SHA=master_28_05_25 -t ${IMAGE_NAME}:${VERSION} -f Dockerfile.pdal .

docker-test-pdal: clean
	docker run --rm  -v `pwd`/tmp_data:/output -t ${IMAGE_NAME}:${VERSION} python -m pytest --log-cli-level=debug 

docker-test:
	docker run --rm -it ${IMAGE_NAME}:${VERSION} python -m pytest -s

docker-remove:
	docker rmi -f `docker images | grep ${IMAGE_NAME}:${VERSION} | tr -s ' ' | cut -d ' ' -f 3`

docker-deploy:
	docker tag ${IMAGE_NAME}:${VERSION} ${FULL_IMAGE_NAME}
	docker push ${FULL_IMAGE_NAME}
