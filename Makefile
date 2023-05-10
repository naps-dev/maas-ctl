HASH := $(shell git rev-parse HEAD)
POETRY_IMAGE_NAME ?= ghcr.io/naps-dev/poetry
IMAGE_NAME ?= ghcr.io/naps-dev/maas-ctl
DOCKER_RUN ?= docker run --rm -it -v $(PWD):/app/ -w /app --env-file ./.env --entrypoint /bin/bash ${IMAGE_NAME}:latest
DOCKER_RUN_CI ?= docker run --rm -v $(PWD):/app/ -w /app --env-file ./.env ${IMAGE_NAME}:latest
DOCKER_BUILD ?= docker build
DOCKER_POETRY ?= docker run --rm -v $(PWD):/app/ -w /app ${POETRY_IMAGE_NAME}
DOCKER_PUSH_IMAGE ?= docker push
POETRY_VERSION ?= 1.4.1
export POETRY_VERSION
PYTEST_VERSION ?= 7.2.1
export PYTEST_VERSION
APP_VERSION := $(shell grep -Po '(?<=version = ")[^"]*' "pyproject.toml" | sed 's/\./ /g' | awk '{print $$1"."$$2"."$$3}')
export APP_VERSION

.DEFAULT_GOAL := help

.PHONY: help
help: ## List of targets with descriptions
	@echo "\n--------------------- Run [TARGET] [ARGS] or "make help" for more information ---------------------\n"
	@for MAKEFILENAME in $(MAKEFILE_LIST); do \
		grep -E '[a-zA-Z_-]+:.*?## .*$$' $$MAKEFILENAME  | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'; \
	done
	@echo "\n---------------------------------------------------------------------------------------------------\n"

# pipeline stages
.PHONY: build_all
build_all: clean install build build_image ## Build poetry image and cli image

.PHONY: test_and_lint
test_and_lint: clean install build format lint ## Build poetry image and cli image

# Docker/Compose targets - These targets depend on the environment having docker/docker-compose installed
.PHONY: app_version
app_version: ## Print the app version
	@echo ${APP_VERSION}

.PHONY: poetry_version
poetry_version: ## Print the poetry version
	@echo ${POETRY_VERSION}

.PHONY: poetry_image_name
poetry_image_name: ## Print the poetry version
	@echo ${POETRY_IMAGE_NAME}

.PHONY: pytest_version
pytest_version: ## Print the pytest version
	@echo ${PYTEST_VERSION}

.PHONY: build
build: ## Build cli wheel file
	$(DOCKER_POETRY) make _build

.PHONY: build_poetry
build_poetry: ## Build the poetry container
	$(DOCKER_BUILD) --build-arg POETRY_VERSION=${POETRY_VERSION} --build-arg PYTEST_VERSION=${PYTEST_VERSION} -f ./tools/poetry.Dockerfile -t ${POETRY_IMAGE_NAME}:latest -t ${POETRY_IMAGE_NAME}:v${POETRY_VERSION} .

.PHONY: build_image
build_image: ## Build cli image
	$(MAKE) _build_image

.PHONY: run dotenv
run: ## Run a docker container with bash as the entrypoint
	$(DOCKER_RUN)

.PHONY: run_ci
run_ci: ## Run a docker container with cli as the entrypoint
	$(DOCKER_RUN_CI)

.PHONY: push_image
push_image: ## Push the image
	$(DOCKER_PUSH_IMAGE) ${IMAGE_NAME}:${HASH}
	$(DOCKER_PUSH_IMAGE) ${IMAGE_NAME}:v${APP_VERSION}
	$(DOCKER_PUSH_IMAGE) ${IMAGE_NAME}:latest

.PHONY: dotenv
dotenv: ## Create the .env file
	@touch .env

.PHONY: clean
clean: ## Remove the dist folder
	@rm -rf ./dist

.PHONY: install
install: ## Format code
	$(DOCKER_POETRY) make _install

.PHONY: format
format:  ## Format code
	$(DOCKER_POETRY) make _format

.PHONY: lint
lint:  ## Format code
	$(DOCKER_POETRY) make _lint

# local targets - These targets depend on the environment having all dependencies installed
.PHONY: _build_all
_build_all: clean _install _build _build_image ## Build cli

.PHONY: _build
_build: ## Build cli wheel file
	poetry build -f wheel

.PHONY: _bump_major_version
_bump_major_version: ## Bump the major version
	poetry version major

.PHONY: _bump_minor_version
_bump_minor_version: ## Bump the minor version
	poetry version minor

.PHONY: _bump_patch_version
_bump_patch_version: ## Bump the patch version
	poetry version patch

.PHONY: _build_image
_build_image: ## Build cli image
	$(DOCKER_BUILD) -f ./Dockerfile -t ${IMAGE_NAME}:${HASH} -t ${IMAGE_NAME}:latest -t ${IMAGE_NAME}:${APP_VERSION} .

.PHONY: _dev_install
_dev_install: ## Installs the cli locally
	pip install -e ${PWD}

.PHONY: _dev_uninstall
_dev_uninstall: ## Uninstalls the cli
	pip uninstall -y mctl

.PHONY: _install
_install: ## Format code
	poetry install

.PHONY: _format
_format:  ## Format code
	poetry run black --check src/ tests/
	poetry run isort --check src/ tests/

.PHONY: _lint
_lint:  ## Lint files
	poetry run ruff --fix --show-fixes --exit-non-zero-on-fix src/ tests/
	poetry run flake8 --config=./.flake8 src/ tests/
