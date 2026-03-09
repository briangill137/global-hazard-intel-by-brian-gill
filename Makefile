install:
	pip install -e .[dev]

run:
	uvicorn global_hazard_intel.main:app --reload

test:
	pytest

lint:
	ruff check .
