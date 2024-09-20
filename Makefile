.PHONY: help docs
.DEFAULT_GOAL := help

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

clean: ## Removing cached python compiled files
	find . -name \*pyc  | xargs  rm -fv
	find . -name \*pyo | xargs  rm -fv
	find . -name \*~  | xargs  rm -fv
	find . -name __pycache__  | xargs  rm -rfv
	find . -name .ruff_cache  | xargs  rm -rfv

install: ## Install dependencies
	pip install -r requirements.txt
	flit install --symlink

install-full: ## Install dependencies
	make install
	pre-commit install -f

lint:fmt ## Run code linters
	ruff check zform tests
	#mypy zform

ruff-fix: ## Run Ruff fixer
	ruff check zform tests --fix --unsafe-fixes

fmt format:clean ## Run code formatters
	ruff format zform tests
	ruff check --fix zform tests

test:clean ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=zform --cov-report term-missing

pre-commit-lint: ## Runs Requires commands during pre-commit
	make clean
	make fmt
	make lint
