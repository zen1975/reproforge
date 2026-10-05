.PHONY: install test lint validate

install:
	python -m pip install -e '.[dev]'

test:
	pytest

lint:
	ruff check src tests

validate:
	reproforge validate templates/paper-manifest.example.yaml
