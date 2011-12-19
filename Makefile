PYTHON=python

#### General

all:
	$(PYTHON) setup.py build

clean:
	rm -rf venv
	find . -name \*.pyc | xargs --no-run-if-empty rm

#### Dependencies

test_deps: venv/.test_deps

venv:
	virtualenv venv
	-rm distribute-*.tar.gz || true

venv/.test_deps: venv
	./venv/bin/pip install tornado
	touch venv/.test_deps

#### Development

test_server: test_deps
	PYTHONPATH=$(PWD) ./venv/bin/python examples/test/test.py
