HASH := $(shell git rev-parse HEAD)
POETRY_IMAGE_NAME ?= poetry
IMAGE_NAME ?= mctl
DOCKER_RUN ?= docker run --rm -it -v $(PWD):/app/ -w /app --env-file ./.env --entrypoint /bin/bash ${IMAGE_NAME}:latest
DOCKER_RUN_CI ?= docker run --rm -v $(PWD):/app/ -w /app --env-file ./.env ${IMAGE_NAME}:latest
DOCKER_BUILD ?= docker build
DOCKER_POETRY_BUILD ?= docker run --rm -v $(PWD):/app/ -w /app ${POETRY_IMAGE_NAME}
DOCKER_PUSH_IMAGE ?= docker push
APP_VERSION := $(shell grep -Po '(?<=version = ")[^"]*' "pyproject.toml" | sed 's/\./ /g' | awk '{print $$1"."$$2"."$$3}')
export APP_VERSION

.DEFAULT_GOAL := help

.PHONY: help
help: ## List of targets with descriptions
	@echo "\n--------------------- Run [TARGET] [ARGS] or "make help" for more information ---------------------\n"
	@for MAKEFILENAME in $(MAKEFILE_LIST); do \
		grep -E '[a-zA-Z_-]+:.*?## .*$$' $$MAKEFILENAME | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'; \
	done
	@echo "\n---------------------------------------------------------------------------------------------------\n"

.PHONY: build_all
build_all: build build_image ## Docker build poetry image and cli image

.PHONY: _build_all
_build_all: clean _build _build_image ## local build cli

.PHONY: _build_poetry
_build_poetry: ## build the poetry container
	$(DOCKER_BUILD) -f ./tools/poetry.Dockerfile -t ${POETRY_IMAGE_NAME}:latest .

.PHONY: build
build: ## Docker build cli wheel file
	$(DOCKER_POETRY_BUILD) make _build

.PHONY: _build
_build: ## local build cli wheel file
	poetry build -f wheel

.PHONY: _bump_major_version
_bump_major_version: ## local build cli wheel file
	poetry version major

.PHONY: _bump_minor_version
_bump_minor_version: ## local build cli wheel file
	poetry version minor

.PHONY: _bump_patch_version
_bump_patch_version: ## local build cli wheel file
	poetry version patch

.PHONY: build_image
build_image: ## Docker build cli image
	$(MAKE) _build_image

.PHONY: _build_image
_build_image: ## build cli image
	$(DOCKER_BUILD) -f ./Dockerfile -t ${IMAGE_NAME}:${HASH} -t ${IMAGE_NAME}:latest -t ${IMAGE_NAME}:${APP_VERSION} .

.PHONY: _dev_install
_dev_install: ## Installs the cli locally
	pip install -e ${PWD}

.PHONY: _dev_uninstall
_dev_uninstall: ## uninstalls the cli
	pip uninstall -y mctl

.PHONY: run dotenv
run: ## Run a docker container with the cli available
	$(DOCKER_RUN)

.PHONY: run_ci
run_ci: ## Run a docker container with the cli available
	$(DOCKER_RUN_CI)

.PHONY: push_image
push_image: ## Push the image
	$(DOCKER_PUSH_IMAGE) ${IMAGE_NAME}:${HASH}
	$(DOCKER_PUSH_IMAGE) ${IMAGE_NAME}:latest

.PHONY: dotenv
dotenv: ## create the .env file
	@touch .env

.PHONY: clean
clean: ## create the .env file
	@rm -rf ./dist
