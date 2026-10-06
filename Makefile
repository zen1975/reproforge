.PHONY: bootstrap install test lint validate statuses verify

bootstrap: install

install:
	python -m pip install -e '.[dev]'

test:
	pytest

lint:
	ruff check src tests

validate:
	reproforge validate templates/paper-manifest.example.yaml

statuses:
	reproforge validate-all-statuses

verify: lint test validate statuses
