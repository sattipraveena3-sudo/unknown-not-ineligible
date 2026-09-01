.PHONY: install download validate build test score reproduce

install:
	python -m pip install -e '.[dev]'

download:
	python scripts/download_data.py

validate:
	python scripts/validate_data.py

build:
	python -m unknown_ineligible.build_cases --config configs/experiment.yaml
	python -m unknown_ineligible.build_cases --config configs/external_2023.yaml

test:
	python -m pytest -q

score:
	python -m unknown_ineligible.score --inputs results/raw/responses.jsonl

reproduce: validate test build
