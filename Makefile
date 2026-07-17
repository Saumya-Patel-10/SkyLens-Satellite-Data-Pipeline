# Convenience targets. Run `make help` to list them.

.PHONY: help setup pipeline app test clean

help:
	@echo "setup     - install dependencies"
	@echo "pipeline  - run ingest -> clean -> analyze"
	@echo "app       - launch the Streamlit dashboard"
	@echo "test      - run the test suite"
	@echo "clean     - delete generated data artifacts"

setup:
	pip install -r requirements.txt

pipeline:
	python -m src.pipeline

app:
	streamlit run app/dashboard.py

test:
	pytest -q

clean:
	rm -f data/raw/*.parquet data/interim/*.parquet data/processed/*
