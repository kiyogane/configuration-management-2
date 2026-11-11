PYTHON ?= python3

.PHONY: run test demo

run:
	PYTHONPATH=src $(PYTHON) -m depviz $(ARGS)

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

demo:
	sh scripts/run_all.sh
