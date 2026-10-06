.PHONY: bootstrap install test lint validate candidates statuses verify

bootstrap: install

install:
	python -m pip install -e '.[dev]'

test:
	pytest

lint:
	ruff check src tests

validate:
	reproforge validate templates/paper-manifest.example.yaml

candidates:
	reproforge validate-candidates candidates/queue.yaml

statuses:
	reproforge validate-all-statuses

verify: lint test validate candidates statuses
