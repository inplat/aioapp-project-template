.DEFAULT_GOAL := test
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define VERSION_PYSCRIPT
import myaioapp;print(myaioapp.__version__)
endef
export VERSION_PYSCRIPT

VENV_EXISTS=$(shell [ -e .venv ] && echo 1 || echo 0 )
VENV_PATH=.venv
VENV_BIN=$(VENV_PATH)/bin
VERSION=$(shell $(VENV_BIN)/python -c "$(VERSION_PYSCRIPT)")
BROWSER := $(VENV_BIN)/python -c "$$BROWSER_PYSCRIPT"

.PHONY: clean
clean: clean-pyc clean-build clean-test clean-venv clean-docs clean-mypy  ## Remove all build, test, coverage and Python artifacts

.PHONY: clean-build
clean-build:  ## Remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

.PHONY: clean-pyc
clean-pyc:  ## Remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: clean-test
clean-test:  ## Remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache


.PHONY: clean-docs
clean-docs:  ## Remove docs artifacts
	rm -rf docs/build
	rm -rf docs/source/myaioapp*.rst
	rm -rf docs/source/modules.rst

.PHONY: clean-mypy
clean-mypy:  ## Remove mypy cache
	rm -rf .mypy_cache

.PHONY: clean-venv
clean-venv:  ## Remove virtual environment
	-rm -rf $(VENV_PATH)

.PHONY: venv
venv:  ## Create virtual environment and install all development requirements
ifeq ($(VENV_EXISTS), 1)
	@echo virtual env already initialized
else
	virtualenv -p python3.6 .venv
	$(VENV_BIN)/pip install -r requirements_dev.txt
endif

.PHONY: flake8
flake8: venv  ## Check style with flake8
	$(VENV_BIN)/flake8 myaioapp tests

.PHONY: bandit
bandit: venv  ## Find common security issues in code
	$(VENV_BIN)/bandit -r ./myaioapp

.PHONY: mypy
mypy: venv  ## Static type check
	$(VENV_BIN)/mypy myaioapp --ignore-missing-imports

.PHONY: lint
lint: flake8 bandit mypy  ## Run flake8, bandit, mypy

.PHONY: test
test: venv  ## Run tests
	$(VENV_BIN)/pytest -v -s tests

.PHONY: coverage-quiet
coverage-quiet: venv  ## Make coverage report
		$(VENV_BIN)/coverage run --source myaioapp -m pytest tests
		$(VENV_BIN)/coverage report -m
		$(VENV_BIN)/coverage html

.PHONY: coverage
coverage: venv coverage-quiet  ## Make coverage report and open it in browser
		$(BROWSER) htmlcov/index.html

.PHONY: fast-test-prepare
fast-test-prepare: ## fast-test-prepare
	docker-compose -f tests/docker-compose.yml up -d

.PHONY: fast-test
fast-test: venv ## fast-test
	pytest -s -v --rabbit-addr=amqp://guest:guest@127.0.0.1:45672/ --postgres-addr=postgres://postgres@127.0.0.1:45432/postgres --tracer-addr=127.0.0.1:49411 --metrics-addr=udp://127.0.0.1:48094 tests

.PHONY: fast-coverage
fast-coverage: venv ## make coverage report and open it in browser
		$(VENV_BIN)/coverage run --source myaioapp -m pytest tests -v --rabbit-addr=amqp://guest:guest@127.0.0.1:45672/ --postgres-addr=postgres://postgres@127.0.0.1:45432/postgres --tracer-addr=127.0.0.1:49411 --metrics-addr=udp://127.0.0.1:48094 tests
		$(VENV_BIN)/coverage report -m
		$(VENV_BIN)/coverage html
		$(BROWSER) htmlcov/index.html

.PHONY: fast-test-stop
fast-test-stop: ## fast-test-stop
	docker-compose -f tests/docker-compose.yml kill
	docker-compose -f tests/docker-compose.yml rm -f

.PHONY: fast-test-build
fast-test-build: ## fast-test-build
	docker-compose -f tests/docker-compose.yml build

.PHONY: fast-test-update
fast-test-update: ## fast-test-update
	docker-compose -f tests/docker-compose.yml pull
	docker-compose -f tests/docker-compose.yml kill
	docker-compose -f tests/docker-compose.yml rm -f

.PHONY: fast-test-rebuild
fast-test-rebuild: fast-test-update fast-test-build fast-test-prepare ## fast-test-rebuild

.PHONY: docs
docs-quiet: venv  ## Make documentation
	rm -f docs/source/myaioapp.rst
	rm -f docs/source/modules.rst
	.venv/bin/sphinx-apidoc -o docs/source/ myaioapp
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

.PHONY: docs
docs: venv docs-quiet  ## Make documentation and open it in browser
	$(BROWSER) docs/build/html/index.html

.PHONY: help
help:  ## Show this help message and exit
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-23s\033[0m %s\n", $$1, $$2}'

