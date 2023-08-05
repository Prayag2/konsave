.PHONY: help all setup dev-setup fmt clean distclean maintclean pyfmt black usort tests

all: setup

help:
		@echo "konsave helper:"
		@echo ""
		@echo " - setup:        User-level setup"
		@echo " - dev-setup:    Development setup"
		@echo " - fmt:          Format the code with pyfmt"
		@echo " - clean:        Remove all pyc files"
		@echo " - distclean:    Remove any eggs/builds"
		@echo " - maintclean:   Remove virtual env and dist files"
		@echo ""

setup:
		@echo "Setting Up (user)"
		@python3 -m venv .venv
		@(. .venv/bin/activate && \
				pip install -r requirements.txt && \
				python -m pip install --upgrade pip \
		)

dev-setup: setup
		@echo "Setting Up (dev)"
		@@(. .venv/bin/activate && pip install -r requirements_dev.txt)


fmt: black pylint

black:
		@echo " * Running black"
		@black --safe konsave


# TODO: Consider adding this
# usort:
# 		@echo " * Running usort"
# 		@usort format konsave

pylint:
		@echo " * Running pylint"
		@pylint konsave

clean:
		@find . -name "*.pyc" -exec rm -f {} \;
		@find . -name '__pycache__' -type d | xargs rm -fr

distclean: clean
		rm -fr *.egg *.egg-info/ .eggs/ dist/ build/

maintclean: distclean
		rm -fr .venv/

# TODO: Consider adding proper type-checking
# typecheck:
#		 mypy -p yacgtc --strict --no-strict-optional --ignore-missing-imports --install-types
#		 mypy -p tests --no-strict-optional --ignore-missing-imports --install-types

tests:
		python3 ./test.py
